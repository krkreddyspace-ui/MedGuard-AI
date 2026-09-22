"""OCR processing and framing guide package."""
from .bounding_box import draw_ocr_bounding_boxes
from .engine import OcrEngine, OcrResult, OcrTextLine, get_ocr_engine
from .framing_guide import FramingState, analyze_framing, compute_scan_zone, render_guidance_overlay
from .preprocessing import preprocess_for_ocr

__all__ = [
    "FramingState",
    "OcrEngine",
    "OcrResult",
    "OcrTextLine",
    "analyze_framing",
    "compute_scan_zone",
    "draw_ocr_bounding_boxes",
    "get_ocr_engine",
    "preprocess_for_ocr",
    "render_guidance_overlay",
]
