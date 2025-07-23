# src/config.py
from enum import Enum

from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """
    Defines fixed, internal application constants.
    User-facing settings are now handled by .toml configuration files.
    """

    # --- Internal Folder Names ---
    PHOTO_FOLDER_NAME: str = "photo_files"
    ICON_FOLDER_NAME: str = "icon_files"

    # --- Application Behavior Constants ---
    IMAGE_EXTENSIONS: tuple[str, ...] = (".png", ".jpg", ".jpeg")
    LOG_FILE_NAME: str = "status.log"
    REQUESTS_USER_AGENT: str = "Geo-Photo-Toolkit/1.0"


# Instantiate the config for easy import across the app
settings = AppConfig()


class OCREngine(str, Enum):
    """Enumeration for the available OCR engines."""

    EASYOCR = "easyocr"
    GOOGLE = "google"


# A list of the available choices for help text in the CLI.
OCR_ENGINE_CHOICES = [e.value for e in OCREngine]
