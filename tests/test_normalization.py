"""
Unit tests for medicine brand-to-generic normalization and fuzzy matching.
"""
from src.normalization.normalizer import MedicineNormalizer


def test_exact_brand_match():
    normalizer = MedicineNormalizer()
    res = normalizer.normalize("Crocin 650 Tablets")
    assert res.recognized is True
    assert res.generic_name == "paracetamol"
    assert res.match_type == "exact_brand"
    assert res.confidence == 100.0


def test_another_brand_match():
    normalizer = MedicineNormalizer()
    res = normalizer.normalize("Ecosprin 75 mg")
    assert res.recognized is True
    assert res.generic_name == "aspirin"
    assert res.brand_name == "Ecosprin"


def test_direct_generic_match():
    normalizer = MedicineNormalizer()
    res = normalizer.normalize("Ibuprofen 400 mg")
    assert res.recognized is True
    assert res.generic_name == "ibuprofen"
    assert res.match_type in ("exact_generic", "exact_brand")


def test_fuzzy_brand_match_with_ocr_typos():
    normalizer = MedicineNormalizer()
    # Minor OCR typo: "Combiflarn" instead of "Combiflam"
    res = normalizer.normalize("Combiflarn 400")
    assert res.recognized is True
    assert res.generic_name == "ibuprofen"
    assert "fuzzy" in res.match_type
    assert res.confidence >= 80.0


def test_unrecognized_medicine_rejection():
    normalizer = MedicineNormalizer()
    res = normalizer.normalize("Xyloguanidine Forte 900")
    assert res.recognized is False
    assert res.generic_name is None
    assert res.match_type == "unrecognized"
