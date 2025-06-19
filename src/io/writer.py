# src/io/writer.py
import logging
import os

import pandas as pd

logger = logging.getLogger("GeoPhotoToolkitLogger")


def write_dataframe_to_excel(
    df: pd.DataFrame, output_folder: str, filename: str
) -> None:
    """
    Saves a pandas DataFrame to an Excel file.

    Args:
        df (pd.DataFrame): The DataFrame to save, with columns already in order.
        output_folder (str): The directory to save the Excel file in.
        filename (str): The name of the output Excel file.
    """
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, filename)

    try:
        df.to_excel(output_path, index=False, header=True)
        logger.info(f"Successfully saved data to Excel file: {output_path}")
    except Exception as e:
        logger.error(f"Could not write to Excel file {output_path}: {e}")
        raise


def write_dataframe_to_csv(df: pd.DataFrame, output_folder: str, filename: str) -> None:
    """
    Saves a pandas DataFrame to a CSV file.

    Args:
        df (pd.DataFrame): The DataFrame to save, with columns already in order.
        output_folder (str): The directory to save the CSV file in.
        filename (str): The name of the output CSV file.
    """
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, filename)

    try:
        df.to_csv(output_path, index=False, header=True)
        logger.info(f"Successfully saved data to CSV file: {output_path}")
    except Exception as e:
        logger.error(f"Could not write to CSV file {output_path}: {e}")
        raise
