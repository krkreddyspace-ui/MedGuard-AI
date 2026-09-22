"""
MedGuard - Medicine Normalization Engine
Normalizes raw OCR text / commercial brand names to canonical active pharmaceutical ingredients (generics).
Enforces conservative thresholds to prevent false or hallucinated identifications.
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from config.settings import (
    BRAND_GENERIC_MAP_FILE,
    FUZZY_MATCH_THRESHOLD,
    INTERACTIONS_FILE,
)
from src.normalization.fuzzy_matcher import match_best_candidate
from src.utils.text_utils import clean_ocr_text, extract_candidate_tokens


@dataclass
class DrugMatchResult:
    """Structured normalization result."""
    recognized: bool
    brand_name: Optional[str]
    generic_name: Optional[str]
    confidence: float
    match_type: str  # "exact_brand", "exact_generic", "fuzzy_brand", "fuzzy_generic", "unrecognized"
    raw_query: str
    message: str = ""
    annotated_image: Optional[object] = None


class MedicineNormalizer:
    """
    Normalizes medicine strip OCR text into canonical generic active ingredients.
    """

    def __init__(
        self,
        brand_map_path: Path = BRAND_GENERIC_MAP_FILE,
        interactions_path: Path = INTERACTIONS_FILE,
        fuzzy_threshold: float = FUZZY_MATCH_THRESHOLD,
    ):
        self.brand_map_path = brand_map_path
        self.interactions_path = interactions_path
        self.fuzzy_threshold = fuzzy_threshold
        self.brand_to_generic: dict[str, str] = {}
        self.known_generics: set[str] = set()
        self._load_vocabularies()

    def _load_vocabularies(self) -> None:
        """Loads brand mappings and known generic compounds from local datasets."""
        if self.brand_map_path.exists():
            with open(self.brand_map_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.brand_to_generic = {k.lower().strip(): v.lower().strip() for k, v in data.items()}
                for gen in self.brand_to_generic.values():
                    self.known_generics.add(gen)

        if self.interactions_path.exists():
            with open(self.interactions_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    self.known_generics.add(item["drug_a"].lower().strip())
                    self.known_generics.add(item["drug_b"].lower().strip())

    def normalize(self, raw_text: str) -> DrugMatchResult:
        """
        Processes raw text or OCR output, extracts candidates, and matches against
        known brand and generic catalogs.
        """
        cleaned_text = clean_ocr_text(raw_text)
        if not cleaned_text:
            return DrugMatchResult(
                recognized=False,
                brand_name=None,
                generic_name=None,
                confidence=0.0,
                match_type="unrecognized",
                raw_query=raw_text,
                message="No readable text found.",
            )

        candidates = extract_candidate_tokens(cleaned_text)

        # 1. Check for EXACT matches across candidates
        # Priority A: Exact match in brand map
        for cand in candidates:
            if cand in self.brand_to_generic:
                return DrugMatchResult(
                    recognized=True,
                    brand_name=cand.title(),
                    generic_name=self.brand_to_generic[cand],
                    confidence=100.0,
                    match_type="exact_brand",
                    raw_query=raw_text,
                    message=f"Exact brand match: {cand.title()} -> {self.brand_to_generic[cand].title()}",
                )

        # Priority B: Exact match with canonical generic
        for cand in candidates:
            if cand in self.known_generics:
                return DrugMatchResult(
                    recognized=True,
                    brand_name=None,
                    generic_name=cand,
                    confidence=100.0,
                    match_type="exact_generic",
                    raw_query=raw_text,
                    message=f"Direct generic match: {cand.title()}",
                )

        # 2. Check for FUZZY matches across candidates
        best_brand_match: Optional[tuple[str, str, float]] = None  # (brand, generic, score)
        best_generic_match: Optional[tuple[str, float]] = None     # (generic, score)

        brand_keys = list(self.brand_to_generic.keys())
        generic_keys = list(self.known_generics)

        for cand in candidates:
            # Match against brands
            brand_res = match_best_candidate(cand, brand_keys, score_cutoff=self.fuzzy_threshold)
            if brand_res:
                matched_brand, score = brand_res
                if best_brand_match is None or score > best_brand_match[2]:
                    best_brand_match = (matched_brand, self.brand_to_generic[matched_brand], score)

            # Match against generics
            gen_res = match_best_candidate(cand, generic_keys, score_cutoff=self.fuzzy_threshold)
            if gen_res:
                matched_gen, score = gen_res
                if best_generic_match is None or score > best_generic_match[1]:
                    best_generic_match = (matched_gen, score)

        # Compare best brand fuzzy vs best generic fuzzy
        brand_score = best_brand_match[2] if best_brand_match else 0.0
        generic_score = best_generic_match[1] if best_generic_match else 0.0

        if brand_score >= self.fuzzy_threshold and brand_score >= generic_score:
            matched_brand, gen_name, score = best_brand_match
            return DrugMatchResult(
                recognized=True,
                brand_name=matched_brand.title(),
                generic_name=gen_name,
                confidence=round(score, 1),
                match_type="fuzzy_brand",
                raw_query=raw_text,
                message=f"Fuzzy brand match ({score:.0f}%): {matched_brand.title()} -> {gen_name.title()}",
            )

        if generic_score >= self.fuzzy_threshold:
            matched_gen, score = best_generic_match
            return DrugMatchResult(
                recognized=True,
                brand_name=None,
                generic_name=matched_gen,
                confidence=round(score, 1),
                match_type="fuzzy_generic",
                raw_query=raw_text,
                message=f"Fuzzy generic match ({score:.0f}%): {matched_gen.title()}",
            )

        # 3. Fallback: Medicine not recognized
        highest_score = max(brand_score, generic_score)
        return DrugMatchResult(
            recognized=False,
            brand_name=None,
            generic_name=None,
            confidence=round(highest_score, 1),
            match_type="unrecognized",
            raw_query=raw_text,
            message="Medicine not confidently recognized.",
        )


# Singleton instance for application use
_global_normalizer: Optional[MedicineNormalizer] = None


def get_normalizer() -> MedicineNormalizer:
    global _global_normalizer
    if _global_normalizer is None:
        _global_normalizer = MedicineNormalizer()
    return _global_normalizer
