"""
MedGuard - Chemical & Biological Composition Engine
Provides active compound structural breakdowns, chemical classifications, target binding sites,
and metabolic pathways for generic active pharmaceutical ingredients.
"""
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from config.settings import DATA_DIR

logger = logging.getLogger(__name__)

CHEMICAL_COMPOSITIONS_FILE = DATA_DIR / "chemical_compositions.json"


@dataclass
class ChemicalProfile:
    """Detailed chemical composition breakdown for an active ingredient."""
    generic_name: str
    chemical_name: str
    chemical_class: str
    pharmacological_class: str
    target_site: str
    metabolic_pathway: str


class ChemicalEngine:
    """
    Lookup engine for active pharmaceutical ingredient chemical properties.
    """

    def __init__(self, data_file: Path = CHEMICAL_COMPOSITIONS_FILE):
        self.data_file = data_file
        self.profiles: dict[str, ChemicalProfile] = {}
        self._load_data()

    def _load_data(self) -> None:
        """Loads chemical composition mapping from local dataset."""
        if not self.data_file.exists():
            logger.warning(f"Chemical compositions file not found at {self.data_file}")
            return

        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            for key, val in raw_data.items():
                gen_key = key.lower().strip()
                self.profiles[gen_key] = ChemicalProfile(
                    generic_name=gen_key.title(),
                    chemical_name=val.get("chemical_name", "N/A"),
                    chemical_class=val.get("chemical_class", "N/A"),
                    pharmacological_class=val.get("pharmacological_class", "N/A"),
                    target_site=val.get("target_site", "N/A"),
                    metabolic_pathway=val.get("metabolic_pathway", "N/A"),
                )
        except Exception as e:
            logger.error(f"Error loading chemical compositions: {e}")

    def get_profile(self, generic_name: Optional[str]) -> Optional[ChemicalProfile]:
        """Retrieves chemical profile for generic active ingredient."""
        if not generic_name:
            return None
        key = generic_name.lower().strip()

        # Handle multi-ingredient drugs (e.g., "aspirin + ibuprofen" or "vildagliptin + metformin")
        if "+" in key:
            parts = [p.strip() for p in key.split("+")]
            sub_profiles = [self.get_profile(p) for p in parts if self.get_profile(p)]
            if sub_profiles:
                return ChemicalProfile(
                    generic_name=generic_name.title(),
                    chemical_name=" + ".join(sp.chemical_name for sp in sub_profiles),
                    chemical_class=" + ".join(sp.chemical_class for sp in sub_profiles),
                    pharmacological_class=" + ".join(sp.pharmacological_class for sp in sub_profiles),
                    target_site=" + ".join(sp.target_site for sp in sub_profiles),
                    metabolic_pathway=" + ".join(sp.metabolic_pathway for sp in sub_profiles),
                )

        return self.profiles.get(key)


_global_chemical_engine: Optional[ChemicalEngine] = None


def get_chemical_engine() -> ChemicalEngine:
    global _global_chemical_engine
    if _global_chemical_engine is None:
        _global_chemical_engine = ChemicalEngine()
    return _global_chemical_engine
