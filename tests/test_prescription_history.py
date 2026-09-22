"""
Unit tests for prescription history store module.
"""
from pathlib import Path
import tempfile
from src.history.prescription_store import PrescriptionStore
from src.normalization.normalizer import DrugMatchResult


def test_prescription_store_crud():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_file = Path(tmp_dir) / "test_history.json"
        tmp_key = Path(tmp_dir) / "test_key.key"
        store = PrescriptionStore(data_file=tmp_file, key_file=tmp_key)

        assert len(store.get_all_prescriptions()) == 0

        med1 = DrugMatchResult(
            recognized=True,
            brand_name="Ecosprin",
            generic_name="aspirin",
            confidence=100.0,
            match_type="exact_brand",
            raw_query="Ecosprin",
        )
        med2 = DrugMatchResult(
            recognized=True,
            brand_name="Combiflam",
            generic_name="ibuprofen",
            confidence=100.0,
            match_type="exact_brand",
            raw_query="Combiflam",
        )

        rec = store.save_prescription("Prescription July 2026", [med1, med2])
        assert rec.id is not None
        assert len(store.get_all_prescriptions()) == 1

        active_meds = store.get_active_medications()
        assert len(active_meds) == 2
        generics = [m.generic_name for m in active_meds]
        assert "aspirin" in generics
        assert "ibuprofen" in generics

        # Reload store from disk with key
        store2 = PrescriptionStore(data_file=tmp_file, key_file=tmp_key)
        assert len(store2.get_all_prescriptions()) == 1

        # Toggle active
        store2.toggle_active(rec.id)
        assert len(store2.get_active_medications()) == 0

        # Delete
        deleted = store2.delete_prescription(rec.id)
        assert deleted is True
        assert len(store2.get_all_prescriptions()) == 0


def test_prescription_history_encrypted_at_rest():
    """Verifies that saved prescription history on disk is encrypted and not human-readable JSON."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_file = Path(tmp_dir) / "encrypted_history.json"
        tmp_key = Path(tmp_dir) / "test_key.key"
        store = PrescriptionStore(data_file=tmp_file, key_file=tmp_key)

        med = DrugMatchResult(
            recognized=True,
            brand_name="Crocin",
            generic_name="paracetamol",
            confidence=100.0,
            match_type="exact_brand",
            raw_query="Crocin 650",
        )
        store.save_prescription("Private Doctor Visit", [med])

        # Read raw content directly from disk
        raw_disk_bytes = tmp_file.read_bytes()
        raw_disk_str = raw_disk_bytes.decode("utf-8", errors="ignore")

        # Must NOT contain plain text JSON keywords or generic drug names
        assert "paracetamol" not in raw_disk_str
        assert "Crocin" not in raw_disk_str
        assert "Private Doctor Visit" not in raw_disk_str
        assert raw_disk_bytes.startswith(b"gAAAAA")  # Fernet encrypted payload header


def test_timeline_receives_severity_flagged_pairs():
    """Confirms timeline generator maps cross-prescription interactions to severity-flagged connections."""
    from src.history.timeline_generator import build_timeline_data, render_timeline_html
    from src.interaction.models import EnsembleInteractionResult, InteractionResult, InteractionStatus, OriginType, SeverityLevel

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_file = Path(tmp_dir) / "test_history.json"
        tmp_key = Path(tmp_dir) / "test_key.key"
        store = PrescriptionStore(data_file=tmp_file, key_file=tmp_key)

        med_asp = DrugMatchResult(
            recognized=True, brand_name="Ecosprin", generic_name="aspirin", confidence=100.0, match_type="exact", raw_query="aspirin"
        )
        med_war = DrugMatchResult(
            recognized=True, brand_name="Coumadin", generic_name="warfarin", confidence=100.0, match_type="exact", raw_query="warfarin"
        )

        rec1 = store.save_prescription("Old Rx June 2026", [med_asp])
        rec2 = store.save_prescription("New Rx August 2026", [med_war])
        all_recs = store.get_all_prescriptions()

        # Mock an EnsembleInteractionResult containing a HIGH severity cross-prescription interaction
        pair = InteractionResult(
            status=InteractionStatus.INTERACTION_FOUND,
            drug_a_label="Ecosprin",
            drug_a_generic="aspirin",
            drug_b_label="Coumadin",
            drug_b_generic="warfarin",
            severity=SeverityLevel.HIGH,
            origin=OriginType.CROSS_PRESCRIPTION,
            mechanism="Combined antiplatelet and anticoagulant effect increases bleeding risk.",
        )
        ensemble_res = EnsembleInteractionResult(
            total_drugs_checked=2,
            interacting_pairs=[pair],
            no_interaction_pairs=[],
        )

        nodes, connections = build_timeline_data(all_recs, ensemble_res)

        assert len(nodes) == 2
        assert len(connections) == 1
        conn = connections[0]
        assert conn.severity == SeverityLevel.HIGH
        assert conn.color == "#ef4444"
        assert conn.from_id in (rec1.id, rec2.id)
        assert conn.to_id in (rec1.id, rec2.id)

        html = render_timeline_html(nodes, connections)
        assert "aspirin" in html.lower() or "ecosprin" in html.lower()
        assert "#ef4444" in html
        assert "High Severity" in html

