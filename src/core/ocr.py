# src/core/ocr.py
import logging
import os
from typing import List, Optional, Tuple

import easyocr
import regex
from google.cloud import vision

from src.config import OCREngine  # --- THE FIX IS HERE ---

# --- Setup ---
logger = logging.getLogger("GeoPhotoToolkitLogger")

# Initialize EasyOCR reader once to load the model into memory.
try:
    easyocr_reader = easyocr.Reader(["en", "id"], gpu=False)
    logger.info("EasyOCR reader initialized successfully.")
except Exception as e:
    logger.warning(f"Could not initialize EasyOCR: {e}. It will not be available.")
    easyocr_reader = None

# Google Vision client is initialized on-demand to handle dynamic key paths.
gcv_client = None


# --- Shared Parsing Logic ---
def _parse_gps_from_text(text: str) -> Optional[Tuple[float, float]]:
    """
    Parses a single block of text to find and extract GPS coordinates.
    Supports DMS, DDM, and DD formats.
    """
    cleaned_text = text.replace(",", ".").replace("\n", " ")
    cleaned_text = regex.sub(r"(\D)(\d{2})(\d{1})(\.)", r"\1\2 \3\4", cleaned_text)
    dms_pattern = regex.compile(
        r"(?P<lat_deg>\d{1,3})\D+?(?P<lat_min>\d{1,2})\D+?(?P<lat_sec>[\d.]+)\D*?(?P<lat_hem>[NS])\D+?(?P<lon_deg>\d{1,3})\D+?(?P<lon_min>\d{1,2})\D+?(?P<lon_sec>[\d.]+)\D*?(?P<lon_hem>[EW])",
        regex.VERBOSE | regex.IGNORECASE,
    )
    ddm_pattern = regex.compile(
        r"(?P<lat_deg>\d{1,3})\D+?(?P<lat_dm>[\d.]+)\D*?(?P<lat_hem>[NS])\D+?(?P<lon_deg>\d{1,3})\D+?(?P<lon_dm>[\d.]+)\D*?(?P<lon_hem>[EW])",
        regex.VERBOSE | regex.IGNORECASE,
    )
    dd_pattern = regex.compile(r"(-?\d{1,3}\.\d{4,})\s*,\s*(-?\d{1,3}\.\d{4,})")

    match = dms_pattern.search(cleaned_text)
    if match:
        try:
            lat_val = _convert_dms_to_dd(
                match.group("lat_deg"),
                match.group("lat_min"),
                match.group("lat_sec"),
                match.group("lat_hem").upper(),
            )
            lon_val = _convert_dms_to_dd(
                match.group("lon_deg"),
                match.group("lon_min"),
                match.group("lon_sec"),
                match.group("lon_hem").upper(),
            )
            if -90 <= lat_val <= 90 and -180 <= lon_val <= 180:
                return lat_val, lon_val
        except (ValueError, TypeError):
            pass

    match = ddm_pattern.search(cleaned_text)
    if match:
        try:
            lat_val = _convert_ddm_to_dd(
                match.group("lat_deg"),
                match.group("lat_dm"),
                match.group("lat_hem").upper(),
            )
            lon_val = _convert_ddm_to_dd(
                match.group("lon_deg"),
                match.group("lon_dm"),
                match.group("lon_hem").upper(),
            )
            if -90 <= lat_val <= 90 and -180 <= lon_val <= 180:
                return lat_val, lon_val
        except (ValueError, TypeError):
            pass

    match = dd_pattern.search(cleaned_text)
    if match:
        try:
            lat = float(match.group(1))
            lon = float(match.group(2))
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon
        except (ValueError, TypeError):
            pass
    return None


def _convert_dms_to_dd(d, m, s, h):
    return (float(d) + float(m) / 60 + float(s) / 3600) * (-1 if h in ["S", "W"] else 1)


def _convert_ddm_to_dd(d, dm, h):
    return (float(d) + float(dm) / 60) * (-1 if h in ["S", "W"] else 1)


# --- Engine-Specific Private Functions ---


def _extract_text_with_easyocr(image_path: str) -> Optional[List[str]]:
    """Uses EasyOCR to get a list of text blocks from an image."""
    if not easyocr_reader:
        return None
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        return easyocr_reader.readtext(image_bytes, detail=0, paragraph=False)
    except Exception as e:
        logger.error(f"EasyOCR processing failed for {image_path}: {e}")
        return None


def _extract_text_with_google_vision(
    image_path: str, key_path: Optional[str]
) -> Optional[str]:
    """Uses Google Cloud Vision to get a single block of text from an image."""
    global gcv_client
    try:
        if gcv_client is None:
            if not key_path or not os.path.exists(key_path):
                logger.error(
                    "Google Vision API key path is not configured or file not found."
                )
                return None
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
            gcv_client = vision.ImageAnnotatorClient()
            logger.info("Google Vision client initialized successfully.")

        with open(image_path, "rb") as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        response = gcv_client.text_detection(image=image)
        if response.error.message:
            raise Exception(response.error.message)
        return response.full_text_annotation.text
    except Exception as e:
        logger.error(f"Google Vision API failed for {image_path}: {e}")
        return None


# --- Public API for the Workflow ---


def extract_gps_with_ocr(
    image_path: str, engine: OCREngine, gcv_key_path: Optional[str]
) -> Optional[Tuple[float, float, str]]:
    """
    Main dispatcher function. Extracts GPS using the specified OCR engine.
    """
    raw_text_blocks: List[str] = []
    source_engine = ""

    if engine == OCREngine.EASYOCR:
        source_engine = "EasyOCR"
        blocks = _extract_text_with_easyocr(image_path)
        if blocks:
            raw_text_blocks = blocks
    elif engine == OCREngine.GOOGLE:
        source_engine = "Google Vision"
        full_text = _extract_text_with_google_vision(image_path, gcv_key_path)
        if full_text:
            raw_text_blocks = [full_text]

    if not raw_text_blocks:
        logger.warning(f"{source_engine} could not find any text in {image_path}")
        return None

    logger.debug(f"{source_engine} found text blocks: {raw_text_blocks}")

    for text_block in raw_text_blocks:
        coords = _parse_gps_from_text(text_block)
        if coords:
            return coords[0], coords[1], text_block

    logger.warning(
        f"Could not find a valid GPS coordinate in any text from {source_engine} for {image_path}"
    )
    return None
