# src/core/image_analysis.py
import hashlib
import os
from typing import Callable

import pandas as pd
import tlsh
from fuzzywuzzy import fuzz
from PIL import Image


# --- Filename Similarity ---
def find_similar_filenames(folder: str, threshold: int = 90) -> pd.DataFrame:
    """
    Finds potential duplicate images based on filename similarity.

    Args:
        folder (str): The path to the folder containing images.
        threshold (int): The similarity ratio threshold (0-100).

    Returns:
        pd.DataFrame: A DataFrame of potential duplicates.
    """
    filenames = [
        f for f in os.listdir(folder) if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]
    potential_duplicates = []

    for i in range(len(filenames)):
        for j in range(i + 1, len(filenames)):
            similarity = fuzz.ratio(filenames[i], filenames[j])
            if similarity >= threshold:
                potential_duplicates.append(
                    {
                        "file_1": filenames[i],
                        "file_2": filenames[j],
                        "similarity_score": similarity,
                    }
                )

    return pd.DataFrame(potential_duplicates)


# --- Exact Duplicates (Cryptographic Hash) ---
def _calculate_crypto_hash(image_path: str, hash_algo: Callable = hashlib.md5) -> str:
    """Calculates the cryptographic hash of an image."""
    hash_obj = hash_algo()
    with Image.open(image_path) as img:
        # Convert to a consistent format to handle minor variations
        img = img.convert("RGB")
        hash_obj.update(img.tobytes())
    return hash_obj.hexdigest()


def find_exact_duplicates(
    folder: str, hash_algo: Callable = hashlib.md5
) -> pd.DataFrame:
    """
    Finds exact duplicate images based on their content hash.

    Args:
        folder (str): Path to the folder with images.
        hash_algo (Callable): The hash function to use from hashlib (e.g., md5, sha256).

    Returns:
        pd.DataFrame: A DataFrame of duplicate file pairs.
    """
    image_hashes = {}
    duplicates = []

    for filename in os.listdir(folder):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            img_path = os.path.join(folder, filename)
            try:
                img_hash = _calculate_crypto_hash(img_path, hash_algo)
                if img_hash in image_hashes:
                    duplicates.append(
                        {"original": image_hashes[img_hash], "duplicate": filename}
                    )
                else:
                    image_hashes[img_hash] = filename
            except Exception:
                continue  # Skip files that can't be opened

    return pd.DataFrame(duplicates)


# --- Visual Similarity (Perceptual Hash) ---
def _calculate_tlsh(image_path: str) -> str:
    """Calculates the TLSH (fuzzy) hash of an image."""
    with Image.open(image_path) as img:
        img = img.convert("RGB")
        img_bytes = img.tobytes()
        return tlsh.hash(img_bytes)


def find_visually_similar_images(
    folder: str, similarity_threshold: int = 100
) -> pd.DataFrame:
    """
    Finds visually similar images using the TLSH fuzzy hashing algorithm.

    Args:
        folder (str): The folder containing images.
        similarity_threshold (int): The maximum difference score to be considered similar.
                                    Lower is more similar. 0 is an exact match.

    Returns:
        pd.DataFrame: DataFrame of similar image pairs and their difference score.
    """
    filenames = [
        f for f in os.listdir(folder) if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]
    hashes = {}
    for filename in filenames:
        try:
            hashes[filename] = _calculate_tlsh(os.path.join(folder, filename))
        except Exception:
            continue

    similar_pairs = []
    items = list(hashes.items())
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            file1, hash1 = items[i]
            file2, hash2 = items[j]
            score = tlsh.diff(hash1, hash2)
            if score <= similarity_threshold:
                similar_pairs.append(
                    {"file_1": file1, "file_2": file2, "difference_score": score}
                )

    return pd.DataFrame(similar_pairs).sort_values(by="difference_score")
