"""
Unit tests for Step 4 multi-drug severity risk gauge summary.
Confirms breakdown counts match actual interaction pairs and severity distributions.
"""
from src.interaction.models import EnsembleInteractionResult, InteractionResult, InteractionStatus, OriginType, SeverityLevel
from src.interaction.severity_gauge import compute_severity_breakdown, render_severity_risk_gauge_html


def test_severity_gauge_counts_match_interactions():
    """
    Confirms severity breakdown metrics match exact count and severity distribution
    returned by ensemble interaction screening.
    """
    pair_high = InteractionResult(
        status=InteractionStatus.INTERACTION_FOUND,
        drug_a_label="Ecosprin",
        drug_a_generic="aspirin",
        drug_b_label="Coumadin",
        drug_b_generic="warfarin",
        severity=SeverityLevel.HIGH,
        origin=OriginType.INTRA_PRESCRIPTION,
    )

    pair_mod = InteractionResult(
        status=InteractionStatus.INTERACTION_FOUND,
        drug_a_label="Lipitor",
        drug_a_generic="atorvastatin",
        drug_b_label="Clarithromycin",
        drug_b_generic="clarithromycin",
        severity=SeverityLevel.MODERATE,
        origin=OriginType.CROSS_PRESCRIPTION,
    )

    pair_low = InteractionResult(
        status=InteractionStatus.INTERACTION_FOUND,
        drug_a_label="Antacid",
        drug_a_generic="magnesium hydroxide",
        drug_b_label="Supp",
        drug_b_generic="iron",
        severity=SeverityLevel.LOW,
        origin=OriginType.INTRA_PRESCRIPTION,
    )

    ensemble = EnsembleInteractionResult(
        total_drugs_checked=4,
        interacting_pairs=[pair_high, pair_mod, pair_low],
        no_interaction_pairs=[],
    )

    breakdown = compute_severity_breakdown(ensemble)

    assert breakdown.total_drugs == 4
    assert breakdown.total_interactions == 3
    assert breakdown.high_count == 1
    assert breakdown.moderate_count == 1
    assert breakdown.low_count == 1
    assert breakdown.unknown_count == 0

    assert "4 medications scanned" in breakdown.summary_text
    assert "3 interaction(s) found" in breakdown.summary_text
    assert "1 high-severity" in breakdown.summary_text
    assert "1 moderate-severity" in breakdown.summary_text
    assert "1 low-severity" in breakdown.summary_text

    html = render_severity_risk_gauge_html(breakdown)
    assert "#ef4444" in html  # High risk color
    assert "#f59e0b" in html  # Moderate risk color
    assert "#3b82f6" in html  # Low risk color
    assert "Multi-Drug Risk Summary" in html


def test_severity_gauge_zero_interactions():
    """Confirms gauge summary handles zero interaction case cleanly."""
    ensemble = EnsembleInteractionResult(
        total_drugs_checked=3,
        interacting_pairs=[],
        no_interaction_pairs=[],
    )

    breakdown = compute_severity_breakdown(ensemble)
    assert breakdown.total_drugs == 3
    assert breakdown.total_interactions == 0
    assert breakdown.high_count == 0
    assert "3 medications scanned · 0 interactions found" in breakdown.summary_text

    html = render_severity_risk_gauge_html(breakdown)
    assert "#22c55e" in html  # Green safe bar
