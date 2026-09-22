"""
MedGuard - Offline OCR Engine
Executes text extraction strictly locally using EasyOCR models loaded from models/easyocr/.
Never makes runtime network calls (download_enabled=False).
"""
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union
import numpy as np
from PIL import Image

from config.settings import (
    DEFAULT_OCR_LANGUAGES,
    EASYOCR_MODEL_DIR,
    OCR_CONFIDENCE_THRESHOLD,
)
from src.ocr.preprocessing import preprocess_for_ocr

logger = logging.getLogger(__name__)


@dataclass
class OcrTextLine:
    """Individual line detected by the OCR engine."""
    text: str
    confidence: float
    bbox: Optional[list] = None


@dataclass
class OcrResult:
    """Structured result returned from the OCR engine."""
    raw_text: str = ""
    confidence: float = 0.0
    text_lines: list[OcrTextLine] = field(default_factory=list)
    engine: str = "EasyOCR (Offline)"
    success: bool = True
    error_message: Optional[str] = None


class OcrEngine:
    """
    Offline OCR engine wrapper ensuring zero network calls during runtime.
    Loads models exclusively from the local models/easyocr directory.
    """

    def __init__(self, model_dir: Path = EASYOCR_MODEL_DIR):
        self.model_dir = model_dir
        self._reader = None
        self._initialized = False

    def is_model_available(self) -> bool:
        """Verifies that local model weights are present in the model directory."""
        if not self.model_dir.exists():
            return False
        # Needs CRAFT detector and recognition model
        has_craft = any("craft" in f.name.lower() for f in self.model_dir.iterdir())
        has_recog = any("english" in f.name.lower() or ".pth" in f.name.lower() for f in self.model_dir.iterdir())
        return has_craft and has_recog

    def _init_reader(self) -> None:
        """Initializes the EasyOCR reader with download_enabled=False."""
        if self._initialized:
            return

        if not self.is_model_available():
            raise FileNotFoundError(
                f"Local EasyOCR model weights not found in {self.model_dir.resolve()}. "
                "Please run 'python scripts/download_models.py' once to download weights for offline use."
            )

        try:
            import easyocr

            # STRICT OFFLINE SETTINGS: download_enabled=False
            self._reader = easyocr.Reader(
                DEFAULT_OCR_LANGUAGES,
                gpu=False,
                model_storage_directory=str(self.model_dir),
                download_enabled=False,
                verbose=False,
            )
            self._initialized = True
        except Exception as e:
            raise RuntimeError(f"Failed to initialize local EasyOCR reader: {e}") from e

    def extract_text(
        self,
        image: Union[Image.Image, np.ndarray],
        apply_preprocessing: bool = True,
    ) -> OcrResult:
        """
        Runs OCR on a medicine strip image.
        Executes entirely in RAM.
        """
        if image is None:
            return OcrResult(
                success=False,
                error_message="Couldn't read the medicine name clearly (No image supplied).",
            )

        try:
            self._init_reader()
        except Exception as init_err:
            return OcrResult(
                success=False,
                error_message=f"OCR initialization error: {str(init_err)}",
            )

        try:
            # 1. Run in-memory preprocessing
            if apply_preprocessing:
                processed_arr = preprocess_for_ocr(image)
            elif isinstance(image, Image.Image):
                processed_arr = np.array(image.convert("RGB"))
            else:
                processed_arr = image

            # 2. Run EasyOCR readtext
            # results format: [ (bbox, text, prob), ... ]
            raw_detections = self._reader.readtext(processed_arr)

            if not raw_detections:
                return OcrResult(
                    raw_text="",
                    confidence=0.0,
                    text_lines=[],
                    success=True,
                    error_message=None,
                )

            extracted_lines: list[OcrTextLine] = []
            text_parts: list[str] = []
            confidences: list[float] = []

            for item in raw_detections:
                bbox, text, prob = item[0], item[1], float(item[2])
                cleaned = text.strip()
                if cleaned:
                    extracted_lines.append(
                        OcrTextLine(text=cleaned, confidence=prob, bbox=bbox)
                    )
                    text_parts.append(cleaned)
                    confidences.append(prob)

            full_text = " ".join(text_parts)
            avg_conf = float(np.mean(confidences)) if confidences else 0.0

            return OcrResult(
                raw_text=full_text,
                confidence=avg_conf,
                text_lines=extracted_lines,
                engine="EasyOCR (Offline)",
                success=True,
            )

        except Exception as ocr_err:
            logger.error(f"OCR execution error: {ocr_err}", exc_info=True)
            return OcrResult(
                success=False,
                error_message=f"Couldn't read the medicine name clearly: {str(ocr_err)}",
            )


# Global singleton instance for Streamlit session reuse
_global_ocr_engine: Optional[OcrEngine] = None


def get_ocr_engine() -> OcrEngine:
    global _global_ocr_engine
    if _global_ocr_engine is None:
        _global_ocr_engine = OcrEngine()
    return _global_ocr_engine
