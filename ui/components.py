"""
MedGuard - Modular UI Components
Clean, accessible, and structured components for the laptop prototype.
Includes Chemical Composition rendering and Prescription History views.
Uses st.html for native DOM HTML rendering.
"""
from typing import Optional
import streamlit as st

from config.settings import (
    APP_SUBTITLE,
    APP_TITLE,
    CAMERA_STANDIN_NOTE,
    OFFLINE_BADGE_TEXT,
    STANDARD_DISCLAIMER_MSG,
)
from src.chemical.engine import ChemicalProfile
from src.explanation.formatter import FormattedExplanation
from src.history.prescription_store import PrescriptionRecord, get_prescription_store
from src.interaction.models import EnsembleInteractionResult, InteractionResult, InteractionStatus, OriginType
from src.normalization.normalizer import DrugMatchResult


from src.privacy.network_monitor import get_network_request_count


def render_header():
    """Renders the top hero branding, offline status indicator, and live verified zero-network counter."""
    net_count = get_network_request_count()
    st.html(
        f"""
        <div class="medguard-header">
            <div class="medguard-title">{APP_TITLE}</div>
            <div class="medguard-subtitle">{APP_SUBTITLE}</div>
        </div>
        <div class="status-pill-container">
            <span class="offline-pill">
                <span class="pulse-dot"></span>
                &nbsp;{OFFLINE_BADGE_TEXT}
            </span>
            <span class="offline-pill" style="color: var(--accent); background: rgba(108,99,255,0.06);">
                <span class="pulse-dot" style="background-color: var(--accent); box-shadow: 0 0 0 3px rgba(108,99,255,0.15);"></span>
                &nbsp;<strong>{net_count} network requests this session</strong>
            </span>
        </div>
        """
    )


def render_detected_medicine_card(drug: Optional[DrugMatchResult], label: str):
    """Renders the detected medicine breakdown card with defensible recognition copy."""
    if not drug:
        return

    if drug.recognized:
        brand_line = f"Brand recognized: <strong>{drug.brand_name}</strong> &nbsp;|&nbsp; " if drug.brand_name else ""
        generic_line = f"Generic: <strong>{drug.generic_name.title()}</strong>"
        match_type = "Exact" if drug.confidence >= 99.0 else "Fuzzy / High confidence"
        st.html(
            f"""
            <div class="detected-pill">
                <div class="detected-label">✔ Medicine Identified ({label})</div>
                <div class="detected-name">{drug.generic_name.upper()}</div>
                <div class="detected-meta">
                    {brand_line}{generic_line} &nbsp;|&nbsp; Match type: {match_type}
                </div>
            </div>
            """
        )
    else:
        st.html(
            f"""
            <div class="detected-pill-unrecognized">
                <div class="detected-label" style="color: #b45309;">⚠ Unrecognized Medicine ({label})</div>
                <div class="detected-name" style="color: #4b5563;">{drug.raw_query or "No recognizable text"}</div>
                <div class="detected-meta" style="color: #6b7280;">
                    Could not confidently match to local database (Threshold &ge; 80%).
                </div>
            </div>
            """
        )


def render_captured_review_screen(captured_img, label: str, med_idx: int) -> tuple[bool, bool]:
    """
    Renders the confirmation review screen after capture.
    """
    st.html(
        f"""
        <div style="margin-bottom: 0.8rem;">
            <div style="font-size: 1.15rem; font-weight: 700; color: #0f172a;">Review your scan ({label})</div>
            <div style="font-size: 0.9rem; color: #475569;">Make sure the medicine name or receipt text is clearly visible.</div>
        </div>
        """
    )

    col_img, col_actions = st.columns([1.2, 1])
    with col_img:
        st.image(captured_img, use_container_width=True, caption=f"Captured Image ({label})")

    with col_actions:
        st.html(
            """
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.8rem; margin-bottom: 1rem; font-size: 0.85rem; color: #334155;">
                🔒 <strong>In-Memory Preview</strong><br>
                This frame is held strictly in volatile RAM. OCR will only run after you confirm.
            </div>
            """
        )

        use_photo = st.button(
            "✓ Use Photo",
            key=f"btn_use_photo_{med_idx}",
            type="primary",
            use_container_width=True,
        )

        retake = st.button(
            "↻ Retake",
            key=f"btn_retake_review_{med_idx}",
            type="secondary",
            use_container_width=True,
        )

    return use_photo, retake


