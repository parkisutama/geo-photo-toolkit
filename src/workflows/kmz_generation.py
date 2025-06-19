# src/workflows/kmz_generation.py
import logging
import os
from datetime import datetime

import pandas as pd

from src.core.kml import create_kml_file, create_kmz_archive
from src.io.downloader import download_file, is_url
from src.utils.config_loader import load_config

logger = logging.getLogger("GeoPhotoToolkitLogger")


def _process_media_links(df: pd.DataFrame, base_media_folder: str) -> pd.DataFrame:
    # ... (This function does not need to change)
    df_processed = df.copy()
    photo_folder = os.path.join(base_media_folder, "photo_files")
    icon_folder = os.path.join(base_media_folder, "icon_files")
    if "photo_path" in df_processed.columns:
        df_processed["local_photo_path"] = df_processed["photo_path"].apply(
            lambda path: download_file(path, photo_folder)
            if pd.notna(path) and is_url(path)
            else path
        )
    if "icon_url" in df_processed.columns:
        df_processed["local_icon_path"] = df_processed["icon_url"].apply(
            lambda url: download_file(url, icon_folder)
            if pd.notna(url) and is_url(url)
            else url
        )
    return df_processed


def run_kmz_generation_workflow(
    input_file: str, output_dir: str, config_path: str | None
) -> None:
    """
    Main workflow to generate a KMZ file from an input data file (CSV or Excel).
    """
    logger.info(f"Starting KMZ generation workflow for file: {input_file}")
    os.makedirs(output_dir, exist_ok=True)

    # 1. Load configuration for description template
    try:
        config = load_config(config_path)
        description_template = (
            config.get("kmz", {}).get("description", {}).get("template")
        )
        if description_template:
            logger.info("Found KMZ description template in config file.")
    except Exception as e:
        logger.error(
            f"Could not load or parse config, will use default description: {e}"
        )
        description_template = None

    # 2. Read and prepare data
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return
    try:
        filename, extension = os.path.splitext(input_file)
        extension = extension.lower()
        if extension == ".csv":
            df = pd.read_csv(input_file)
        elif extension == ".xlsx":
            df = pd.read_excel(input_file)
        else:
            logger.error(
                f"Unsupported file format: '{extension}'. Please use '.csv' or '.xlsx'."
            )
            return

        # To handle potential NaN values from empty cells that break the formatter
        df.fillna("", inplace=True)
        # We need a 'longitude' and 'latitude' column from the extraction step
        # Let's assume the config maps them as 'lon' and 'lat'
        df.rename(columns={"lon": "longitude", "lat": "latitude"}, inplace=True)

        if not all(col in df.columns for col in ["latitude", "longitude"]):
            logger.error(
                "Input file must contain 'latitude' and 'longitude' columns (or 'lat'/'lon')."
            )
            return
    except Exception as e:
        logger.error(f"Failed to read or validate input file: {e}")
        return

    # 3. Process media files
    df_with_local_paths = _process_media_links(df, output_dir)

    # 4. Create the KML file
    folder_name = os.path.basename(filename)
    temp_kml_path = os.path.join(output_dir, "doc.kml")
    create_kml_file(
        df_with_local_paths, folder_name, temp_kml_path, description_template
    )

    # 5. Create the final KMZ archive
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_kmz_filename = f"{folder_name}_{timestamp}.kmz"
    output_kmz_path = os.path.join(output_dir, output_kmz_filename)
    create_kmz_archive(temp_kml_path, df_with_local_paths, output_kmz_path)

    logger.info("KMZ generation workflow completed successfully.")
