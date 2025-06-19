# src/io/downloader.py
import logging
import os
from typing import Optional

import requests

from src.config import settings

logger = logging.getLogger("GeoPhotoToolkitLogger")


def is_url(path: str) -> bool:
    """Checks if a given path string is a URL."""
    return path.startswith(("http://", "https://"))


def download_file(url: str, download_folder: str) -> Optional[str]:
    """
    Downloads a file from a URL into a specified folder.

    Args:
        url (str): The URL of the file to download.
        download_folder (str): The local directory to save the file in.

    Returns:
        Optional[str]: The local path to the downloaded file, or None on failure.
    """
    os.makedirs(download_folder, exist_ok=True)
    local_filename = os.path.join(download_folder, os.path.basename(url))

    if os.path.exists(local_filename):
        logger.info(f"File already exists, skipping download: {local_filename}")
        return local_filename

    headers = {"User-Agent": settings.REQUESTS_USER_AGENT}
    try:
        with requests.get(url, headers=headers, stream=True) as response:
            response.raise_for_status()
            with open(local_filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        logger.info(f"Successfully downloaded {url} to {local_filename}")
        return local_filename
    except requests.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        return None
