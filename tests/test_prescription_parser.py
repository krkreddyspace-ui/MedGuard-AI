"""
Unit tests for multi-medicine prescription parser module.
"""
from src.ocr.prescription_parser import PrescriptionParser, get_prescription_parser


def test_parse_text_multiple_medicines():
    parser = get_prescription_parser()
    text = """
    Rx Medical Prescription
    1. Ecosprin 75 mg - 1 tab daily
    2. Combiflam - 1 tab as needed for pain
    3. Pan-D - 1 cap before breakfast
    """
    res = parser.parse_text(text)
    assert res.total_medicines_found >= 2
    generics = [m.generic_name for m in res.detected_medicines]
    assert "aspirin" in generics
    assert "ibuprofen" in generics


def test_parse_text_comma_separated():
    parser = PrescriptionParser()
    text = "Patient prescribed: Crocin 650, Cetzine 10mg, Atorlip 10"
    res = parser.parse_text(text)
    generics = [m.generic_name for m in res.detected_medicines]
    assert "paracetamol" in generics
    assert "cetirizine" in generics
    assert "atorvastatin" in generics


def test_parse_empty_text():
    parser = PrescriptionParser()
    res = parser.parse_text("")
    assert res.total_medicines_found == 0
    assert len(res.detected_medicines) == 0
