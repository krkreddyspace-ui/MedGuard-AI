"""
MedGuard - Multi-Medicine Prescription OCR Parser
Scans full prescription sheets/receipts containing multiple listed medicines,
extracts all recognizable drug lines, and normalizes them into generic compounds.
"""
from dataclasses import dataclass, field
import re
from typing import Optional, Union
import numpy as np
from PIL import Image

from src.normalization.normalizer import DrugMatchResult, MedicineNormalizer, get_normalizer
from src.ocr.engine import OcrEngine, get_ocr_engine
from src.utils.text_utils import clean_ocr_text, extract_candidate_tokens


@dataclass
class PrescriptionParseResult:
    """Outcome of full prescription document multi-medicine scanning."""
    raw_text: str
    detected_medicines: list[DrugMatchResult] = field(default_factory=list)
    unrecognized_lines: list[str] = field(default_factory=list)
    total_medicines_found: int = 0


class PrescriptionParser:
    """
    Parses multi-medicine prescription documents and receipts.
    """

    def __init__(
        self,
        normalizer: Optional[MedicineNormalizer] = None,
        ocr_engine: Optional[OcrEngine] = None,
    ):
        self.normalizer = normalizer or get_normalizer()
        self.ocr_engine = ocr_engine or get_ocr_engine()

    def parse_text(self, text: str) -> PrescriptionParseResult:
        """
        Parses raw text extracted from a multi-medicine prescription sheet.
        """
        if not text or not text.strip():
            return PrescriptionParseResult(raw_text="", detected_medicines=[], unrecognized_lines=[])

        detected_generics: set[str] = set()
        detected_medicines: list[DrugMatchResult] = []
        unrecognized: list[str] = []

        # Split text by line breaks, commas, semicolons, and bullet numbers
        segments = [s.strip() for s in re.split(r"[\n,;]+", text) if s.strip()]

        for seg in segments:
            match = self.normalizer.normalize(seg)
            if match.recognized and match.generic_name:
                gen = match.generic_name.lower().strip()
                if gen not in detected_generics:
                    detected_generics.add(gen)
                    detected_medicines.append(match)
            else:
                # Try candidate tokens within the segment
                tokens = extract_candidate_tokens(clean_ocr_text(seg))
                seg_recognized = False
                for token in tokens:
                    token_match = self.normalizer.normalize(token)
                    if token_match.recognized and token_match.generic_name:
                        gen = token_match.generic_name.lower().strip()
                        if gen not in detected_generics:
                            detected_generics.add(gen)
                            detected_medicines.append(token_match)
                        seg_recognized = True

                if not seg_recognized and len(seg) > 3:
                    unrecognized.append(seg)

        return PrescriptionParseResult(
            raw_text=text,
            detected_medicines=detected_medicines,
            unrecognized_lines=unrecognized,
            total_medicines_found=len(detected_medicines),
        )

    def parse_image(
        self,
        image: Union[Image.Image, np.ndarray],
    ) -> PrescriptionParseResult:
        """
        Runs OCR on a full prescription image and parses all detected medicines.
        """
        ocr_res = self.ocr_engine.extract_text(image)
        if not ocr_res.success or not ocr_res.raw_text:
            return PrescriptionParseResult(
                raw_text=ocr_res.raw_text or "",
                detected_medicines=[],
                unrecognized_lines=[ocr_res.error_message] if ocr_res.error_message else [],
            )

        lines = [line.text for line in ocr_res.text_lines if line.text]
        combined_text = "\n".join(lines) if lines else ocr_res.raw_text
        return self.parse_text(combined_text)


_global_prescription_parser: Optional[PrescriptionParser] = None


def get_prescription_parser() -> PrescriptionParser:
    global _global_prescription_parser
    if _global_prescription_parser is None:
        _global_prescription_parser = PrescriptionParser()
    return _global_prescription_parser
