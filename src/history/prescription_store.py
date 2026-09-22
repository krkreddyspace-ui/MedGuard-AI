"""
MedGuard - Persistent Prescription History Manager
Stores scanned prescriptions and active medication lists encrypted at rest in data/prescription_history.json
to enable cross-prescription interaction checking across different dates/months.
"""
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

from cryptography.fernet import Fernet

from config.settings import DATA_DIR
from src.normalization.normalizer import DrugMatchResult

logger = logging.getLogger(__name__)

HISTORY_FILE = DATA_DIR / "prescription_history.json"
KEY_FILE = DATA_DIR / ".history.key"


@dataclass
class PrescriptionRecord:
    """Record representing a scanned or saved prescription."""
    id: str
    title: str
    date: str
    medicines: list[dict] = field(default_factory=list)  # Serialized DrugMatchResult dicts
    active: bool = True
    notes: str = ""

    def get_drug_match_results(self) -> list[DrugMatchResult]:
        """Deserializes stored medicine dicts back to DrugMatchResult objects."""
        results = []
        for m in self.medicines:
            results.append(
                DrugMatchResult(
                    recognized=m.get("recognized", True),
                    brand_name=m.get("brand_name"),
                    generic_name=m.get("generic_name"),
                    confidence=m.get("confidence", 100.0),
                    match_type=m.get("match_type", "exact_generic"),
                    raw_query=m.get("raw_query", ""),
                    message=m.get("message", ""),
                )
            )
        return results


class PrescriptionStore:
    """
    Manages persistent local prescription history encrypted at rest.
    """

    def __init__(self, data_file: Path = HISTORY_FILE, key_file: Path = KEY_FILE):
        self.data_file = data_file
        self.key_file = key_file
        self.cipher: Optional[Fernet] = None
        self._init_cipher()
        self.records: list[PrescriptionRecord] = []
        self._load_records()

    def _init_cipher(self) -> None:
        """Initializes or generates local Fernet encryption key."""
        try:
            self.key_file.parent.mkdir(parents=True, exist_ok=True)
            if self.key_file.exists():
                with open(self.key_file, "rb") as kf:
                    key = kf.read().strip()
            else:
                key = Fernet.generate_key()
                with open(self.key_file, "wb") as kf:
                    kf.write(key)
            self.cipher = Fernet(key)
        except Exception as e:
            logger.error(f"Failed to initialize encryption cipher: {e}")
            self.cipher = None

    def _load_records(self) -> None:
        """Loads prescription records from local encrypted file."""
        if not self.data_file.exists():
            self.records = []
            return

        try:
            with open(self.data_file, "rb") as f:
                raw_content = f.read().strip()

            if not raw_content:
                self.records = []
                return

            decrypted_data: Optional[bytes] = None

            # Try Fernet decryption first
            if self.cipher:
                try:
                    decrypted_data = self.cipher.decrypt(raw_content)
                except Exception:
                    # Fallback to plain UTF-8 if file was unencrypted
                    decrypted_data = raw_content
            else:
                decrypted_data = raw_content

            raw_list = json.loads(decrypted_data.decode("utf-8"))

            self.records = []
            for item in raw_list:
                self.records.append(
                    PrescriptionRecord(
                        id=item.get("id", str(uuid.uuid4())),
                        title=item.get("title", "Prescription"),
                        date=item.get("date", datetime.now().strftime("%Y-%m-%d")),
                        medicines=item.get("medicines", []),
                        active=item.get("active", True),
                        notes=item.get("notes", ""),
                    )
                )
        except Exception as e:
            logger.error(f"Error reading prescription history: {e}")
            self.records = []

    def _save_records(self) -> None:
        """Persists current prescription records encrypted at rest."""
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            raw_list = [asdict(r) for r in self.records]
            json_bytes = json.dumps(raw_list, indent=2).encode("utf-8")

            if self.cipher:
                payload = self.cipher.encrypt(json_bytes)
            else:
                payload = json_bytes

            with open(self.data_file, "wb") as f:
                f.write(payload)
        except Exception as e:
            logger.error(f"Error saving prescription history: {e}")

    def save_prescription(
        self,
        title: str,
        medicines: list[DrugMatchResult],
        active: bool = True,
        notes: str = "",
    ) -> PrescriptionRecord:
        """Saves a new prescription entry to persistent storage."""
        serialized_meds = []
        for m in medicines:
            serialized_meds.append({
                "recognized": m.recognized,
                "brand_name": m.brand_name,
                "generic_name": m.generic_name,
                "confidence": m.confidence,
                "match_type": m.match_type,
                "raw_query": m.raw_query,
                "message": m.message,
            })

        rec = PrescriptionRecord(
            id=str(uuid.uuid4())[:8],
            title=title or f"Prescription #{len(self.records) + 1}",
            date=datetime.now().strftime("%b %d, %Y"),
            medicines=serialized_meds,
            active=active,
            notes=notes,
        )
        self.records.insert(0, rec)
        self._save_records()
        return rec

    def get_all_prescriptions(self) -> list[PrescriptionRecord]:
        return self.records

    def get_active_medications(self) -> list[DrugMatchResult]:
        """
        Returns all active generic medications from past stored prescriptions.
        De-duplicates by generic name.
        """
        seen_generics: set[str] = set()
        active_meds: list[DrugMatchResult] = []

        for rec in self.records:
            if not rec.active:
                continue
            for drug_res in rec.get_drug_match_results():
                if drug_res.recognized and drug_res.generic_name:
                    gen = drug_res.generic_name.lower().strip()
                    if gen not in seen_generics:
                        seen_generics.add(gen)
                        active_meds.append(drug_res)

        return active_meds

    def toggle_active(self, rec_id: str) -> bool:
        """Toggles the active state of a stored prescription."""
        for rec in self.records:
            if rec.id == rec_id:
                rec.active = not rec.active
                self._save_records()
                return rec.active
        return False

    def delete_prescription(self, rec_id: str) -> bool:
        """Removes a prescription record from history."""
        initial_len = len(self.records)
        self.records = [r for r in self.records if r.id != rec_id]
        if len(self.records) < initial_len:
            self._save_records()
            return True
        return False

    def clear_all(self) -> None:
        self.records = []
        self._save_records()


_global_prescription_store: Optional[PrescriptionStore] = None


def get_prescription_store() -> PrescriptionStore:
    global _global_prescription_store
    if _global_prescription_store is None:
        _global_prescription_store = PrescriptionStore()
    return _global_prescription_store
