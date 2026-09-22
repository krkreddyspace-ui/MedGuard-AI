"""
Unit tests for text cleaning and candidate token extraction.
"""
from src.utils.text_utils import (
    clean_ocr_text,
    extract_candidate_tokens,
    normalize_case,
    normalize_whitespace,
    remove_packaging_noise,
)


def test_normalize_whitespace():
    raw = "   Crocin   650   \n\t  Tablets   "
    assert normalize_whitespace(raw) == "Crocin 650 Tablets"


def test_normalize_case():
    assert normalize_case("Ecosprin 75 MG") == "ecosprin 75 mg"


def test_remove_packaging_noise_batch_and_expiry():
    raw = "Combiflam B.No. 8923A Exp: 12/2026 Mfg: 01/2024"
    cleaned = remove_packaging_noise(raw)
    assert "8923A" not in cleaned
    assert "12/2026" not in cleaned
    assert "combiflam" in cleaned.lower()


def test_remove_packaging_noise_dosage_and_forms():
    raw = "Dolo 650 mg Tablets IP Paracetamol 500mg capsules"
    cleaned = remove_packaging_noise(raw)
    assert "mg" not in cleaned
    assert "tablets" not in cleaned
    assert "ip" not in cleaned


def test_clean_ocr_text():
    raw = "Ecosprin-75 (Aspirin Gastro-resistant Tablets I.P.) B.No: AB123 Exp: 05/27"
    cleaned = clean_ocr_text(raw)
    assert "ecosprin" in cleaned
    assert "aspirin" in cleaned
    assert "ab123" not in cleaned


def test_extract_candidate_tokens():
    cleaned = "ecosprin aspirin gastro"
    tokens = extract_candidate_tokens(cleaned)
    assert "ecosprin" in tokens
    assert "aspirin" in tokens
    assert "ecosprin aspirin" in tokens
