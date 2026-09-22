"""
MedGuard - Computer Vision Image Preprocessing Pipeline
Prepares medicine strip images for optimal OCR accuracy.
All transformations execute strictly in RAM using OpenCV and NumPy.
"""
from typing import Union
import cv2
import numpy as np
from PIL import Image

from config.settings import MAX_IMAGE_DIMENSION, MIN_IMAGE_DIMENSION


def pil_to_cv2(pil_img: Image.Image) -> np.ndarray:
    """Converts a PIL Image to an OpenCV BGR numpy array."""
    rgb_arr = np.array(pil_img.convert("RGB"))
    return cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)


def cv2_to_pil(cv2_img: np.ndarray) -> Image.Image:
    """Converts an OpenCV BGR or Grayscale numpy array to a PIL Image."""
    if len(cv2_img.shape) == 2:
        return Image.fromarray(cv2_img)
    rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def resize_if_needed(img: np.ndarray) -> np.ndarray:
    """
    Resizes image to an optimal resolution for OCR:
    - Upscales small crops where text might be too low-resolution.
    - Downscales giant images to save processing latency without losing legibility.
    """
    h, w = img.shape[:2]

    # Upscale small images
    if min(h, w) < MIN_IMAGE_DIMENSION:
        scale = float(MIN_IMAGE_DIMENSION) / float(min(h, w))
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

    # Downscale overly huge images
    if max(h, w) > MAX_IMAGE_DIMENSION:
        scale = float(MAX_IMAGE_DIMENSION) / float(max(h, w))
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    return img


def enhance_contrast(gray_img: np.ndarray) -> np.ndarray:
    """
    Applies CLAHE (Contrast Limited Adaptive Histogram Equalization)
    to handle reflections, blister pack glare, and uneven illumination on medicine foils.
    """
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray_img)


def sharpen_image(gray_img: np.ndarray) -> np.ndarray:
    """
    Applies an unsharp mask filter to enhance edge definition of printed drug text.
    """
    gaussian = cv2.GaussianBlur(gray_img, (0, 0), sigmaX=1.5)
    sharpened = cv2.addWeighted(gray_img, 1.5, gaussian, -0.5, 0)
    return sharpened


def preprocess_for_ocr(
    source: Union[Image.Image, np.ndarray],
    apply_binarization: bool = False,
) -> np.ndarray:
    """
    Full in-memory preprocessing pipeline for medicine-strip OCR.

    Steps:
    1. Convert PIL to OpenCV format if needed.
    2. Resize to optimal scale.
    3. Convert to Grayscale.
    4. Apply CLAHE contrast enhancement for foil/blister packs.
    5. Sharpen text contours.
    6. Optional Otsu binarization for high-noise backgrounds.

    Returns:
        Processed grayscale numpy array ready for EasyOCR or other OCR backends.
    """
    if isinstance(source, Image.Image):
        cv_img = pil_to_cv2(source)
    else:
        cv_img = source.copy()

    # 1. Resize bounds
    resized = resize_if_needed(cv_img)

    # 2. Convert to Grayscale
    if len(resized.shape) == 3:
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    else:
        gray = resized

    # 3. Enhance Contrast (CLAHE)
    contrasted = enhance_contrast(gray)

    # 4. Sharpen
    sharpened = sharpen_image(contrasted)

    # 5. Optional Adaptive Thresholding / Binarization
    if apply_binarization:
        _, binary = cv2.threshold(
            sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        return binary

    return sharpened
