# src/core/exif.py
import logging
import os
from typing import Any, Dict, Optional

from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS

logger = logging.getLogger("GeoPhotoToolkitLogger")

# --- Helper Functions ---


def _get_exif_data(image_path: str) -> Optional[Image.Exif]:
    """Opens an image and extracts its raw EXIF data object."""
    try:
        with Image.open(image_path) as img:
            exif_data = img.getexif()
            if not exif_data:
                logger.warning(f"No EXIF data found in {image_path}")
                return None
            return exif_data
    except Exception as e:
        logger.error(f"Could not open or read image file at {image_path}: {e}")
        return None


def _decode_ifd(ifd, tag_map: Dict[int, str]) -> Dict[str, Any]:
    """Decodes an IFD from numeric tags to human-readable names."""
    decoded_data = {}
    for key, val in ifd.items():
        tag_name = tag_map.get(key, key)
        # Clean up byte strings for cleaner output
        if isinstance(val, bytes):
            try:
                decoded_data[tag_name] = val.decode("utf-8", errors="ignore").strip(
                    "\x00"
                )
            except Exception:
                decoded_data[tag_name] = repr(val)
        else:
            decoded_data[tag_name] = val
    return decoded_data


def _convert_dms_to_dd(degrees, minutes, seconds, direction):
    """Converts a GPS coordinate from DMS to DD format."""
    dd = float(degrees) + float(minutes) / 60 + float(seconds) / 3600
    if direction in ["S", "W"]:
        dd *= -1
    return dd


# --- Main Extraction Logic ---


def extract_exif_data(
    image_path: str, tags_to_extract: Dict[str, str]
) -> Optional[Dict[str, Any]]:
    """
    Extracts specific, user-defined EXIF tags from an image file,
    searching across all relevant IFDs (Image File Directories).
    """
    raw_exif = _get_exif_data(image_path)
    if not raw_exif:
        return None

    # --- THE CORE FIX IS HERE ---
    # 1. Decode the main IFD (top-level tags)
    all_decoded_data = _decode_ifd(raw_exif, TAGS)

    # 2. Decode the nested Exif IFD (detailed photo settings)
    #    The numeric ID 34665 is the standard pointer to the Exif sub-directory.
    exif_ifd = raw_exif.get_ifd(34665)
    all_decoded_data.update(_decode_ifd(exif_ifd, TAGS))

    # 3. Decode the nested GPS IFD (location data)
    gps_ifd = raw_exif.get_ifd(34853)
    gps_decoded = _decode_ifd(gps_ifd, GPSTAGS)

    # 4. Process GPS data if it exists and is valid
    lat_dms = gps_decoded.get("GPSLatitude")
    lon_dms = gps_decoded.get("GPSLongitude")
    if lat_dms and lon_dms:
        # Check for the corrupt 'Rational with denominator 0' case
        try:
            if lat_dms[0].denominator != 0 and lon_dms[0].denominator != 0:
                lat = _convert_dms_to_dd(
                    lat_dms[0],
                    lat_dms[1],
                    lat_dms[2],
                    gps_decoded.get("GPSLatitudeRef"),
                )
                lon = _convert_dms_to_dd(
                    lon_dms[0],
                    lon_dms[1],
                    lon_dms[2],
                    gps_decoded.get("GPSLongitudeRef"),
                )
                # Add the converted values to our main data dictionary
                all_decoded_data["GPSLatitude"] = lat
                all_decoded_data["GPSLongitude"] = lon
        except (AttributeError, ZeroDivisionError, TypeError, ValueError):
            logger.debug(f"Found corrupt GPS tags in {os.path.basename(image_path)}")

    # Also add non-coordinate GPS data like altitude
    if "GPSAltitude" in gps_decoded:
        all_decoded_data["GPSAltitude"] = gps_decoded.get("GPSAltitude")
    # --- END OF CORE FIX ---

    # Now, build the final result based on the user's config
    final_data = {}
    for friendly_name, exif_tag_name in tags_to_extract.items():
        value = all_decoded_data.get(exif_tag_name)
        if value is not None:
            final_data[friendly_name] = value
        else:
            final_data[friendly_name] = None  # Explicitly set to None if not found
            logger.debug(
                f"Tag '{exif_tag_name}' not found in any IFD for {os.path.basename(image_path)}"
            )

    return final_data
