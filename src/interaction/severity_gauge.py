"""
MedGuard - Multi-Drug Severity Risk Gauge Summary Generator
Computes glanceable severity distribution metrics across all identified drug interaction pairs.
"""
from dataclasses import dataclass
from src.interaction.models import EnsembleInteractionResult, SeverityLevel


@dataclass
class SeverityBreakdown:
    total_drugs: int
    total_interactions: int
    high_count: int
    moderate_count: int
    low_count: int
    unknown_count: int
    summary_text: str


def compute_severity_breakdown(ensemble_res: EnsembleInteractionResult) -> SeverityBreakdown:
    """
    Computes exact interaction counts and severity breakdown for multi-drug scan results.
    """
    total_drugs = ensemble_res.total_drugs_checked
    pairs = ensemble_res.interacting_pairs or []
    total_interactions = len(pairs)

    high = sum(1 for p in pairs if p.severity == SeverityLevel.HIGH)
    moderate = sum(1 for p in pairs if p.severity == SeverityLevel.MODERATE)
    low = sum(1 for p in pairs if p.severity == SeverityLevel.LOW)
    unknown = sum(1 for p in pairs if p.severity == SeverityLevel.UNKNOWN or p.severity is None)

    if total_interactions == 0:
        summary_text = f"{total_drugs} medications scanned · 0 interactions found"
    else:
        parts = []
        if high > 0:
            parts.append(f"{high} high-severity")
        if moderate > 0:
            parts.append(f"{moderate} moderate-severity")
        if low > 0:
            parts.append(f"{low} low-severity")
        if unknown > 0:
            parts.append(f"{unknown} unclassified")
        
        breakdown_str = ", ".join(parts) if parts else "1 interaction"
        summary_text = f"{total_drugs} medications scanned · {total_interactions} interaction(s) found ({breakdown_str})"

    return SeverityBreakdown(
        total_drugs=total_drugs,
        total_interactions=total_interactions,
        high_count=high,
        moderate_count=moderate,
        low_count=low,
        unknown_count=unknown,
        summary_text=summary_text,
    )


def render_severity_risk_gauge_html(breakdown: SeverityBreakdown) -> str:
    """
    Renders HTML/CSS stacked bar severity distribution gauge.
    """
    tot = breakdown.total_interactions
    if tot == 0:
        return f"""
        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; padding: 0.9rem 1.1rem; margin-bottom: 1.2rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; font-weight: 700; color: #166534; font-size: 0.95rem;">
                <span>🛡️ Risk Profile Summary</span>
                <span>{breakdown.summary_text}</span>
            </div>
            <div style="height: 12px; border-radius: 6px; background: #22c55e; margin-top: 0.6rem;"></div>
        </div>
        """

    high_pct = (breakdown.high_count / tot) * 100.0
    mod_pct = (breakdown.moderate_count / tot) * 100.0
    low_pct = (breakdown.low_count / tot) * 100.0
    unk_pct = (breakdown.unknown_count / tot) * 100.0

    bars_html = []
    if high_pct > 0:
        bars_html.append(f'<div style="width: {high_pct}%; background: #ef4444;" title="High Risk: {breakdown.high_count}"></div>')
    if mod_pct > 0:
        bars_html.append(f'<div style="width: {mod_pct}%; background: #f59e0b;" title="Moderate Risk: {breakdown.moderate_count}"></div>')
    if low_pct > 0:
        bars_html.append(f'<div style="width: {low_pct}%; background: #3b82f6;" title="Low Risk: {breakdown.low_count}"></div>')
    if unk_pct > 0:
        bars_html.append(f'<div style="width: {unk_pct}%; background: #64748b;" title="Unknown: {breakdown.unknown_count}"></div>')

    bars_rendered = "".join(bars_html)

    return f"""
    <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 1rem; margin-bottom: 1.2rem; box-shadow: 0 1px 4px rgba(0,0,0,0.04);">
        <div style="display: flex; justify-content: space-between; align-items: center; font-weight: 700; color: #0f172a; font-size: 0.95rem; margin-bottom: 0.6rem;">
            <span>📊 Multi-Drug Risk Summary</span>
            <span style="color: #475569; font-weight: 600;">{breakdown.summary_text}</span>
        </div>
        <div style="display: flex; height: 14px; border-radius: 7px; overflow: hidden; background: #e2e8f0; margin-bottom: 0.6rem;">
            {bars_rendered}
        </div>
        <div style="display: flex; gap: 1.2rem; font-size: 0.8rem; color: #475569; font-weight: 600;">
            <span style="color: #ef4444;">● High Risk ({breakdown.high_count})</span>
            <span style="color: #d97706;">● Moderate ({breakdown.moderate_count})</span>
            <span style="color: #2563eb;">● Low ({breakdown.low_count})</span>
        </div>
    </div>
    """
