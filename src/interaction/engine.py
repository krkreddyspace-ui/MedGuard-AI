"""
MedGuard - Deterministic Local Interaction Engine
Evaluates drug pairs strictly locally with order-independent symmetric lookup.
Guarantees distinct outcomes for known interaction, no known interaction, and unrecognized drug.
Supports multi-drug ensemble and cross-prescription interaction screening with severity-descending sorting.
"""
import json
import logging
from pathlib import Path
from typing import Optional, Union

from config.settings import INTERACTIONS_FILE
from src.interaction.models import (
    EnsembleInteractionResult,
    InteractionResult,
    InteractionStatus,
    OriginType,
    SeverityLevel,
)
from src.normalization.normalizer import DrugMatchResult

logger = logging.getLogger(__name__)

SEVERITY_WEIGHTS = {
    SeverityLevel.HIGH: 3,
    SeverityLevel.MODERATE: 2,
    SeverityLevel.LOW: 1,
    SeverityLevel.UNKNOWN: 0,
}


class InteractionEngine:
    """
    Offline, deterministic drug interaction matcher.
    """

    def __init__(self, interactions_file: Path = INTERACTIONS_FILE):
        self.interactions_file = interactions_file
        # Maps tuple(sorted([drug_a, drug_b])) -> dict of interaction details
        self._lookup_table: dict[tuple[str, str], dict] = {}
        self._load_dataset()

    def _load_dataset(self) -> None:
        """Loads interaction records and indexes them symmetrically."""
        if not self.interactions_file.exists():
            logger.warning(f"Interactions file not found at {self.interactions_file}")
            return

        with open(self.interactions_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for record in data:
            drug_a = record["drug_a"].lower().strip()
            drug_b = record["drug_b"].lower().strip()
            key = tuple(sorted([drug_a, drug_b]))
            self._lookup_table[key] = record

    def check_interaction(
        self,
        drug_a_input: Union[DrugMatchResult, str, None],
        drug_b_input: Union[DrugMatchResult, str, None],
        drug_a_label: str = "",
        drug_b_label: str = "",
        origin: OriginType = OriginType.INTRA_PRESCRIPTION,
    ) -> InteractionResult:
        """
        Determines the interaction status between two medicines.

        Rules:
        1. If either medicine is unrecognized or missing -> DRUG_NOT_RECOGNIZED
        2. If both are recognized and pair exists in lookup -> INTERACTION_FOUND
        3. If both are recognized and pair does not exist in lookup -> NO_KNOWN_INTERACTION
        """
        a_generic: Optional[str] = None
        b_generic: Optional[str] = None
        unrecognized: list[str] = []

        # Process Drug A
        if isinstance(drug_a_input, DrugMatchResult):
            if drug_a_input.recognized and drug_a_input.generic_name:
                a_generic = drug_a_input.generic_name.lower().strip()
                if not drug_a_label:
                    drug_a_label = drug_a_input.brand_name or drug_a_input.generic_name.title()
            else:
                unrecognized.append(drug_a_label or drug_a_input.raw_query or "Medicine 1")
        elif isinstance(drug_a_input, str) and drug_a_input.strip():
            a_generic = drug_a_input.lower().strip()
            if not drug_a_label:
                drug_a_label = drug_a_input.title()
        else:
            unrecognized.append(drug_a_label or "Medicine 1")

        # Process Drug B
        if isinstance(drug_b_input, DrugMatchResult):
            if drug_b_input.recognized and drug_b_input.generic_name:
                b_generic = drug_b_input.generic_name.lower().strip()
                if not drug_b_label:
                    drug_b_label = drug_b_input.brand_name or drug_b_input.generic_name.title()
            else:
                unrecognized.append(drug_b_label or drug_b_input.raw_query or "Medicine 2")
        elif isinstance(drug_b_input, str) and drug_b_input.strip():
            b_generic = drug_b_input.lower().strip()
            if not drug_b_label:
                drug_b_label = drug_b_input.title()
        else:
            unrecognized.append(drug_b_label or "Medicine 2")

        # Rule 1: If any drug is unrecognized, return DRUG_NOT_RECOGNIZED
        if unrecognized or not a_generic or not b_generic:
            return InteractionResult(
                status=InteractionStatus.DRUG_NOT_RECOGNIZED,
                drug_a_label=drug_a_label or "Medicine 1",
                drug_b_label=drug_b_label or "Medicine 2",
                drug_a_generic=a_generic,
                drug_b_generic=b_generic,
                unrecognized_drugs=unrecognized,
                origin=origin,
            )

        # Build order-independent lookup key
        pair_key = tuple(sorted([a_generic, b_generic]))

        # Rule 2: Pair exists in lookup table -> INTERACTION_FOUND
        if pair_key in self._lookup_table:
            rec = self._lookup_table[pair_key]
            severity_str = rec.get("severity", "moderate").lower()
            try:
                sev = SeverityLevel(severity_str)
            except ValueError:
                sev = SeverityLevel.MODERATE

            return InteractionResult(
                status=InteractionStatus.INTERACTION_FOUND,
                drug_a_label=drug_a_label,
                drug_b_label=drug_b_label,
                drug_a_generic=a_generic,
                drug_b_generic=b_generic,
                severity=sev,
                mechanism=rec.get("mechanism", ""),
                plain_language=rec.get("plain_language", ""),
                source=rec.get("source", "Local curated prototype dataset"),
                origin=origin,
            )

        # Rule 3: Both recognized but pair not in local dataset -> NO_KNOWN_INTERACTION
        return InteractionResult(
            status=InteractionStatus.NO_KNOWN_INTERACTION,
            drug_a_label=drug_a_label,
            drug_b_label=drug_b_label,
            drug_a_generic=a_generic,
            drug_b_generic=b_generic,
            origin=origin,
        )

    def check_ensemble_interactions(
        self,
        drugs: list[Union[DrugMatchResult, str]],
    ) -> EnsembleInteractionResult:
        """
        Checks all pairwise combinations among a list of recognized drugs,
        sorted in severity-descending order.
        """
        if not drugs or len(drugs) < 2:
            return EnsembleInteractionResult(total_drugs_checked=len(drugs))

        interacting: list[InteractionResult] = []
        no_interaction: list[InteractionResult] = []
        unrecognized: list[str] = []

        seen_pairs: set[tuple[str, str]] = set()

        for i in range(len(drugs)):
            for j in range(i + 1, len(drugs)):
                res = self.check_interaction(drugs[i], drugs[j])

                # De-duplicate pair results
                a_gen = res.drug_a_generic or res.drug_a_label
                b_gen = res.drug_b_generic or res.drug_b_label
                pair_key = tuple(sorted([a_gen.lower(), b_gen.lower()]))

                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                if res.status == InteractionStatus.INTERACTION_FOUND:
                    interacting.append(res)
                elif res.status == InteractionStatus.NO_KNOWN_INTERACTION:
                    no_interaction.append(res)
                elif res.status == InteractionStatus.DRUG_NOT_RECOGNIZED:
                    unrecognized.extend(res.unrecognized_drugs)

        # Sort interacting pairs by severity descending
        interacting.sort(key=lambda x: SEVERITY_WEIGHTS.get(x.severity, 0), reverse=True)

        return EnsembleInteractionResult(
            total_drugs_checked=len(drugs),
            interacting_pairs=interacting,
            no_interaction_pairs=no_interaction,
            unrecognized_drugs=list(set(unrecognized)),
        )

    def check_cross_prescription_interactions(
        self,
        new_drugs: list[Union[DrugMatchResult, str]],
        past_active_drugs: list[Union[DrugMatchResult, str]],
    ) -> EnsembleInteractionResult:
        """
        Checks interactions within new prescription items (INTRA_PRESCRIPTION)
        AND between new prescription items and past active prescription items (CROSS_PRESCRIPTION),
        sorted in severity-descending order.
        """
        interacting: list[InteractionResult] = []
        no_interaction: list[InteractionResult] = []
        unrecognized: list[str] = []
        seen_pairs: set[tuple[str, str]] = set()

        # 1. Intra-prescription checks (among new drugs)
        for i in range(len(new_drugs)):
            for j in range(i + 1, len(new_drugs)):
                res = self.check_interaction(
                    new_drugs[i], new_drugs[j], origin=OriginType.INTRA_PRESCRIPTION
                )
                a_gen = res.drug_a_generic or res.drug_a_label
                b_gen = res.drug_b_generic or res.drug_b_label
                pair_key = tuple(sorted([a_gen.lower(), b_gen.lower()]))
                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    if res.status == InteractionStatus.INTERACTION_FOUND:
                        interacting.append(res)
                    elif res.status == InteractionStatus.NO_KNOWN_INTERACTION:
                        no_interaction.append(res)

        # 2. Cross-prescription checks (new vs past active)
        for new_d in new_drugs:
            for past_d in past_active_drugs:
                res = self.check_interaction(
                    new_d, past_d, origin=OriginType.CROSS_PRESCRIPTION
                )
                a_gen = res.drug_a_generic or res.drug_a_label
                b_gen = res.drug_b_generic or res.drug_b_label
                pair_key = tuple(sorted([a_gen.lower(), b_gen.lower()]))
                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    if res.status == InteractionStatus.INTERACTION_FOUND:
                        interacting.append(res)
                    elif res.status == InteractionStatus.NO_KNOWN_INTERACTION:
                        no_interaction.append(res)

        # Sort interacting pairs by severity descending
        interacting.sort(key=lambda x: SEVERITY_WEIGHTS.get(x.severity, 0), reverse=True)

        total_unique_drugs = len(set(
            [str(d.generic_name if isinstance(d, DrugMatchResult) and d.generic_name else d) for d in new_drugs + past_active_drugs]
        ))

        return EnsembleInteractionResult(
            total_drugs_checked=total_unique_drugs,
            interacting_pairs=interacting,
            no_interaction_pairs=no_interaction,
            unrecognized_drugs=list(set(unrecognized)),
        )


# Singleton instance
_global_interaction_engine: Optional[InteractionEngine] = None


def get_interaction_engine() -> InteractionEngine:
    global _global_interaction_engine
    if _global_interaction_engine is None:
        _global_interaction_engine = InteractionEngine()
    return _global_interaction_engine
