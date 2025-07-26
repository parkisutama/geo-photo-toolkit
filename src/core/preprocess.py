# src/core/preprocess.py
"""
Image preprocessing module for OCR, with dynamic method selection based on image characteristics.
"""

import os

import cv2
import numpy as np


def analyze_image_characteristics(image_path: str) -> dict:
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)
    std_brightness = np.std(gray)
    noise = cv2.Laplacian(gray, cv2.CV_64F).var()
    # Add more analysis as needed
    return {
        "mean_brightness": mean_brightness,
        "std_brightness": std_brightness,
        "noise": noise,
    }


def preprocess_image(
    image_path: str, method: str = "auto", debug_folder: str = None
) -> str:
    img = cv2.imread(image_path)
    characteristics = analyze_image_characteristics(image_path)
    chosen_method = method.lower()
    # Auto mode: choose method based on characteristics
    if chosen_method == "auto":
        if characteristics["mean_brightness"] < 80:
            chosen_method = "brighten"
        elif characteristics["noise"] > 100:
            chosen_method = "denoise"
        elif characteristics["std_brightness"] > 50:
            chosen_method = "threshold"
        else:
            chosen_method = "none"
    # Apply chosen preprocessing
    if chosen_method == "brighten":
        img = cv2.convertScaleAbs(img, alpha=1.5, beta=30)
    elif chosen_method == "denoise":
        img = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
    elif chosen_method == "deskew":
        # Deskew not implemented, placeholder
        pass
    # Always convert to grayscale for OCR
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if chosen_method == "threshold":
        img = cv2.adaptiveThreshold(
            img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2
        )
    # Save preprocessed image if debug_folder is set
    if debug_folder:
        os.makedirs(debug_folder, exist_ok=True)
        debug_path = os.path.join(debug_folder, os.path.basename(image_path))
        cv2.imwrite(debug_path, img)
        return debug_path
    # Optionally, return path to temp file or processed image array
    return None
