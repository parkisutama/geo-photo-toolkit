# src/core/ocr.py
import logging
import os
from typing import List, Optional, Tuple

import easyocr
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
    import re

    # Normalize and clean text
    cleaned = (
        text.replace("\n", " ")
        .replace("*", "°")
        .replace("/", "'")
        .replace(",", ".")
        .replace("  ", " ")
    )
    cleaned = re.sub(r'[^\dNSEW°\'".\- ]+', " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)

    # Stricter regex for DMS/DM/Decimal formats (avoid matching huge numbers)
    coord_regex = re.compile(
        r'(\d{1,2})[°\s]?(\d{1,2})[\s\'"]?(\d{1,2}(?:\.\d+)?)?["\s]?([NS])'
        r'.*?(\d{1,3})[°\s]?(\d{1,2})[\s\'"]?(\d{1,2}(?:\.\d+)?)?["\s]?([EW])',
        re.IGNORECASE,
    )

    # Stricter regex for DDM format
    ddm_regex = re.compile(
        r'(\d{1,2})[°\s]?([\d.]+)[\s\'"]?([NS])'
        r'.*?(\d{1,3})[°\s]?([\d.]+)[\s\'"]?([EW])',
        re.IGNORECASE,
    )

    # Try DMS first
    match = coord_regex.search(cleaned)
    if match:
        try:
            lat_deg = float(match.group(1))
            lat_min = float(match.group(2) or 0)
            lat_sec = float(match.group(3) or 0)
            lat_hem = match.group(4).upper()
            lon_deg = float(match.group(5))
            lon_min = float(match.group(6) or 0)
            lon_sec = float(match.group(7) or 0)
            lon_hem = match.group(8).upper()
            # Convert to decimal degrees
            lat_dd = lat_deg + lat_min / 60 + lat_sec / 3600
            lon_dd = lon_deg + lon_min / 60 + lon_sec / 3600
            if lat_hem == "S":
                lat_dd = -lat_dd
            if lon_hem == "W":
                lon_dd = -lon_dd
            # Validate ranges
            if not (-90 <= lat_dd <= 90 and -180 <= lon_dd <= 180):
                logger.warning(
                    f"GPS Parsing DMS out of range: lat={lat_dd}, lon={lon_dd} | Raw text: '{text}'"
                )
                return None
            logger.info(
                f"GPS Parsing: Raw text: '{text}' | Format: DMS | Parsed: lat={lat_dd}, lon={lon_dd} | Converted DD: ({lat_dd}, {lon_dd})"
            )
            return (lat_dd, lon_dd)
        except Exception as e:
            logger.warning(f"GPS Parsing DMS failed: {e} | Raw text: '{text}'")
            return None

    # Try DDM format
    match = ddm_regex.search(cleaned)
    if match:
        try:
            lat_deg = float(match.group(1))
            lat_min = float(match.group(2) or 0)
            lat_hem = match.group(3).upper()
            lon_deg = float(match.group(4))
            lon_min = float(match.group(5) or 0)
            lon_hem = match.group(6).upper()
            # Convert to decimal degrees
            lat_dd = lat_deg + lat_min / 60
            lon_dd = lon_deg + lon_min / 60
            if lat_hem == "S":
                lat_dd = -lat_dd
            if lon_hem == "W":
                lon_dd = -lon_dd
            # Validate ranges
            if not (-90 <= lat_dd <= 90 and -180 <= lon_dd <= 180):
                logger.warning(
                    f"GPS Parsing DDM out of range: lat={lat_dd}, lon={lon_dd} | Raw text: '{text}'"
                )
                return None
            logger.info(
                f"GPS Parsing: Raw text: '{text}' | Format: DDM | Parsed: lat={lat_dd}, lon={lon_dd} | Converted DD: ({lat_dd}, {lon_dd})"
            )
            return (lat_dd, lon_dd)
        except Exception as e:
            logger.warning(f"GPS Parsing DDM failed: {e} | Raw text: '{text}'")
            return None

    # Fallback: try to find decimal degrees (DD) format
    dd_pattern = re.compile(
        r"(-?\d{1,2}\.\d{4,})\s*[NS]?[, ]\s*(-?\d{1,3}\.\d{4,})\s*[EW]?"
    )
    match = dd_pattern.search(cleaned)
    if match:
        try:
            lat = float(match.group(1))
            lon = float(match.group(2))
            # Validate ranges
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                logger.warning(
                    f"GPS Parsing DD out of range: lat={lat}, lon={lon} | Raw text: '{text}'"
                )
                return None
            logger.info(
                f"GPS Parsing: Raw text: '{text}' | Format: DD | Parsed: lat={lat}, lon={lon} | Converted DD: ({lat}, {lon})"
            )
            return (lat, lon)
        except Exception as e:
            logger.warning(f"GPS Parsing DD failed: {e} | Raw text: '{text}'")
            return None
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
    image_path: str,
    engine: OCREngine,
    gcv_key_path: Optional[str],
    preprocess_method: str = "auto",
    debug_folder: str = None,
) -> Optional[Tuple[float, float, str]]:
    """
    Main dispatcher function. Extracts GPS using the specified OCR engine.
    """
    from src.core.preprocess import preprocess_image

    # Preprocess image before OCR
    preprocessed_path = preprocess_image(
        image_path, method=preprocess_method, debug_folder=debug_folder
    )
    ocr_input_path = preprocessed_path if preprocessed_path else image_path

    raw_text_blocks: List[str] = []
    source_engine = ""

    if engine == OCREngine.EASYOCR:
        source_engine = "EasyOCR"
        blocks = _extract_text_with_easyocr(ocr_input_path)
        if blocks:
            raw_text_blocks = blocks
    elif engine == OCREngine.GOOGLE:
        source_engine = "Google Vision"
        full_text = _extract_text_with_google_vision(ocr_input_path, gcv_key_path)
        if full_text:
            raw_text_blocks = [full_text]

    if not raw_text_blocks:
        logger.warning(f"{source_engine} could not find any text in {ocr_input_path}")
        return None

    # Log the OCR output for debugging and traceability
    logger.info(f"{source_engine} OCR output for {ocr_input_path}: {raw_text_blocks}")
    logger.debug(f"{source_engine} found text blocks: {raw_text_blocks}")

    for text_block in raw_text_blocks:
        coords = _parse_gps_from_text(text_block)
        if coords:
            return coords[0], coords[1], text_block

    logger.warning(
        f"Could not find a valid GPS coordinate in any text from {source_engine} for {ocr_input_path}"
    )
    return None
