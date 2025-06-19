# src/utils/logging.py
import logging
import os
import sys

from src.config import settings


def setup_logger(log_folder: str) -> logging.Logger:
    """
    Sets up a dedicated logger for the application.

    Args:
        log_folder (str): The directory where the log file will be stored.

    Returns:
        logging.Logger: A configured logger instance.
    """
    os.makedirs(log_folder, exist_ok=True)
    log_file_path = os.path.join(log_folder, settings.LOG_FILE_NAME)

    # Create a specific logger to avoid interfering with the root logger
    logger = logging.getLogger("GeoPhotoToolkitLogger")
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Prevent logs from being passed to the root logger

    # Avoid adding duplicate handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # File handler
    file_handler = logging.FileHandler(log_file_path, mode="w", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info(f"Logger initialized. Log file: {log_file_path}")
    return logger
