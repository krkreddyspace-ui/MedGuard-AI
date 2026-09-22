"""
MedGuard - OCR Bounding Box Overlay Generator
Draws bounding box annotations on in-memory images strictly in RAM.
Zero disk persistence guarantee.
"""
import logging
from typing import Optional, Union
import numpy as np
from PIL import Image

from src.ocr.engine import OcrTextLine

logger = logging.getLogger(__name__)


def draw_ocr_bounding_boxes(
    image: Union[np.ndarray, Image.Image],
    text_lines: list[OcrTextLine],
    highlight_words: Optional[list[str]] = None,
    box_color: tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
) -> np.ndarray:
    """
    Draws bounding box rectangle(s) around recognized OCR text lines on an in-memory copy of the image.
    Follows zero-disk-persistence rules (operates strictly in RAM array copies).
    Returns the annotated image as a numpy array.
    """
    import cv2

    if image is None:
        raise ValueError("Cannot draw bounding boxes on None image.")

    # Convert to numpy uint8 RGB array copy
    if isinstance(image, Image.Image):
        img_arr = np.array(image.convert("RGB")).copy()
    else:
        img_arr = np.array(image, copy=True)

    if img_arr.size == 0:
        return img_arr

    # Ensure 3-channel RGB image
    if len(img_arr.shape) == 2:
        img_arr = cv2.cvtColor(img_arr, cv2.COLOR_GRAY2RGB)

    targets = [w.lower().strip() for w in highlight_words] if highlight_words else []

    for line in text_lines:
        if not line.bbox:
            continue

        text_lower = line.text.lower()
        if targets:
            is_matched = any(tgt in text_lower for tgt in targets)
            color = (0, 255, 0) if is_matched else (255, 200, 0)
        else:
            color = box_color

        bbox = line.bbox
        try:
            if isinstance(bbox, (list, tuple, np.ndarray)):
                if len(bbox) == 4 and isinstance(bbox[0], (list, tuple, np.ndarray)):
                    # 4 points [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                    pts = np.int32(bbox)
                    cv2.polylines(img_arr, [pts], isClosed=True, color=color, thickness=thickness)
                    x_min = int(min(p[0] for p in pts))
                    y_min = int(min(p[1] for p in pts))
                    cv2.putText(
                        img_arr,
                        line.text[:20],
                        (max(0, x_min), max(15, y_min - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        color,
                        1,
                        cv2.LINE_AA,
                    )
                elif len(bbox) == 4 and all(isinstance(v, (int, float, np.number)) for v in bbox):
                    # [x1, y1, x2, y2]
                    x1, y1, x2, y2 = map(int, bbox)
                    cv2.rectangle(img_arr, (x1, y1), (x2, y2), color=color, thickness=thickness)
                    cv2.putText(
                        img_arr,
                        line.text[:20],
                        (max(0, x1), max(15, y1 - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        color,
                        1,
                        cv2.LINE_AA,
                    )
        except Exception as err:
            logger.debug(f"Skipping bounding box draw error: {err}")
            continue

    return img_arr
