"""
Unit tests for ChemicalCompositionEngine module.
"""
from src.chemical.engine import ChemicalEngine, get_chemical_engine


def test_chemical_engine_lookup():
    engine = get_chemical_engine()
    prof = engine.get_profile("aspirin")
    assert prof is not None
    assert "Acetylsalicylic acid" in prof.chemical_name
    assert "Salicylate" in prof.chemical_class


def test_chemical_engine_combination_lookup():
    engine = ChemicalEngine()
    prof = engine.get_profile("aspirin + ibuprofen")
    assert prof is not None
    assert "Acetylsalicylic acid" in prof.chemical_name
    assert "isobutylphenyl" in prof.chemical_name


def test_chemical_engine_missing():
    engine = ChemicalEngine()
    prof = engine.get_profile("nonexistent_compound_123")
    assert prof is None