def render_captured_medicine_card(
    drug: Optional[DrugMatchResult],
    captured_img,
    label: str,
    med_idx: int,
):
    """
    Displays the captured medicine frame preview along with identification details and Retake button.
    """
    st.markdown(f"##### Captured Medicine ({label})")
    col_img, col_details = st.columns([1, 1.4])

    with col_img:
        display_img = drug.annotated_image if (drug and drug.annotated_image is not None) else captured_img
        if display_img is not None:
            box_badge = " (OCR Bounding Box Overlay)" if (drug and drug.annotated_image is not None) else ""
            st.image(display_img, use_container_width=True, caption=f"Captured {label}{box_badge}")

    with col_details:
        render_detected_medicine_card(drug, label)
        st.write("")
        if st.button(f"🔄 Retake {label}", key=f"btn_retake_{med_idx}", use_container_width=True):
            st.session_state[f"med{med_idx}_drug"] = None
            st.session_state[f"med{med_idx}_img"] = None
            st.rerun()


def render_chemical_breakdown_card(
    prof_a: Optional[ChemicalProfile],
    prof_b: Optional[ChemicalProfile],
):
    """
    Renders detailed chemical composition breakdown for active pharmaceutical ingredients.
    """
    if not prof_a and not prof_b:
        return

    with st.expander("🧬 Chemical Profile & Pharmacological Details", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            if prof_a:
                st.html(
                    f"""
                    <div style="background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 0.9rem; margin-bottom: 0.8rem;">
                        <div style="font-weight: 700; color: #0f172a; font-size: 1.05rem; margin-bottom: 0.4rem;">
                            🔬 {prof_a.generic_name}
                        </div>
                        <div style="font-size: 0.85rem; color: #334155; line-height: 1.5;">
                            <strong>Chemical Name:</strong> {prof_a.chemical_name}<br>
                            <strong>Chemical Class:</strong> {prof_a.chemical_class}<br>
                            <strong>Pharmacological Class:</strong> {prof_a.pharmacological_class}<br>
                            <strong>Target Site / Enzyme:</strong> {prof_a.target_site}<br>
                            <strong>Metabolic Pathway:</strong> {prof_a.metabolic_pathway}
                        </div>
                    </div>
                    """
                )

        with col2:
            if prof_b:
                st.html(
                    f"""
                    <div style="background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 0.9rem; margin-bottom: 0.8rem;">
                        <div style="font-weight: 700; color: #0f172a; font-size: 1.05rem; margin-bottom: 0.4rem;">
                            🔬 {prof_b.generic_name}
                        </div>
                        <div style="font-size: 0.85rem; color: #334155; line-height: 1.5;">
                            <strong>Chemical Name:</strong> {prof_b.chemical_name}<br>
                            <strong>Chemical Class:</strong> {prof_b.chemical_class}<br>
                            <strong>Pharmacological Class:</strong> {prof_b.pharmacological_class}<br>
                            <strong>Target Site / Enzyme:</strong> {prof_b.target_site}<br>
                            <strong>Metabolic Pathway:</strong> {prof_b.metabolic_pathway}
                        </div>
                    </div>
                    """
                )


def render_placement_guidance():
    """Renders expandable guidance on how to position medicine strips and prescriptions."""
    with st.expander("💡 Best Scan: How to position your packaging or prescription sheet"):
        st.markdown(
            """
            - **Single Blister Strip**: Position the printed brand/generic name inside the target box.
            - **Full Prescription Document**: Capture or upload the entire prescription page with good lighting.
            - **Keep Flat**: Avoid reflections or creases on the paper/foil.
            - **Multi-Medicine Parser**: Automatically extracts and normalizes all prescribed medicines on the page.
            """
        )


def render_result_view(explanation: FormattedExplanation, result: InteractionResult):
    """
    Renders the dominant result screen tailored for State A, State B, or State C, including chemical breakdowns.
    Uses st.html for native HTML component rendering.
    """
    origin_html = ""
    if explanation.origin_tag:
        origin_html = f"""
        <div style="background: #fef2f2; border: 1px solid #fca5a5; border-radius: 6px; padding: 0.5rem 0.8rem; margin-bottom: 0.8rem; font-weight: 700; color: #991b1b; font-size: 0.9rem;">
            {explanation.origin_tag}
        </div>
        """

    # -------------------------------------------------------------
    # STATE A: INTERACTION DETECTED
    # -------------------------------------------------------------
    if result.status == InteractionStatus.INTERACTION_FOUND:
        mech_html = (
            f'<div style="margin-top:0.6rem; font-size:0.95rem; color:#475569;"><em>Biochemical Mechanism: {explanation.mechanism_detail}</em></div>'
            if explanation.mechanism_detail
            else ""
        )
        st.html(
            f"""
            <div class="result-card-interaction">
                {origin_html}
                <div class="result-header-interaction">
                    <span>⚠</span> {explanation.headline}
                </div>
                <div class="drugs-pairing-banner">
                    <div class="drugs-pairing-text">{explanation.med1_display} &nbsp;+&nbsp; {explanation.med2_display}</div>
                </div>
                <div class="result-section-title">Why this matters</div>
                <div class="result-section-content">{explanation.why_it_matters}</div>
                {mech_html}
                <div class="result-section-title">Recommended next step</div>
                <div class="recommendation-box">{explanation.recommended_action}</div>
                <div class="meta-footer">
                    <div><strong>{explanation.severity_label}</strong></div>
                    <div>Source: {explanation.source_attribution}</div>
                </div>
                <div class="disclaimer-box">{explanation.disclaimer}</div>
            </div>
            """
        )

        # Chemical Breakdown Section
        render_chemical_breakdown_card(explanation.chemical_profile_a, explanation.chemical_profile_b)

    # -------------------------------------------------------------
    # STATE B: NO KNOWN INTERACTION
    # -------------------------------------------------------------
    elif result.status == InteractionStatus.NO_KNOWN_INTERACTION:
        st.html(
            f"""
            <div class="result-card-no-interaction">
                {origin_html}
                <div class="result-header-no-interaction">
                    <span>ℹ</span> {explanation.headline}
                </div>
                <div class="drugs-pairing-banner">
                    <div class="drugs-pairing-text">{explanation.med1_display} &nbsp;+&nbsp; {explanation.med2_display}</div>
                </div>
                <div class="result-section-title">Result Summary</div>
                <div class="result-section-content">{explanation.summary_text}</div>
                <div class="result-section-title">Important Notice</div>
                <div class="recommendation-box" style="border-left-color: #3b82f6; color: #1e40af;">
                    {explanation.recommended_action}
                </div>
                <div class="meta-footer">
                    <div>Status: Both medicines recognized</div>
                    <div>Source: {explanation.source_attribution}</div>
                </div>
                <div class="disclaimer-box">{explanation.disclaimer}</div>
            </div>
            """
        )

        render_chemical_breakdown_card(explanation.chemical_profile_a, explanation.chemical_profile_b)

    # -------------------------------------------------------------
    # STATE C: DRUG NOT RECOGNIZED
    # -------------------------------------------------------------
    else:
        suggestions_html = ""
        if explanation.suggestions:
            items = "".join(f"<li>{s}</li>" for s in explanation.suggestions)
            suggestions_html = f"<div class='result-section-title'>Photo suggestions</div><ul style='margin-top: 0.4rem; color: #334155; line-height: 1.6;'>{items}</ul>"

        st.html(
            f"""
            <div class="result-card-unrecognized">
                <div class="result-header-unrecognized">
                    <span>❓</span> {explanation.headline}
                </div>
                <div class="drugs-pairing-banner">
                    <div class="drugs-pairing-text">{explanation.med1_display} &nbsp;&amp;&nbsp; {explanation.med2_display}</div>
                </div>
                <div class="result-section-title">Status Explanation</div>
                <div class="result-section-content">{explanation.why_it_matters}</div>
                <div class="result-section-title">Safety Guidance</div>
                <div class="recommendation-box" style="border-left-color: #f59e0b; color: #92400e;">
                    {explanation.recommended_action}
                </div>
                {suggestions_html}
                <div class="meta-footer">
                    <div><strong>{explanation.severity_label}</strong></div>
                    <div>Action: Rescan required</div>
                </div>
                <div class="disclaimer-box">{explanation.disclaimer}</div>
            </div>
            """
        )


def render_ensemble_result_view(ensemble_res: EnsembleInteractionResult):
    """
    Renders multi-medicine interaction screening results grouped by origin type.
    """
    st.markdown("### 📋 Multi-Medicine Interaction Screening Report")

    from src.interaction.severity_gauge import compute_severity_breakdown, render_severity_risk_gauge_html
    breakdown = compute_severity_breakdown(ensemble_res)
    gauge_html = render_severity_risk_gauge_html(breakdown)
    st.html(gauge_html)

    if ensemble_res.has_any_interaction:
        st.error(f"⚠️ Found {len(ensemble_res.interacting_pairs)} potential interaction(s) across checked medications!")

        cross_pairs = [p for p in ensemble_res.interacting_pairs if p.origin == OriginType.CROSS_PRESCRIPTION]
        intra_pairs = [p for p in ensemble_res.interacting_pairs if p.origin != OriginType.CROSS_PRESCRIPTION]

        if cross_pairs:
            st.markdown("#### ⚠️ New interactions with your saved medications")
            for pair_res in cross_pairs:
                from src.explanation.formatter import format_explanation
                expl = format_explanation(pair_res)
                render_result_view(expl, pair_res)
                st.write("")

        if intra_pairs:
            st.markdown("#### ⚠️ Interactions within this scan")
            for pair_res in intra_pairs:
                from src.explanation.formatter import format_explanation
                expl = format_explanation(pair_res)
                render_result_view(expl, pair_res)
                st.write("")
    else:
        st.success(f"✓ Checked {ensemble_res.total_drugs_checked} active medications — No matching interactions found in local dataset.")

    if ensemble_res.no_interaction_pairs and not ensemble_res.has_any_interaction:
        st.markdown("##### Safe / Verified Combinations Checked:")
        for pair_res in ensemble_res.no_interaction_pairs:
            a_label = pair_res.drug_a_generic or pair_res.drug_a_label
            b_label = pair_res.drug_b_generic or pair_res.drug_b_label
            origin_badge = " [Past Active vs New]" if pair_res.origin == OriginType.CROSS_PRESCRIPTION else ""
            st.info(f"• **{a_label.upper()}** + **{b_label.upper()}** — No known interaction{origin_badge}")


def render_history_tab():
    """Renders the persistent prescription history tab."""
    store = get_prescription_store()
    history = store.get_all_prescriptions()

    st.markdown("### 📜 Prescription History & Active Medication Tracker")
    st.caption("Medicines saved here are automatically cross-checked when you scan new prescriptions (even months later).")

    if not history:
        st.info("No saved prescriptions yet. Scan a full prescription or medicine strip and click 'Save to Prescription History'.")
        return

    active_meds = store.get_active_medications()
    if active_meds:
        active_names = ", ".join([f"**{m.generic_name.upper()}**" for m in active_meds if m.generic_name])
        st.html(
            f"""
            <div style="background: #e0f2fe; border: 1px solid #7dd3fc; border-radius: 8px; padding: 0.8rem; margin-bottom: 1rem;">
                🛡️ <strong>Currently Active Medications ({len(active_meds)}):</strong><br>
                {active_names}
            </div>
            """
        )

    view_mode = st.radio(
        "Display Mode",
        ["📊 Regimen Timeline", "📋 List View"],
        horizontal=True,
        key="history_view_mode",
    )

    if view_mode == "📊 Regimen Timeline":
        from src.history.timeline_generator import build_timeline_data, render_timeline_html

        ensemble_res = st.session_state.get("ensemble_result")
        nodes, connections = build_timeline_data(history, ensemble_res)
        timeline_html = render_timeline_html(nodes, connections)
        st.html(timeline_html)
        st.write("")

    st.markdown("#### 📋 Stored Prescription Records")
    for rec in history:
        status_icon = "🟢 Active" if rec.active else "⚪ Archived / Past"
        with st.expander(f"{status_icon} | {rec.title} ({rec.date})"):
            med_list = rec.get_drug_match_results()
            st.markdown(f"**Saved Medicines ({len(med_list)}):**")
            for m in med_list:
                brand_str = f" ({m.brand_name})" if m.brand_name else ""
                st.write(f"• **{m.generic_name.title() if m.generic_name else m.raw_query}**{brand_str}")

            col1, col2 = st.columns(2)
            with col1:
                toggle_btn_label = "Deactivate (Mark as finished)" if rec.active else "Re-activate"
                if st.button(toggle_btn_label, key=f"btn_toggle_{rec.id}"):
                    store.toggle_active(rec.id)
                    st.rerun()
            with col2:
                if st.button("🗑 Delete Record", key=f"btn_del_{rec.id}"):
                    store.delete_prescription(rec.id)
                    st.rerun()


def render_architecture_diagram_html() -> str:
    """
    Renders visual HTML pipeline diagram: Camera -> On-device OCR -> Local Matching -> Explanation,
    labeling each box clearly as 'on-device / offline'.
    """
    return """
    <div style="background:var(--bg,#E0E5EC); border-radius:20px;
                box-shadow:8px 8px 20px rgba(166,180,200,.7),-8px -8px 20px rgba(255,255,255,.85);
                padding:1.5rem; margin:0.8rem 0;">
        <div style="font-size:1rem;font-weight:800;color:var(--text-primary,#3D4852);margin-bottom:.3rem;">
            🏗️ MedGuard On-Device Privacy Architecture
        </div>
        <div style="font-size:.83rem;color:var(--text-secondary,#6B7280);margin-bottom:1.2rem;">
            Zero cloud transmission. Full local pipeline execution in volatile RAM.
        </div>
        <div style="display:flex;align-items:stretch;justify-content:space-between;gap:.7rem;flex-wrap:wrap;">
            <div style="flex:1;min-width:120px;background:var(--bg,#E0E5EC);
                        box-shadow:4px 4px 10px rgba(166,180,200,.6),-4px -4px 10px rgba(255,255,255,.8);
                        border-radius:14px;padding:.9rem;text-align:center;border-top:3px solid #3b82f6;">
                <div style="font-size:1.5rem;margin-bottom:.3rem;">📷</div>
                <div style="font-weight:700;font-size:.85rem;color:var(--text-primary,#3D4852);">Camera</div>
                <div style="font-size:.7rem;color:#3b82f6;margin-top:.4rem;background:rgba(59,130,246,.08);
                            padding:.2rem .5rem;border-radius:20px;font-weight:700;display:inline-block;">🔒 on-device / offline</div>
            </div>
            <div style="display:flex;align-items:center;justify-content:center;font-size:1.1rem;color:var(--accent,#6C63FF);font-weight:bold;">➔</div>
            <div style="flex:1;min-width:120px;background:var(--bg,#E0E5EC);
                        box-shadow:4px 4px 10px rgba(166,180,200,.6),-4px -4px 10px rgba(255,255,255,.8);
                        border-radius:14px;padding:.9rem;text-align:center;border-top:3px solid #6C63FF;">
                <div style="font-size:1.5rem;margin-bottom:.3rem;">🔤</div>
                <div style="font-weight:700;font-size:.85rem;color:var(--text-primary,#3D4852);">On-device OCR</div>
                <div style="font-size:.7rem;color:#6C63FF;margin-top:.4rem;background:rgba(108,99,255,.08);
                            padding:.2rem .5rem;border-radius:20px;font-weight:700;display:inline-block;">🔒 on-device / offline</div>
            </div>
            <div style="display:flex;align-items:center;justify-content:center;font-size:1.1rem;color:var(--accent,#6C63FF);font-weight:bold;">➔</div>
            <div style="flex:1;min-width:120px;background:var(--bg,#E0E5EC);
                        box-shadow:4px 4px 10px rgba(166,180,200,.6),-4px -4px 10px rgba(255,255,255,.8);
                        border-radius:14px;padding:.9rem;text-align:center;border-top:3px solid #38B2AC;">
                <div style="font-size:1.5rem;margin-bottom:.3rem;">🧪</div>
                <div style="font-weight:700;font-size:.85rem;color:var(--text-primary,#3D4852);">Local Matching</div>
                <div style="font-size:.7rem;color:#38B2AC;margin-top:.4rem;background:rgba(56,178,172,.08);
                            padding:.2rem .5rem;border-radius:20px;font-weight:700;display:inline-block;">🔒 on-device / offline</div>
            </div>
            <div style="display:flex;align-items:center;justify-content:center;font-size:1.1rem;color:var(--accent,#6C63FF);font-weight:bold;">➔</div>
            <div style="flex:1;min-width:120px;background:var(--bg,#E0E5EC);
                        box-shadow:4px 4px 10px rgba(166,180,200,.6),-4px -4px 10px rgba(255,255,255,.8);
                        border-radius:14px;padding:.9rem;text-align:center;border-top:3px solid #F59E0B;">
                <div style="font-size:1.5rem;margin-bottom:.3rem;">📄</div>
                <div style="font-weight:700;font-size:.85rem;color:var(--text-primary,#3D4852);">Explanation</div>
                <div style="font-size:.7rem;color:#F59E0B;margin-top:.4rem;background:rgba(245,158,11,.08);
                            padding:.2rem .5rem;border-radius:20px;font-weight:700;display:inline-block;">🔒 on-device / offline</div>
            </div>
        </div>
    </div>
    """


def render_educational_accordions():
    """Renders the collapsible informational sections at the bottom."""
    st.write("")
    with st.expander("🏗️ How MedGuard Works — Live On-Device Architecture Pipeline", expanded=False):
        st.html(render_architecture_diagram_html())

    col1, col2, col3 = st.columns(3)

    with col1:
        with st.expander("🔍 How It Works"):
            st.markdown(
                """
                1. **Scan**: Photograph blister strips or full prescription documents.
                2. **Multi-Medicine Parser**: Local OCR extracts all medicines listed.
                3. **Chemical & Cross-History Check**: Checks molecular mechanisms against current and past active prescriptions.
                4. **Understand**: Read plain-language risk summaries and chemical compound breakdowns.
                """
            )

    with col2:
        with st.expander("🛡 Privacy & Safety"):
            st.markdown(
                """
                - **100% Local & Private**: All OCR and interaction matching run strictly on your device.
                - **Persistent Storage**: History stored locally in `data/prescription_history.json`.
                - **No Diagnostic Claims**: MedGuard is a decision-support screening prototype.
                """
            )

    with col3:
        with st.expander("📚 Dataset & Sources"):
            st.markdown(
                """
                - **Curated Dataset**: Contains 25 verified high-risk pairs, 69 brand mappings, and chemical compositions.
                - **Clinical Provenance**: Cross-referenced with BNF 84, FDA safety alerts, and Stockley's Drug Interactions.
                """
            )
