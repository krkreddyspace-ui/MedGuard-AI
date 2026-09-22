"""
MedGuard - Deterministic Explanation Formatter
Transforms structured interaction outcomes into clear, empathetic, non-jargon patient explanations.
Includes chemical composition breakdowns and cross-prescription guidance.
Strictly non-LLM, rule-based, and medically safe.
"""
from dataclasses import dataclass
from typing import Optional

from config.settings import (
    NO_KNOWN_INTERACTION_MSG,
    STANDARD_CONFIRMATION_MSG,
    STANDARD_DISCLAIMER_MSG,
    UNRECOGNIZED_MEDICINE_MSG,
)
from src.chemical.engine import ChemicalProfile, get_chemical_engine
from src.interaction.models import (
    EnsembleInteractionResult,
    InteractionResult,
    InteractionStatus,
    OriginType,
    SeverityLevel,
)


@dataclass
class FormattedExplanation:
    """Structured representation ready for the UI result view."""
    headline: str
    headline_badge_type: str  # "danger", "info", "warning"
    med1_display: str
    med2_display: str
    summary_text: str
    why_it_matters: Optional[str] = None
    mechanism_detail: Optional[str] = None
    recommended_action: str = STANDARD_CONFIRMATION_MSG
    severity_label: Optional[str] = None
    source_attribution: Optional[str] = None
    disclaimer: str = STANDARD_DISCLAIMER_MSG
    suggestions: list[str] = None
    chemical_profile_a: Optional[ChemicalProfile] = None
    chemical_profile_b: Optional[ChemicalProfile] = None
    origin_tag: Optional[str] = None


def format_explanation(result: InteractionResult) -> FormattedExplanation:
    """
    Formats an InteractionResult into structured, patient-accessible copy.
    """
    med1_name = (
        result.drug_a_generic.upper()
        if result.drug_a_generic
        else result.drug_a_label.upper()
    )
    med2_name = (
        result.drug_b_generic.upper()
        if result.drug_b_generic
        else result.drug_b_label.upper()
    )

    chem_engine = get_chemical_engine()
    prof_a = chem_engine.get_profile(result.drug_a_generic)
    prof_b = chem_engine.get_profile(result.drug_b_generic)

    origin_label = (
        "⚠️ Cross-Prescription Alert (Past Active Med vs New Med)"
        if result.origin == OriginType.CROSS_PRESCRIPTION
        else None
    )

    # ---------------------------------------------------------
    # STATE A: POTENTIAL INTERACTION DETECTED
    # ---------------------------------------------------------
    if result.status == InteractionStatus.INTERACTION_FOUND:
        sev_str = result.severity.value.upper() if result.severity else "MODERATE"
        return FormattedExplanation(
            headline="Potential interaction detected",
            headline_badge_type="danger",
            med1_display=med1_name,
            med2_display=med2_name,
            summary_text=(
                "These medicines may affect each other in a way that could increase health risks. "
                "Review the details below and consult your healthcare team."
            ),
            why_it_matters=result.plain_language or "A documented pharmacological interaction exists between these two active ingredients.",
            mechanism_detail=result.mechanism,
            recommended_action=STANDARD_CONFIRMATION_MSG,
            severity_label=f"Severity: {sev_str}",
            source_attribution=result.source or "Local curated prototype dataset",
            disclaimer=STANDARD_DISCLAIMER_MSG,
            chemical_profile_a=prof_a,
            chemical_profile_b=prof_b,
            origin_tag=origin_label,
        )

    # ---------------------------------------------------------
    # STATE B: NO KNOWN INTERACTION IN LOCAL DATASET
    # ---------------------------------------------------------
    if result.status == InteractionStatus.NO_KNOWN_INTERACTION:
        return FormattedExplanation(
            headline="No known interaction found",
            headline_badge_type="info",
            med1_display=med1_name,
            med2_display=med2_name,
            summary_text="No matching interaction was found in MedGuard's local dataset.",
            why_it_matters=(
                "Neither of these medications is cataloged to adversely interact with each other "
                "within our curated prototype database."
            ),
            mechanism_detail=None,
            recommended_action=(
                "Important: This does not rule out every possible interaction. "
                "Always confirm with your pharmacist or doctor if you have doubts or experience new symptoms."
            ),
            severity_label=None,
            source_attribution="Local curated prototype dataset",
            disclaimer=STANDARD_DISCLAIMER_MSG,
            chemical_profile_a=prof_a,
            chemical_profile_b=prof_b,
            origin_tag=origin_label,
        )

    # ---------------------------------------------------------
    # STATE C: MEDICINE NOT RECOGNIZED
    # ---------------------------------------------------------
    unrecognized_names = ", ".join(result.unrecognized_drugs) if result.unrecognized_drugs else "one of the medicines"
    return FormattedExplanation(
        headline="Medicine not recognized",
        headline_badge_type="warning",
        med1_display=result.drug_a_label.upper(),
        med2_display=result.drug_b_label.upper(),
        summary_text=UNRECOGNIZED_MEDICINE_MSG,
        why_it_matters=(
            f"We could not confidently verify the active ingredient for {unrecognized_names}. "
            "Because an unknown medicine cannot be matched, interaction status cannot be determined."
        ),
        mechanism_detail=None,
        recommended_action=(
            "Please try scanning again with clearer packaging, or manually show the physical blister packs "
            "to your pharmacist for verification."
        ),
        severity_label="Status: Unverified Input",
        source_attribution=None,
        disclaimer=STANDARD_DISCLAIMER_MSG,
        suggestions=[
            "Use bright, even lighting on the packaging",
            "Keep the printed generic or brand name clearly in frame",
            "Hold the medicine strip flat to minimize glare from foil",
            "Wipe camera lens if the preview appears blurry",
        ],
        chemical_profile_a=prof_a,
        chemical_profile_b=prof_b,
        origin_tag=origin_label,
    )
