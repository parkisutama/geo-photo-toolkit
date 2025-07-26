# src/workflows/gps_extraction.py
import logging
import os
from typing import Any, Dict, List

import pandas as pd

from src.config import OCREngine
from src.core.exif import extract_exif_data
from src.core.ocr import extract_gps_with_ocr
from src.io.writer import write_dataframe_to_csv, write_dataframe_to_excel
from src.utils.config_loader import load_config

logger = logging.getLogger("GeoPhotoToolkitLogger")


def run_gps_extraction_workflow(
    input_dir,
    output_file,
    include_full_path=True,
    config_path=None,
    ocr_disabled=False,
    ocr_engine=None,
    gcv_fallback=False,
    gcv_limit=-1,
    no_ocr_on_invalid_gps=False,
    preprocess_method="auto",
    save_preprocessed=False,
):
    """
    Main workflow to extract GPS data, with tiered OCR and configurable logic.
    """
    logger.info("--- Starting GPS Extraction Workflow ---")
    debug_folder = None
    if save_preprocessed:
        debug_folder = os.path.join(input_dir, "_preprocessed_debug")
    # Example loop for preprocessing each image before OCR
    # for image_path in image_list:
    #     preprocessed_path = preprocess_image(image_path, method=preprocess_method, debug_folder=debug_folder)
    #     # Use preprocessed_path for OCR
    if ocr_disabled:
        logger.info("Mode: EXIF-only. OCR fallback is completely disabled.")
    else:
        logger.info(f"Primary OCR Engine: {ocr_engine.value}")
        if ocr_engine == OCREngine.EASYOCR and gcv_fallback:
            limit_msg = (
                f"up to {gcv_limit} images" if gcv_limit != -1 else "all failed images"
            )
            logger.info(f"Google Vision fallback is ENABLED for {limit_msg}.")
        if no_ocr_on_invalid_gps:
            logger.info(
                "Strict Mode: OCR will be disabled for images with invalid EXIF GPS."
            )

    # 1. Load configuration
    try:
        config = load_config(config_path)
        tags_to_extract = config.get("extract", {}).get("columns", {})
        gcv_key_path = config.get("google_cloud", {}).get("service_account_key_path")
    except Exception as e:
        logger.error(f"Failed to load or parse configuration: {e}")
        return

    # 2. Process images
    gcv_processed_count = 0
    all_image_data: List[Dict[str, Any]] = []
    image_files = [
        f
        for f in os.listdir(input_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]

    for filename in image_files:
        full_path = os.path.join(input_dir, filename)
        image_data = extract_exif_data(full_path, tags_to_extract)

        if not image_data:
            image_data = {}

        gps_tags_present = (
            image_data.get("lat") is not None or image_data.get("lon") is not None
        )
        has_valid_gps = gps_tags_present and not (
            image_data.get("lat") == 0.0 and image_data.get("lon") == 0.0
        )

        # --- REFACTORED LOGIC WITH MASTER SWITCH ---
        if not has_valid_gps and not ocr_disabled:
            if no_ocr_on_invalid_gps and gps_tags_present:
                logger.warning(
                    f"Found invalid/corrupt EXIF GPS for {filename}. "
                    "Skipping OCR fallback as per user setting."
                )
            else:
                # This entire block is now conditional on ocr_disabled being False
                ocr_result = None
                source_engine = ""

                logger.info(
                    f"No valid EXIF GPS for {filename}. Attempting OCR with {ocr_engine.value}."
                )

                use_gcv_primary = ocr_engine == OCREngine.GOOGLE
                if use_gcv_primary:
                    if gcv_limit == -1 or gcv_processed_count < gcv_limit:
                        ocr_result = extract_gps_with_ocr(
                            full_path,
                            OCREngine.GOOGLE,
                            gcv_key_path,
                            preprocess_method=preprocess_method,
                            debug_folder=debug_folder,
                        )
                        gcv_processed_count += 1
                        source_engine = "Google Vision"
                    else:
                        logger.warning(
                            f"Google Vision limit reached. Skipping OCR for {filename}."
                        )
                else:
                    ocr_result = extract_gps_with_ocr(
                        full_path,
                        OCREngine.EASYOCR,
                        None,
                        preprocess_method=preprocess_method,
                        debug_folder=debug_folder,
                    )
                    source_engine = "EasyOCR"

                # Google Vision fallback if EasyOCR fails and fallback is enabled
                if (
                    ocr_result is None
                    and ocr_engine == OCREngine.EASYOCR
                    and gcv_fallback
                ):
                    if gcv_limit == -1 or gcv_processed_count < gcv_limit:
                        logger.info(
                            f"EasyOCR failed for {filename}. Trying Google Vision fallback..."
                        )
                        ocr_result = extract_gps_with_ocr(
                            full_path,
                            OCREngine.GOOGLE,
                            gcv_key_path,
                            preprocess_method=preprocess_method,
                            debug_folder=debug_folder,
                        )
                        gcv_processed_count += 1
                        source_engine = "Google Vision (Fallback)"
                    else:
                        logger.warning(
                            f"Google Vision limit reached. Skipping fallback for {filename}."
                        )

                if ocr_result:
                    lat, lon, raw_text = ocr_result
                    image_data["lat"], image_data["lon"] = lat, lon
                    logger.info(
                        f"Successfully extracted GPS via {source_engine} for {filename}. "
                        f"Raw: '{raw_text}' -> Converted: ({lat:.6f}, {lon:.6f})"
                    )
                else:
                    logger.warning(f"All OCR attempts failed for {filename}.")
        # --- END OF REFACTORED LOGIC ---

        # Finalize Row Data
        image_data["name"] = filename
        if image_data.get("lat") is not None and image_data.get("lon") is not None:
            lat, lon = image_data["lat"], image_data["lon"]
            image_data["maps_url"] = (
                f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
            )
        if include_full_path:
            image_data["photo_path"] = os.path.abspath(full_path)
        all_image_data.append(image_data)

    # 3. Create DataFrame and save
    if not all_image_data:
        logger.warning("No images processed. No output file will be created.")
        return

    df = pd.DataFrame(all_image_data)
    final_columns = list(tags_to_extract.keys())
    if "name" not in final_columns:
        final_columns.insert(0, "name")
    if "maps_url" not in final_columns:
        final_columns.append("maps_url")
    if include_full_path:
        final_columns.append("photo_path")
    df = df.reindex(columns=final_columns)

    output_folder, output_filename = os.path.split(output_file)
    file_extension = os.path.splitext(output_filename)[1].lower()

    if file_extension == ".csv":
        write_dataframe_to_csv(df, output_folder or ".", output_filename)
    elif file_extension == ".xlsx":
        write_dataframe_to_excel(df, output_folder or ".", output_filename)
    else:
        logger.error(
            f"Unsupported output file format: '{file_extension}'. Please use '.csv' or '.xlsx'."
        )
        raise ValueError("Unsupported file format")

    logger.info("--- GPS Extraction Workflow Completed ---")
