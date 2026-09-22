"""
MedGuard - Regimen History Visual Timeline Generator
Generates clean SVG/HTML horizontal timeline visualizations connecting stored prescriptions
and drawing color-coded interaction arcs between cross-prescription drug pairs.
"""
from dataclasses import dataclass
from typing import Optional

from src.history.prescription_store import PrescriptionRecord
from src.interaction.models import EnsembleInteractionResult, SeverityLevel


@dataclass
class TimelineNode:
    id: str
    title: str
    date: str
    active: bool
    drugs: list[str]
    x_percent: float


@dataclass
class TimelineConnection:
    from_id: str
    to_id: str
    from_x: float
    to_x: float
    drug_a: str
    drug_b: str
    severity: SeverityLevel
    color: str
    severity_label: str


SEVERITY_COLORS = {
    SeverityLevel.HIGH: "#ef4444",
    SeverityLevel.MODERATE: "#f59e0b",
    SeverityLevel.LOW: "#3b82f6",
    SeverityLevel.UNKNOWN: "#64748b",
}


def build_timeline_data(
    records: list[PrescriptionRecord],
    ensemble_res: Optional[EnsembleInteractionResult] = None,
) -> tuple[list[TimelineNode], list[TimelineConnection]]:
    """
    Constructs timeline nodes and cross-prescription interaction connecting arcs.
    """
    if not records:
        return [], []

    # Chronological sort (oldest to newest left-to-right)
    sorted_recs = sorted(records, key=lambda r: r.date)
    n = len(sorted_recs)

    nodes: list[TimelineNode] = []
    rec_x_map: dict[str, float] = {}

    for idx, r in enumerate(sorted_recs):
        x_pct = 15.0 + (idx * (70.0 / max(1, n - 1))) if n > 1 else 50.0
        rec_x_map[r.id] = x_pct
        drug_names = [
            m.get("generic_name", "").title() or m.get("raw_query", "")
            for m in r.medicines
            if m.get("generic_name") or m.get("raw_query")
        ]
        nodes.append(
            TimelineNode(
                id=r.id,
                title=r.title,
                date=r.date,
                active=r.active,
                drugs=drug_names,
                x_percent=x_pct,
            )
        )

    connections: list[TimelineConnection] = []

    if ensemble_res and ensemble_res.interacting_pairs:
        # Map drugs to prescription IDs
        drug_to_rec: dict[str, str] = {}
        for r in sorted_recs:
            for m in r.get_drug_match_results():
                if m.recognized and m.generic_name:
                    drug_to_rec[m.generic_name.lower().strip()] = r.id

        for pair in ensemble_res.interacting_pairs:
            gen_a = pair.drug_a_generic.lower().strip() if pair.drug_a_generic else ""
            gen_b = pair.drug_b_generic.lower().strip() if pair.drug_b_generic else ""

            id_a = drug_to_rec.get(gen_a)
            id_b = drug_to_rec.get(gen_b)

            if id_a and id_b and id_a != id_b:
                x_a = rec_x_map.get(id_a, 50.0)
                x_b = rec_x_map.get(id_b, 50.0)

                sev = pair.severity or SeverityLevel.MODERATE
                color = SEVERITY_COLORS.get(sev, "#f59e0b")
                sev_label = f"{sev.value.capitalize()} Severity"

                connections.append(
                    TimelineConnection(
                        from_id=id_a,
                        to_id=id_b,
                        from_x=min(x_a, x_b),
                        to_x=max(x_a, x_b),
                        drug_a=pair.drug_a_label,
                        drug_b=pair.drug_b_label,
                        severity=sev,
                        color=color,
                        severity_label=sev_label,
                    )
                )

    return nodes, connections


def render_timeline_html(
    nodes: list[TimelineNode],
    connections: list[TimelineConnection],
) -> str:
    """
    Renders horizontal timeline visualization SVG/HTML.
    """
    if not nodes:
        return "<div style='color:#64748b; font-size:0.9rem;'>No stored prescriptions to display on timeline.</div>"

    svg_lines = []
    # Base axis line
    svg_lines.append('<line x1="5%" y1="60" x2="95%" y2="60" stroke="#cbd5e1" stroke-width="4" stroke-dasharray="6,6" />')

    # Draw connecting arcs for cross-prescription interactions
    for conn in connections:
        mid_x = (conn.from_x + conn.to_x) / 2.0
        # Curved arc above line
        svg_lines.append(
            f'<path d="M {conn.from_x}% 60 Q {mid_x}% 10 {conn.to_x}% 60" '
            f'fill="none" stroke="{conn.color}" stroke-width="3" stroke-dasharray="4,2" />'
        )
        svg_lines.append(
            f'<text x="{mid_x}%" y="25" fill="{conn.color}" font-size="11" font-weight="700" text-anchor="middle">'
            f'⚠️ {conn.drug_a} + {conn.drug_b} ({conn.severity_label})</text>'
        )

    # Draw nodes
    node_html_list = []
    for n in nodes:
        dot_color = "#10b981" if n.active else "#94a3b8"
        border_color = "#059669" if n.active else "#64748b"
        status_text = "Active Regimen" if n.active else "Past / Archived"
        drugs_str = ", ".join(n.drugs[:3]) + ("..." if len(n.drugs) > 3 else "")

        svg_lines.append(
            f'<circle cx="{n.x_percent}%" cy="60" r="10" fill="{dot_color}" stroke="{border_color}" stroke-width="3" />'
        )

        node_html_list.append(
            f"""
            <div style="position: absolute; left: {n.x_percent}%; transform: translateX(-50%); top: 80px; width: 160px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 0.6rem; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.05);">
                <div style="font-weight: 700; font-size: 0.88rem; color: #0f172a;">{n.title}</div>
                <div style="font-size: 0.75rem; color: #64748b; margin-bottom: 0.3rem;">{n.date} &nbsp;•&nbsp; <span style="color:{dot_color}; font-weight:600;">{status_text}</span></div>
                <div style="font-size: 0.8rem; color: #334155; font-weight: 600;">{drugs_str}</div>
            </div>
            """
        )

    svg_content = "".join(svg_lines)
    nodes_content = "".join(node_html_list)

    return f"""
    <div style="position: relative; width: 100%; min-height: 240px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem; margin: 1rem 0;">
        <svg width="100%" height="100" style="overflow: visible;">
            {svg_content}
        </svg>
        {nodes_content}
    </div>
    """
