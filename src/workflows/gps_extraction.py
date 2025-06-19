# src/workflows/gps_extraction.py
import logging
import os
from typing import Any, Dict, List

import pandas as pd

from src.core.exif import extract_exif_data
from src.io.writer import write_dataframe_to_csv, write_dataframe_to_excel
from src.utils.config_loader import load_config

logger = logging.getLogger("GeoPhotoToolkitLogger")


def run_gps_extraction_workflow(
    input_dir: str, output_file: str, include_full_path: bool, config_path: str | None
) -> None:
    """
    Main workflow to scan a folder and extract EXIF data based on a config file.
    """
    logger.info(f"Starting config-driven GPS extraction for directory: {input_dir}")

    # 1. Load configuration
    try:
        config = load_config(config_path)
        tags_to_extract = config.get("extract", {}).get("columns", {})
        if not tags_to_extract:
            logger.error(
                "Configuration error: No columns defined in [extract.columns] section."
            )
            return
    except FileNotFoundError as e:
        logger.error(e)
        return
    except Exception as e:
        logger.error(f"Failed to load or parse configuration: {e}")
        return

    # 2. Process images
    all_image_data: List[Dict[str, Any]] = []
    for filename in os.listdir(input_dir):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            full_path = os.path.join(input_dir, filename)
            image_data = extract_exif_data(full_path, tags_to_extract)

            if image_data:
                # Add special calculated fields
                image_data["name"] = filename
                if (
                    "lat" in image_data
                    and "lon" in image_data
                    and image_data["lat"] is not None
                    and image_data["lon"] is not None
                ):
                    lat, lon = image_data["lat"], image_data["lon"]
                    image_data["maps_url"] = (
                        f"http://maps.google.com/maps?q={lat},{lon}"
                    )

                if include_full_path:
                    image_data["photo_path"] = os.path.abspath(full_path)

                all_image_data.append(image_data)

    if not all_image_data:
        logger.warning("No images could be processed. No output file will be created.")
        return

    # 3. Create DataFrame and save to file
    df = pd.DataFrame(all_image_data)

    final_columns = list(tags_to_extract.keys())
    # Add special columns that might not be in the config
    if "name" not in final_columns:
        final_columns.insert(0, "name")
    if "maps_url" not in final_columns:
        final_columns.append("maps_url")
    if include_full_path:
        final_columns.append("photo_path")

    for col in final_columns:
        if col not in df.columns:
            df[col] = None

    final_df = df[final_columns]

    output_folder, output_filename = os.path.split(output_file)
    file_extension = os.path.splitext(output_filename)[1].lower()

    if file_extension == ".csv":
        write_dataframe_to_csv(final_df, output_folder or ".", output_filename)
    elif file_extension == ".xlsx":
        write_dataframe_to_excel(final_df, output_folder or ".", output_filename)
    else:
        # --- THE FIX IS HERE ---
        logger.error(
            f"Unsupported output file format: '{file_extension}'. Please use '.csv' or '.xlsx'."
        )
        raise ValueError("Unsupported file format")

    logger.info("GPS extraction workflow completed successfully.")
