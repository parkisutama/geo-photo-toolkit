# src/core/exif.py
import os
from typing import Any, Dict, Optional

from PIL import ExifTags, Image


# --- Helper Functions ---
def _convert_to_degrees(value: tuple[float, float, float]) -> float:
    """Converts GPS coordinate from DMS to Decimal Degrees."""
    d, m, s = value
    return d + (m / 60.0) + (s / 3600.0)


def _get_exif_dict(exif_data) -> Dict[str, Any]:
    """Converts raw EXIF data into a human-readable dictionary."""
    if not exif_data:
        return {}
    return {
        ExifTags.TAGS.get(tag_id, tag_id): value for tag_id, value in exif_data.items()
    }


# --- Main Public Functions ---
def extract_exif_data(
    image_path: str, tags_to_extract: Dict[str, str]
) -> Optional[Dict[str, Any]]:
    """
    Extracts a specified set of EXIF tags from an image file.
    This version is backward-compatible with older Pillow library versions.

    Args:
        image_path (str): The path to the image file.
        tags_to_extract (Dict[str, str]): A dictionary mapping desired column names
                                          to official EXIF tag names.

    Returns:
        A dictionary containing the extracted data for the requested tags, or None if
        the image can't be processed.
    """
    try:
        img = Image.open(image_path)
        exif = img.getexif()
        if not exif:
            return None

        # --- Handle GPS Data Separately for proper parsing ---
        try:
            # For modern Pillow versions with the IFD enum
            gps_ifd_tag = ExifTags.IFD.GPS
        except AttributeError:
            # Fallback for older Pillow versions using the raw integer tag
            gps_ifd_tag = 34853

        gps_ifd = exif.get_ifd(gps_ifd_tag)
        gps_tags = _get_exif_dict(gps_ifd)

        # Calculate latitude and longitude if present and add them back to the dict
        lat_dms = gps_tags.get("GPSLatitude")
        lon_dms = gps_tags.get("GPSLongitude")
        lat_ref = gps_tags.get("GPSLatitudeRef")
        lon_ref = gps_tags.get("GPSLongitudeRef")

        if all([lat_dms, lon_dms, lat_ref, lon_ref]):
            lat = _convert_to_degrees(lat_dms)
            lon = _convert_to_degrees(lon_dms)
            if lat_ref == "S":
                lat = -lat
            if lon_ref == "W":
                lon = -lon
            # Overwrite the raw tuples with calculated decimal degrees
            gps_tags["GPSLatitude"] = lat
            gps_tags["GPSLongitude"] = lon

        # Combine main and GPS tags, with GPS tags taking precedence
        main_tags = _get_exif_dict(exif)
        all_tags = {**main_tags, **gps_tags}

        # --- Extract only the user-requested tags ---
        extracted_data = {}
        for column_name, exif_tag_name in tags_to_extract.items():
            extracted_data[column_name] = all_tags.get(exif_tag_name)

        return extracted_data

    except Exception as e:
        # Using print here for direct feedback on file-specific errors during a run
        print(
            f"Warning: Could not process EXIF for {os.path.basename(image_path)}: {e}"
        )
        return None
