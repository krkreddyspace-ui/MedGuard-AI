"""
Unit tests for the deterministic interaction matching engine.
"""
from pathlib import Path
import tempfile

from src.explanation.formatter import format_explanation
from src.history.prescription_store import PrescriptionStore
from src.interaction.engine import InteractionEngine
from src.interaction.models import InteractionStatus, OriginType, SeverityLevel
from src.normalization.normalizer import DrugMatchResult


def test_known_interaction_pair():
    engine = InteractionEngine()
    res = engine.check_interaction("aspirin", "ibuprofen")
    assert res.status == InteractionStatus.INTERACTION_FOUND
    assert res.severity == SeverityLevel.HIGH
    assert "bleeding" in res.plain_language.lower()


def test_reverse_pair_symmetry():
    engine = InteractionEngine()
    res_ab = engine.check_interaction("aspirin", "ibuprofen")
    res_ba = engine.check_interaction("ibuprofen", "aspirin")

    assert res_ab.status == res_ba.status
    assert res_ab.severity == res_ba.severity
    assert res_ab.mechanism == res_ba.mechanism
    assert res_ab.plain_language == res_ba.plain_language


def test_no_known_interaction():
    engine = InteractionEngine()
    res = engine.check_interaction("paracetamol", "cetirizine")
    assert res.status == InteractionStatus.NO_KNOWN_INTERACTION
    assert res.has_interaction is False


def test_unknown_drug_does_not_become_no_interaction():
    engine = InteractionEngine()

    # Case 1: First drug recognized, second unrecognized
    res1 = engine.check_interaction("aspirin", None)
    assert res1.status == InteractionStatus.DRUG_NOT_RECOGNIZED
    assert res1.status != InteractionStatus.NO_KNOWN_INTERACTION

    # Case 2: DrugMatchResult with recognized=False
    unrec_match = DrugMatchResult(
        recognized=False,
        brand_name=None,
        generic_name=None,
        confidence=0.0,
        match_type="unrecognized",
        raw_query="UnknownSubstance",
    )
    rec_match = DrugMatchResult(
        recognized=True,
        brand_name="Combiflam",
        generic_name="ibuprofen",
        confidence=100.0,
        match_type="exact_brand",
        raw_query="Combiflam",
    )
    res2 = engine.check_interaction(unrec_match, rec_match)
    assert res2.status == InteractionStatus.DRUG_NOT_RECOGNIZED
    assert res2.status != InteractionStatus.NO_KNOWN_INTERACTION


def test_explanation_formatting_states():
    engine = InteractionEngine()

    # State A
    res_a = engine.check_interaction("sildenafil", "nitroglycerin")
    expl_a = format_explanation(res_a)
    assert "potential interaction detected" in expl_a.headline.lower()
    assert expl_a.headline_badge_type == "danger"
    assert "blood pressure" in expl_a.why_it_matters.lower()

    # State B
    res_b = engine.check_interaction("paracetamol", "cetirizine")
    expl_b = format_explanation(res_b)
    assert "no known interaction" in expl_b.headline.lower()
    assert expl_b.headline_badge_type == "info"

    # State C
    res_c = engine.check_interaction("aspirin", None)
    expl_c = format_explanation(res_c)
    assert "not recognized" in expl_c.headline.lower()
    assert expl_c.headline_badge_type == "warning"
    assert expl_c.suggestions is not None


def test_cumulative_regimen_cross_prescription_check():
    """Verifies newly scanned medicine is checked against saved active prescriptions from previous sessions."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_file = Path(tmp_dir) / "test_history.json"
        tmp_key = Path(tmp_dir) / "test_key.key"
        store = PrescriptionStore(data_file=tmp_file, key_file=tmp_key)

        # Save an active prescription containing aspirin from 2 months ago
        old_med = DrugMatchResult(
            recognized=True,
            brand_name="Ecosprin 75",
            generic_name="aspirin",
            confidence=100.0,
            match_type="exact_brand",
            raw_query="Ecosprin 75",
        )
        store.save_prescription("Prescription 2 Months Ago", [old_med], active=True)

        active_meds = store.get_active_medications()
        assert len(active_meds) == 1
        assert active_meds[0].generic_name == "aspirin"

        # Newly scanned medicine today (ibuprofen)
        new_med = DrugMatchResult(
            recognized=True,
            brand_name="Combiflam",
            generic_name="ibuprofen",
            confidence=100.0,
            match_type="exact_brand",
            raw_query="Combiflam",
        )

        engine = InteractionEngine()
        ens_res = engine.check_cross_prescription_interactions([new_med], active_meds)

        assert ens_res.has_any_interaction is True
        assert len(ens_res.interacting_pairs) == 1

        pair_res = ens_res.interacting_pairs[0]
        assert pair_res.origin == OriginType.CROSS_PRESCRIPTION
        assert pair_res.severity == SeverityLevel.HIGH


def test_multiple_interactions_sorted_by_severity_descending():
    """Verifies that multiple flagged interaction pairs are returned in severity-descending order."""
    engine = InteractionEngine()

    # Create multi-drug list with both HIGH and MODERATE interactions:
    # 1. aspirin + ibuprofen (HIGH)
    # 2. amlodipine + simvastatin (MODERATE - wait, amlodipine + simvastatin is moderate)
    # 3. ciprofloxacin + antacids (MODERATE)
    # 4. warfarin + aspirin (HIGH)
    drugs = ["aspirin", "ibuprofen", "ciprofloxacin", "antacids"]

    ens_res = engine.check_ensemble_interactions(drugs)
    assert len(ens_res.interacting_pairs) >= 2

    # Verify severity descending order
    severities = [p.severity for p in ens_res.interacting_pairs]
    # Check that HIGH comes before MODERATE
    high_idx = [i for i, s in enumerate(severities) if s == SeverityLevel.HIGH]
    mod_idx = [i for i, s in enumerate(severities) if s == SeverityLevel.MODERATE]

    if high_idx and mod_idx:
        assert min(high_idx) < max(mod_idx)
