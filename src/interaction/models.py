"""
MedGuard - Interaction Data Models & Status Enums
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class InteractionStatus(str, Enum):
    """Possible outcomes of the interaction check."""
    INTERACTION_FOUND = "interaction_found"
    NO_KNOWN_INTERACTION = "no_known_interaction"
    DRUG_NOT_RECOGNIZED = "drug_not_recognized"


class SeverityLevel(str, Enum):
    """Clinical interaction severity levels."""
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    UNKNOWN = "unknown"


class OriginType(str, Enum):
    """Source origin of the drug interaction pair."""
    INTRA_PRESCRIPTION = "intra_prescription"   # Interaction between drugs in current prescription
    CROSS_PRESCRIPTION = "cross_prescription"   # Interaction with past active prescription


@dataclass
class InteractionResult:
    """
    Structured outcome of the interaction screening engine for a single drug pair.
    """
    status: InteractionStatus
    drug_a_label: str
    drug_b_label: str
    drug_a_generic: Optional[str] = None
    drug_b_generic: Optional[str] = None
    severity: Optional[SeverityLevel] = None
    mechanism: Optional[str] = None
    plain_language: Optional[str] = None
    source: Optional[str] = None
    unrecognized_drugs: list[str] = field(default_factory=list)
    origin: OriginType = OriginType.INTRA_PRESCRIPTION

    @property
    def has_interaction(self) -> bool:
        return self.status == InteractionStatus.INTERACTION_FOUND

    @property
    def is_recognized(self) -> bool:
        return self.status != InteractionStatus.DRUG_NOT_RECOGNIZED


@dataclass
class EnsembleInteractionResult:
    """
    Structured outcome of checking multiple medicines (full prescription or cross-prescription).
    """
    total_drugs_checked: int
    interacting_pairs: list[InteractionResult] = field(default_factory=list)
    no_interaction_pairs: list[InteractionResult] = field(default_factory=list)
    unrecognized_drugs: list[str] = field(default_factory=list)

    @property
    def has_any_interaction(self) -> bool:
        return len(self.interacting_pairs) > 0

    @property
    def max_severity(self) -> Optional[SeverityLevel]:
        if not self.interacting_pairs:
            return None
        severities = [p.severity for p in self.interacting_pairs if p.severity]
        if SeverityLevel.HIGH in severities:
            return SeverityLevel.HIGH
        if SeverityLevel.MODERATE in severities:
            return SeverityLevel.MODERATE
        if SeverityLevel.LOW in severities:
            return SeverityLevel.LOW
        return SeverityLevel.UNKNOWN
