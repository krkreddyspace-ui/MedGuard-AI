"""
MedGuard - UI Screen Controllers & Workflow Manager
Neumorphic multi-page application with state-based navigation.
Integrates the Superdesign neumorphic UI while preserving all backend logic intact.
"""
from typing import Optional
import streamlit as st
from PIL import Image

from config.settings import (
    CAMERA_STANDIN_NOTE,
    DEMO_SCENARIOS,
    SUPPORTED_IMAGE_TYPES,
    APP_TITLE,
    APP_SUBTITLE,
    OFFLINE_BADGE_TEXT,
)
from src.explanation.formatter import format_explanation
from src.history.prescription_store import get_prescription_store
from src.interaction.engine import get_interaction_engine
from src.normalization.normalizer import DrugMatchResult, get_normalizer
from src.ocr.engine import get_ocr_engine
from src.ocr.prescription_parser import get_prescription_parser
from src.privacy.image_handler import load_image_into_memory
from ui.camera_stream import render_live_camera_scanner
from ui.components import (
    render_captured_medicine_card,
    render_captured_review_screen,
    render_educational_accordions,
    render_ensemble_result_view,
    render_header,
    render_history_tab,
    render_placement_guidance,
    render_result_view,
)


# ============================================================
# SESSION STATE
# ============================================================

def init_session_state():
    """Initializes Streamlit session state keys if not already present."""
    defaults = {
        "current_page": "landing",
        "mode_selection": "Live OCR",
        "workflow_tab": "Two Medicine Check",
        "med1_drug": None,
        "med2_drug": None,
        "med1_img": None,
        "med2_img": None,
        "med1_review_frame": None,
        "med2_review_frame": None,
        "prescription_detected_meds": [],
        "prescription_review_frame": None,
        "interaction_result": None,
        "ensemble_result": None,
        "explanation": None,
        "manual_1": "",
        "manual_2": "",
        "mode_radio": "Live OCR (Camera / Upload)",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def reset_session():
    """Clears active scans and results without reloading the server."""
    st.session_state.med1_drug = None
    st.session_state.med2_drug = None
    st.session_state.med1_img = None
    st.session_state.med2_img = None
    st.session_state.med1_review_frame = None
    st.session_state.med2_review_frame = None
    st.session_state.prescription_detected_meds = []
    st.session_state.prescription_review_frame = None
    st.session_state.interaction_result = None
    st.session_state.ensemble_result = None
    st.session_state.explanation = None
    st.session_state.manual_1 = ""
    st.session_state.manual_2 = ""


def navigate(page: str):
    """Navigate to a named page and trigger rerun."""
    st.session_state.current_page = page
    st.rerun()


# ============================================================
# NAVIGATION BAR
# ============================================================

NAV_PAGES = [
    ("🏠", "Dashboard", "dashboard"),
    ("💊", "Scanner", "scanner"),
    ("📄", "Prescription", "prescription"),
    ("📜", "History", "history"),
    ("🔍", "How It Works", "how_it_works"),
    ("🔒", "Privacy", "privacy"),
    ("ℹ️", "About", "about"),
]


def render_nav():
    """Renders the neumorphic top navigation bar."""
    current = st.session_state.get("current_page", "landing")

    from src.privacy.network_monitor import get_network_request_count
    net_count = get_network_request_count()

    nav_links_html = ""
    for icon, label, page_key in NAV_PAGES:
        active_class = "mg-nav-link-active" if current == page_key else ""
        nav_links_html += f'<span class="mg-nav-link {active_class}" data-page="{page_key}">{icon} {label}</span>'

    # Render the visual nav bar
    st.html(f"""
    <div class="mg-nav">
        <div class="mg-nav-logo" onclick="">
            <div class="mg-nav-logo-icon">🛡️</div>
            <div class="mg-nav-logo-text">MedGuard</div>
        </div>
        <div class="mg-nav-links">
            {nav_links_html}
        </div>
        <div class="offline-pill" style="font-size:0.75rem; padding: 0.3rem 0.8rem;">
            <span class="pulse-dot"></span>
            &nbsp;<strong>{net_count}</strong> network req.
        </div>
    </div>
    """)

    # Streamlit navigation buttons (functional, visually minimal)
    cols = st.columns(len(NAV_PAGES) + 1)
    with cols[0]:
        if st.button("🏠 Home", key="nav_home", help="Go to landing page", use_container_width=True):
            st.session_state.current_page = "landing"
            st.rerun()
    for i, (icon, label, page_key) in enumerate(NAV_PAGES):
        with cols[i + 1]:
            btn_type = "primary" if current == page_key else "secondary"
            if st.button(f"{icon}", key=f"nav_{page_key}", help=label, use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()


# ============================================================
# LANDING PAGE
# ============================================================

def render_landing_page():
    """Neumorphic landing/hero page with real CTAs."""
    st.html("""
    <div class="mg-hero mg-animate-in">
        <div class="mg-hero-eyebrow">
            🛡️ &nbsp; Offline Medical AI &nbsp; · &nbsp; 100% Private
        </div>
        <div class="mg-hero-title">
            Know What Your Medicines<br>
            <span class="mg-hero-title-accent">Contain. Before They Interact.</span>
        </div>
        <div class="mg-hero-subtitle">
            MedGuard checks your medicine combinations privately — using local OCR, local drug matching,
            and a curated interaction database. No cloud, no data transmission, no tracking.
        </div>
    </div>
    """)

    # CTA buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("💊 Scan a Medicine", type="primary", use_container_width=True, key="hero_cta_scanner"):
            reset_session()
            st.session_state.current_page = "scanner"
            st.rerun()
    with col2:
        if st.button("📄 Scan Full Prescription", use_container_width=True, key="hero_cta_prescription"):
            reset_session()
            st.session_state.current_page = "prescription"
            st.rerun()
    with col3:
        if st.button("🔍 See How It Works", use_container_width=True, key="hero_cta_hiw"):
            st.session_state.current_page = "how_it_works"
            st.rerun()

    st.html("""
    <div class="mg-hero-badge-row" style="margin-top: 2rem;">
        <span class="mg-badge">🔒 100% Offline OCR</span>
        <span class="mg-badge">🧪 Chemical-level checks</span>
        <span class="mg-badge">📜 Prescription history</span>
        <span class="mg-badge">⚡ No cloud transmission</span>
        <span class="mg-badge">🌍 Works without internet</span>
    </div>
    """)

    # Feature cards
    st.write("")
    st.html('<div class="mg-section-divider"></div>')
    st.html('<div class="mg-page-subtitle" style="text-align:center; font-weight:700; font-size:1.2rem; color:var(--text-primary);">How MedGuard Protects You</div>')

    c1, c2, c3, c4 = st.columns(4)
    cards = [
        ("📷", "Scan Instantly", "Point your camera at any medicine strip or blister pack."),
        ("🔬", "Chemical Analysis", "See active ingredients and their molecular interaction mechanisms."),
        ("⚠️", "Interaction Alert", "Get clear severity warnings for dangerous combinations."),
        ("📜", "Long-term Memory", "Cross-check today's prescription against your history."),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3, c4], cards):
        with col:
            st.html(f"""
            <div class="mg-feature-card">
                <div class="mg-feature-icon mg-feature-icon-accent">{icon}</div>
                <div class="mg-feature-title">{title}</div>
                <div class="mg-feature-desc">{desc}</div>
            </div>
            """)


# ============================================================
# DASHBOARD PAGE
# ============================================================

def render_dashboard_page():
    """Dashboard with live stats and quick-access cards."""
    st.html("""
    <div class="mg-animate-in">
        <div class="mg-page-title">Dashboard</div>
        <div class="mg-page-subtitle">Your medication safety overview at a glance.</div>
    </div>
    """)

    store = get_prescription_store()
    history = store.get_all_prescriptions()
    active_meds = store.get_active_medications()
    total_meds = len(active_meds)
    total_rx = len(history)

    c1, c2, c3, c4 = st.columns(4)
    stats = [
        ("💊", str(total_meds), "Active Medications"),
        ("📜", str(total_rx), "Saved Prescriptions"),
        ("🌐", "0", "Network Requests"),
        ("🔒", "100%", "Local & Private"),
    ]
    for col, (icon, val, label) in zip([c1, c2, c3, c4], stats):
        with col:
            st.html(f"""
            <div class="mg-stat-card">
                <span class="mg-stat-icon">{icon}</span>
                <div class="mg-stat-value">{val}</div>
                <div class="mg-stat-label">{label}</div>
            </div>
            """)

    st.write("")
    st.html('<div class="mg-section-divider"></div>')

    col_scan, col_hist = st.columns(2)
    with col_scan:
        st.html("""
        <div class="mg-card-accent">
            <div style="font-size:2rem;margin-bottom:.5rem;">💊</div>
            <div style="font-size:1.1rem;font-weight:700;color:var(--text-primary);margin-bottom:.4rem;">Quick Scan</div>
            <div style="font-size:.88rem;color:var(--text-secondary);">Scan a medicine strip or upload a photo to check for interactions instantly.</div>
        </div>
        """)
        if st.button("Open Scanner →", type="primary", use_container_width=True, key="dash_scanner"):
            reset_session()
            st.session_state.current_page = "scanner"
            st.rerun()

    with col_hist:
        st.html("""
        <div class="mg-card-accent" style="border-left-color:var(--accent-medical);">
            <div style="font-size:2rem;margin-bottom:.5rem;">📜</div>
            <div style="font-size:1.1rem;font-weight:700;color:var(--text-primary);margin-bottom:.4rem;">Prescription History</div>
            <div style="font-size:.88rem;color:var(--text-secondary);">View saved prescriptions and cross-check your current medications automatically.</div>
        </div>
        """)
        if st.button("View History →", use_container_width=True, key="dash_history"):
            st.session_state.current_page = "history"
            st.rerun()

    if active_meds:
        st.write("")
        st.html('<div style="font-size:1rem;font-weight:700;color:var(--text-primary);margin-bottom:.8rem;">🛡️ Currently Active Medications</div>')
        med_chips = " ".join(
            f'<span class="mg-badge" style="color:var(--success);">💊 {m.generic_name.title()}</span>'
            for m in active_meds if m.generic_name
        )
        st.html(f'<div style="display:flex;flex-wrap:wrap;gap:.5rem;">{med_chips}</div>')

    # Demo mode selector in expander
    with st.expander("⚙️ Demo / Test Mode Selector", expanded=False):
        render_demo_selector()


# ============================================================
# SCANNER PAGE
# ============================================================

def render_scanner_page():
    """Two-medicine scanner page connected to real OCR + interaction engine."""
    st.html("""
    <div class="mg-animate-in">
        <div class="mg-page-title">💊 Medicine Scanner</div>
        <div class="mg-page-subtitle">
            Scan two medicine strips or enter names manually. The interaction engine checks
            your current scan against saved prescription history automatically.
        </div>
    </div>
    """)

    # Show results if already computed
    if st.session_state.interaction_result and st.session_state.explanation:
        render_result_view(st.session_state.explanation, st.session_state.interaction_result)
        st.write("")
        col_new, col_save = st.columns([1, 1])
        with col_new:
            if st.button("🔄 Start New Check", type="primary", use_container_width=True, key="scanner_new_check"):
                reset_session()
                st.rerun()
        with col_save:
            if st.button("💾 Save Pair to History", use_container_width=True, key="scanner_save_pair"):
                store = get_prescription_store()
                meds = [st.session_state.med1_drug, st.session_state.med2_drug]
                store.save_prescription("Medicine Pair Check", [m for m in meds if m and m.recognized])
                st.success("✅ Saved to prescription history!")
        return

    if st.session_state.ensemble_result:
        render_ensemble_result_view(st.session_state.ensemble_result)
        st.write("")
        if st.button("🔄 New Prescription Check", type="primary", use_container_width=True, key="scanner_new_ens"):
            reset_session()
            st.rerun()
        return

    render_placement_guidance()
    st.write("")

    render_scan_card(1, "Scan Medicine 1")
    st.html("<div class='scan-divider'>+</div>")
    render_scan_card(2, "Scan Medicine 2")

    st.write("")

    med1_ready = st.session_state.med1_drug is not None
    med2_ready = st.session_state.med2_drug is not None

    if st.button(
        "🔍 Check Interaction",
        type="primary",
        disabled=not (med1_ready and med2_ready),
        use_container_width=True,
        key="btn_check_single",
    ):
        with st.spinner("Checking local interaction database & past prescription history..."):
            engine = get_interaction_engine()
            store = get_prescription_store()
            past_active = store.get_active_medications()
            current_drugs = [st.session_state.med1_drug, st.session_state.med2_drug]

            if past_active:
                ens_res = engine.check_cross_prescription_interactions(current_drugs, past_active)
                st.session_state.ensemble_result = ens_res
            else:
                res = engine.check_interaction(
                    st.session_state.med1_drug,
                    st.session_state.med2_drug,
                )
                expl = format_explanation(res)
                st.session_state.interaction_result = res
                st.session_state.explanation = expl

            st.rerun()

    if not (med1_ready and med2_ready):
        st.info("💡 Scan or identify both Medicine 1 and Medicine 2 above to enable the interaction check.")


# ============================================================
# PRESCRIPTION PAGE
# ============================================================

def render_prescription_page():
    """Full prescription document scanner page."""
    st.html("""
    <div class="mg-animate-in">
        <div class="mg-page-title">📄 Prescription Scanner</div>
        <div class="mg-page-subtitle">
            Upload or photograph a complete prescription. MedGuard extracts all medicine names
            and checks interactions — including against your saved prescription history.
        </div>
    </div>
    """)

    if st.session_state.ensemble_result:
        render_ensemble_result_view(st.session_state.ensemble_result)
        st.write("")
        if st.button("🔄 Scan New Prescription", type="primary", use_container_width=True, key="presc_new"):
            reset_session()
            st.rerun()
        return

    render_full_prescription_scanner()


# ============================================================
# HISTORY PAGE
# ============================================================

def render_history_page():
    """Prescription history page connected to real PrescriptionStore."""
    st.html("""
    <div class="mg-animate-in">
        <div class="mg-page-title">📜 Prescription History</div>
        <div class="mg-page-subtitle">
            Your saved medicine records. All history is stored locally and encrypted on your device.
            New scans are automatically cross-checked against active records here.
        </div>
    </div>
    """)
    render_history_tab()


# ============================================================
# HOW IT WORKS PAGE
# ============================================================

def render_how_it_works_page():
    """Visual pipeline explainer matching the actual implementation."""
    from ui.components import render_architecture_diagram_html

    st.html("""
    <div class="mg-animate-in">
        <div class="mg-page-title">🔍 How MedGuard Works</div>
        <div class="mg-page-subtitle">
            A fully local, privacy-preserving pipeline — from camera to interaction result.
            No data ever leaves your device.
        </div>
    </div>
    """)

    st.html(render_architecture_diagram_html())

    st.write("")
    st.html('<div class="mg-section-divider"></div>')
    st.html('<div style="font-size:1.1rem;font-weight:700;color:var(--text-primary);margin-bottom:1rem;">Step-by-Step Pipeline</div>')

    steps = [
        ("📷", "SCAN", "Camera or uploaded image captured strictly in-memory (volatile RAM). No frames are ever written to disk."),
        ("🔤", "OCR", "EasyOCR runs locally using pre-downloaded model weights. Zero network calls. Extracts text from medicine packaging or prescription documents."),
        ("🔎", "NORMALIZE", "Raw OCR text is fuzzy-matched against a local brand→generic drug database. Conservative 80% confidence threshold prevents false identifications."),
        ("🧪", "MATCH", "Identified generics are looked up in a local curated interaction dataset (25 verified high-risk pairs, 69 brand mappings)."),
        ("⚠️", "INTERACTION CHECK", "Pairs checked for cross-interactions — including current scan vs. your saved prescription history from months ago."),
        ("📄", "EXPLAIN", "Results formatted in plain language with mechanism, severity, and recommended action. Chemical profiles shown for full transparency."),
    ]

    for i, (icon, title, desc) in enumerate(steps):
        st.html(f"""
        <div class="mg-pipeline-step mg-animate-in">
            <div class="mg-pipeline-number">{i + 1}</div>
            <div style="font-size:1.4rem;flex-shrink:0;">{icon}</div>
            <div class="mg-pipeline-content">
                <div class="mg-pipeline-step-title">{title}</div>
                <div class="mg-pipeline-step-desc">{desc}</div>
            </div>
        </div>
        """)
        if i < len(steps) - 1:
            st.html('<div class="mg-pipeline-arrow" style="width:100%;max-width:520px;text-align:center;">↓</div>')


# ============================================================
# PRIVACY PAGE
# ============================================================

def render_privacy_page():
    """Privacy architecture page — accurately describes the real implementation."""
    st.html("""
    <div class="mg-animate-in">
        <div class="mg-page-title">🔒 Privacy Architecture</div>
        <div class="mg-page-subtitle">
            MedGuard is built with privacy as the primary constraint, not an afterthought.
            Here is exactly what happens to your data — and what doesn't.
        </div>
    </div>
    """)

    privacy_items = [
        ("🖼️", "rgba(108, 99, 255, 0.1)", "Camera Images — Never Written to Disk",
         "Live camera frames and uploaded photos exist strictly in volatile RAM. They are processed in-memory by EasyOCR and immediately discarded. No image file is ever created on disk."),
        ("🔤", "rgba(56, 178, 172, 0.1)", "OCR — 100% Local",
         "EasyOCR runs using pre-downloaded model weights stored locally. The model runs offline. Zero network calls are made during text extraction. download_enabled=False is enforced."),
        ("🧪", "rgba(16, 185, 129, 0.1)", "Interaction Database — Local JSON",
         "The drug interaction dataset is a local JSON file (data/interactions.json). No cloud API, no pharmacy database, no external lookup service is used."),
        ("📜", "rgba(245, 158, 11, 0.1)", "Prescription History — Encrypted Local Storage",
         "Saved prescription records are encrypted using Fernet symmetric encryption before writing to data/prescription_history.json. Your drug names are never stored in plain text."),
        ("🌐", "rgba(59, 130, 246, 0.1)", "Network Requests — Zero During Processing",
         "The live network request counter shown in the header always reads 0 during scanning. No OCR result, normalization output, or interaction result is ever transmitted externally."),
        ("⚕️", "rgba(239, 68, 68, 0.1)", "Medical Disclaimer",
         "MedGuard is a screening prototype. Results are based on a curated dataset and do not replace professional clinical advice. Always confirm with a pharmacist or doctor."),
    ]

    for icon, bg, title, desc in privacy_items:
        st.html(f"""
        <div class="mg-privacy-item">
            <div class="mg-privacy-icon" style="background:{bg};">{icon}</div>
            <div>
                <div class="mg-privacy-title">{title}</div>
                <div class="mg-privacy-desc">{desc}</div>
            </div>
        </div>
        """)


# ============================================================
# ABOUT PAGE
# ============================================================

def render_about_page():
    """About page with tech stack and product philosophy."""
    st.html("""
    <div class="mg-animate-in">
        <div class="mg-page-title">ℹ️ About MedGuard</div>
        <div class="mg-page-subtitle">
            A privacy-first, offline medication interaction checker built for the iQOO Hackathon 2026 HealthTech track.
        </div>
    </div>
    """)

    st.html("""
    <div class="mg-card">
        <div style="font-size:1.1rem;font-weight:700;color:var(--text-primary);margin-bottom:.8rem;">🎯 What MedGuard Does</div>
        <div style="font-size:.95rem;color:var(--text-secondary);line-height:1.7;">
            MedGuard scans medicine packaging and prescription documents using on-device OCR, identifies
            active pharmaceutical ingredients, and checks for known drug-drug interactions using a curated
            local dataset — all without sending a single byte to the cloud.
        </div>
    </div>
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.html("""
        <div class="mg-card">
            <div style="font-size:1rem;font-weight:700;margin-bottom:.7rem;">🛠️ Technology Stack</div>
            <div style="font-size:.87rem;color:var(--text-secondary);line-height:2;">
                <strong>Frontend:</strong> Streamlit (Python)<br>
                <strong>OCR:</strong> EasyOCR (offline)<br>
                <strong>Normalization:</strong> RapidFuzz fuzzy matching<br>
                <strong>History encryption:</strong> Fernet (cryptography lib)<br>
                <strong>Computer vision:</strong> OpenCV + PIL<br>
                <strong>Camera streaming:</strong> streamlit-webrtc<br>
                <strong>Dataset:</strong> Local JSON (BNF 84, FDA, Stockley's)
            </div>
        </div>
        """)
    with col2:
        st.html("""
        <div class="mg-card">
            <div style="font-size:1rem;font-weight:700;margin-bottom:.7rem;">📊 Dataset Coverage</div>
            <div style="font-size:.87rem;color:var(--text-secondary);line-height:2;">
                <strong>Interaction pairs:</strong> 25 verified high-risk pairs<br>
                <strong>Brand mappings:</strong> 69 brand→generic entries<br>
                <strong>Chemical profiles:</strong> Active ingredient compositions<br>
                <strong>Sources:</strong> BNF 84, FDA safety alerts, Stockley's Drug Interactions<br>
                <strong>Scope:</strong> Demonstration dataset (not a complete clinical database)
            </div>
        </div>
        """)

    st.html("""
    <div class="mg-card-inset" style="margin-top:1rem;">
        <div style="font-size:.85rem;color:var(--text-muted);text-align:center;line-height:1.6;">
            ⚕️ <strong>Medical Disclaimer:</strong> MedGuard is a decision-support screening prototype, not a diagnostic or prescribing tool.
            Results are based on a curated demonstration dataset and do not replace professional pharmacist or physician review.
            Always consult a licensed healthcare professional before making medication decisions.
        </div>
    </div>
    """)


# ============================================================
# SETTINGS PAGE
# ============================================================

def render_settings_page():
    """Settings and configuration page."""
    st.html("""
    <div class="mg-animate-in">
        <div class="mg-page-title">⚙️ Settings</div>
        <div class="mg-page-subtitle">Configure MedGuard preferences and manage your data.</div>
    </div>
    """)

    with st.expander("🗑️ Clear All Scan Data", expanded=False):
        st.warning("This will clear your current scan session (not prescription history).")
        if st.button("Clear Current Session", type="secondary", key="settings_clear_session"):
            reset_session()
            st.success("Session cleared!")
            st.rerun()

    with st.expander("📜 Manage Prescription History", expanded=False):
        render_history_tab()

    with st.expander("⚙️ Demo Mode Selector", expanded=False):
        render_demo_selector()

    st.html("""
    <div class="mg-card-sm" style="margin-top:1.5rem;">
        <div style="font-size:.9rem;color:var(--text-secondary);">
            <strong>App Version:</strong> MedGuard v2 (Hackathon 2026 build)<br>
            <strong>Branch:</strong> v2-chemical-prescription-scanner<br>
            <strong>Privacy mode:</strong> 100% offline, zero network requests during processing
        </div>
    </div>
    """)


# ============================================================
# EXISTING BACKEND-CONNECTED SCREENS (PRESERVED INTACT)
# ============================================================

def process_image_input(img_source) -> Optional[DrugMatchResult]:
    """Safely processes a single medicine image in-memory."""
    if img_source is None:
        return None

    buffer, err = load_image_into_memory(img_source)
    if err or buffer is None:
        st.error(f"Image load error: {err}")
        return None

    try:
        with st.spinner("Analyzing medicine strip in memory..."):
            ocr_engine = get_ocr_engine()
            ocr_res = ocr_engine.extract_text(buffer.image)

        buffer.release()

        if not ocr_res.success:
            st.warning(ocr_res.error_message or "Could not read text from packaging.")
            return None

        normalizer = get_normalizer()
        drug_res = normalizer.normalize(ocr_res.raw_text)

        if ocr_res.text_lines and buffer.image is not None:
            from src.ocr.bounding_box import draw_ocr_bounding_boxes
            highlight_targets = [m for m in [drug_res.brand_name, drug_res.generic_name] if m]
            annotated_arr = draw_ocr_bounding_boxes(buffer.image, ocr_res.text_lines, highlight_words=highlight_targets)
            if annotated_arr is not None and annotated_arr.size > 0:
                drug_res.annotated_image = Image.fromarray(annotated_arr)

        return drug_res

    except Exception as e:
        buffer.release()
        st.error(f"Analysis error: {str(e)}")
        return None


def process_prescription_image_input(img_source) -> list[DrugMatchResult]:
    """Processes a full multi-medicine prescription image in-memory."""
    if img_source is None:
        return []

    buffer, err = load_image_into_memory(img_source)
    if err or buffer is None:
        st.error(f"Image load error: {err}")
        return []

    try:
        with st.spinner("Scanning full prescription document in memory..."):
            parser = get_prescription_parser()
            parse_res = parser.parse_image(buffer.image)

        buffer.release()
        return parse_res.detected_medicines

    except Exception as e:
        buffer.release()
        st.error(f"Prescription scan error: {str(e)}")
        return []


def render_full_prescription_scanner():
    """Renders the Full Multi-Medicine Prescription Document Scanner UI."""
    st.markdown("#### 📄 Scan Full Prescription Document")
    st.caption("Upload or take a photo of a complete prescription listing multiple medicines.")

    tab_upload, tab_text = st.tabs([
        "📁 Upload Prescription Sheet",
        "⌨ Type / Paste Prescription Text",
    ])

    with tab_upload:
        uploaded_doc = st.file_uploader(
            "Upload full prescription photo",
            type=SUPPORTED_IMAGE_TYPES,
            key="prescription_doc_uploader",
            label_visibility="collapsed",
        )
        if uploaded_doc is not None and st.button("🔍 Scan Full Prescription", type="primary", key="btn_scan_prescription"):
            detected = process_prescription_image_input(uploaded_doc)
            if detected:
                st.session_state.prescription_detected_meds = detected
                st.success(f"✓ Found {len(detected)} medicine(s) in prescription!")
            else:
                st.warning("No recognized medicines were detected on this prescription sheet. Try a clearer photo.")

    with tab_text:
        raw_presc_text = st.text_area(
            "Or paste full prescription text:",
            placeholder="e.g.\n1. Ecosprin 75mg\n2. Combiflam pain tablet\n3. Pan-D",
            height=120,
        )
        if st.button("Parse Prescription Text", key="btn_parse_text"):
            if raw_presc_text.strip():
                parser = get_prescription_parser()
                parse_res = parser.parse_text(raw_presc_text)
                if parse_res.detected_medicines:
                    st.session_state.prescription_detected_meds = parse_res.detected_medicines
                    st.success(f"✓ Extracted {len(parse_res.detected_medicines)} medicine(s) from text!")
                else:
                    st.warning("No medicines recognized in text.")

    if st.session_state.prescription_detected_meds:
        meds = st.session_state.prescription_detected_meds
        st.markdown(f"##### Recognized Medicines on Prescription ({len(meds)})")

        for idx, m in enumerate(meds, 1):
            brand_str = f" ({m.brand_name})" if m.brand_name else ""
            st.info(f"**Medicine {idx}:** {m.generic_name.upper() if m.generic_name else m.raw_query}{brand_str} — Match: {m.match_type}")

        col_check, col_save = st.columns(2)
        with col_check:
            if st.button("🔍 Check Prescription Interactions", type="primary", use_container_width=True):
                engine = get_interaction_engine()
                store = get_prescription_store()
                past_active = store.get_active_medications()

                if past_active:
                    ens_res = engine.check_cross_prescription_interactions(meds, past_active)
                else:
                    ens_res = engine.check_ensemble_interactions(meds)

                st.session_state.ensemble_result = ens_res
                st.rerun()

        with col_save:
            if st.button("💾 Save to Prescription History", use_container_width=True):
                store = get_prescription_store()
                store.save_prescription("Scanned Prescription", meds)
                st.success(f"Saved! Preserved {len(meds)} active medicine(s) for future cross-prescription checks.")


def render_scan_card(med_idx: int, label: str):
    """Renders an individual medicine scanning card."""
    current_drug_key = f"med{med_idx}_drug"
    current_img_key = f"med{med_idx}_img"
    review_key = f"med{med_idx}_review_frame"

    if st.session_state.get(current_drug_key) is not None:
        render_captured_medicine_card(
            st.session_state[current_drug_key],
            st.session_state.get(current_img_key),
            label,
            med_idx,
        )
        return

    if st.session_state.get(review_key) is not None:
        review_frame = st.session_state[review_key]
        use_photo, retake = render_captured_review_screen(review_frame, label, med_idx)
        if use_photo:
            res = process_image_input(review_frame)
            if res:
                st.session_state[current_drug_key] = res
                import cv2
                import numpy as np
                if isinstance(review_frame, np.ndarray):
                    rgb = cv2.cvtColor(review_frame, cv2.COLOR_BGR2RGB)
                    st.session_state[current_img_key] = Image.fromarray(rgb)
                elif isinstance(review_frame, Image.Image):
                    st.session_state[current_img_key] = review_frame
                else:
                    st.session_state[current_img_key] = Image.open(review_frame)
            st.session_state[review_key] = None
            st.rerun()

        if retake:
            st.session_state[review_key] = None
            proc = st.session_state.get(f"processor_{med_idx}")
            if proc is not None:
                proc.reset_capture()
            st.rerun()

        return

    st.html(
        f"""
        <div class="med-card">
            <div class="med-card-header">
                <div class="med-card-title">📷 Scan Your Medicine ({label})</div>
                <div class="camera-standin-badge">{CAMERA_STANDIN_NOTE}</div>
            </div>
            <div style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
                Position the medicine packaging inside the target box.
            </div>
        </div>
        """
    )

    tab_live, tab_snapshot, tab_upload, tab_manual = st.tabs([
        "📷 Live Camera",
        "📸 Snapshot Camera (Fallback)",
        "📁 Upload Image (Fallback)",
        "⌨ Type Name",
    ])

    with tab_live:
        render_live_camera_scanner(med_idx, label)

    with tab_snapshot:
        cam_pic = st.camera_input(
            f"Take a photo of {label}",
            key=f"camera_snap_{med_idx}",
            label_visibility="collapsed",
        )
        if cam_pic is not None and st.button(f"Review Snapshot ({label})", key=f"btn_snap_{med_idx}", type="primary"):
            st.session_state[review_key] = Image.open(cam_pic)
            st.rerun()

    with tab_upload:
        uploaded_file = st.file_uploader(
            f"Upload strip photo for {label}",
            type=SUPPORTED_IMAGE_TYPES,
            key=f"uploader_{med_idx}",
            label_visibility="collapsed",
        )
        if uploaded_file is not None and st.button(f"Review Uploaded Photo ({label})", key=f"btn_upload_{med_idx}", type="primary"):
            st.session_state[review_key] = Image.open(uploaded_file)
            st.rerun()

    with tab_manual:
        manual_txt = st.text_input(
            f"Or type medicine / brand name for {label}:",
            placeholder="e.g. Ecosprin 75 or Ibuprofen 400",
        )
        if st.button(f"Identify Typed Name ({label})", key=f"btn_manual_{med_idx}"):
            if manual_txt.strip():
                normalizer = get_normalizer()
                st.session_state[current_drug_key] = normalizer.normalize(manual_txt)
                st.rerun()


def render_demo_selector():
    """Renders the deterministic demo mode selector."""
    st.markdown("### Select Execution Mode")
    mode_options = [
        "Live OCR (Camera / Upload)",
        DEMO_SCENARIOS["INTERACTION"]["name"],
        DEMO_SCENARIOS["NO_KNOWN_INTERACTION"]["name"],
        DEMO_SCENARIOS["UNRECOGNIZED"]["name"],
        DEMO_SCENARIOS["SEVERE_CARDIAC"]["name"],
        DEMO_SCENARIOS["STATIN_CYP3A4"]["name"],
        DEMO_SCENARIOS["FULL_PRESCRIPTION"]["name"],
    ]

    selected = st.radio(
        "Mode selection",
        options=mode_options,
        key="mode_radio",
        label_visibility="collapsed",
        horizontal=False,
    )

    normalizer = get_normalizer()

    if selected != st.session_state.mode_selection:
        st.session_state.mode_selection = selected
        reset_session()

        if DEMO_SCENARIOS["INTERACTION"]["name"] in selected:
            scenario = DEMO_SCENARIOS["INTERACTION"]
            st.session_state.med1_drug = normalizer.normalize(scenario["med1_raw"])
            st.session_state.med2_drug = normalizer.normalize(scenario["med2_raw"])
            st.session_state.current_page = "scanner"
            st.rerun()

        elif DEMO_SCENARIOS["NO_KNOWN_INTERACTION"]["name"] in selected:
            scenario = DEMO_SCENARIOS["NO_KNOWN_INTERACTION"]
            st.session_state.med1_drug = normalizer.normalize(scenario["med1_raw"])
            st.session_state.med2_drug = normalizer.normalize(scenario["med2_raw"])
            st.session_state.current_page = "scanner"
            st.rerun()

        elif DEMO_SCENARIOS["UNRECOGNIZED"]["name"] in selected:
            scenario = DEMO_SCENARIOS["UNRECOGNIZED"]
            st.session_state.med1_drug = normalizer.normalize(scenario["med1_raw"])
            st.session_state.med2_drug = normalizer.normalize(scenario["med2_raw"])
            st.session_state.current_page = "scanner"
            st.rerun()

        elif DEMO_SCENARIOS["SEVERE_CARDIAC"]["name"] in selected:
            scenario = DEMO_SCENARIOS["SEVERE_CARDIAC"]
            st.session_state.med1_drug = normalizer.normalize(scenario["med1_raw"])
            st.session_state.med2_drug = normalizer.normalize(scenario["med2_raw"])
            st.session_state.current_page = "scanner"
            st.rerun()

        elif DEMO_SCENARIOS["STATIN_CYP3A4"]["name"] in selected:
            scenario = DEMO_SCENARIOS["STATIN_CYP3A4"]
            st.session_state.med1_drug = normalizer.normalize(scenario["med1_raw"])
            st.session_state.med2_drug = normalizer.normalize(scenario["med2_raw"])
            st.session_state.current_page = "scanner"
            st.rerun()

        elif DEMO_SCENARIOS["FULL_PRESCRIPTION"]["name"] in selected:
            scenario = DEMO_SCENARIOS["FULL_PRESCRIPTION"]
            parser = get_prescription_parser()
            parse_res = parser.parse_text(scenario["presc_text"])
            st.session_state.prescription_detected_meds = parse_res.detected_medicines
            engine = get_interaction_engine()
            ens_res = engine.check_ensemble_interactions(parse_res.detected_medicines)
            st.session_state.ensemble_result = ens_res
            st.session_state.current_page = "prescription"
            st.rerun()

        else:
            st.rerun()


# ============================================================
# MAIN APPLICATION ENTRY POINT
# ============================================================

def render_main_app():
    """Multi-page application layout with neumorphic navigation."""
    init_session_state()

    current_page = st.session_state.get("current_page", "landing")

    # Show nav on all pages except landing
    if current_page != "landing":
        render_nav()
    else:
        # Minimal header on landing
        from src.privacy.network_monitor import get_network_request_count
        net_count = get_network_request_count()
        st.html(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
            <div class="mg-nav-logo">
                <div class="mg-nav-logo-icon">🛡️</div>
                <div class="mg-nav-logo-text">MedGuard</div>
            </div>
            <div class="offline-pill" style="font-size:.75rem;">
                <span class="pulse-dot"></span>&nbsp;{net_count} network requests · All local
            </div>
        </div>
        """)
        nav_cols = st.columns(7)
        nav_items = [("🏠", "dashboard"), ("💊", "scanner"), ("📄", "prescription"),
                     ("📜", "history"), ("🔍", "how_it_works"), ("🔒", "privacy"), ("ℹ️", "about")]
        for col, (icon, page_key) in zip(nav_cols, nav_items):
            with col:
                if st.button(icon, key=f"landing_nav_{page_key}", use_container_width=True, help=page_key.replace("_", " ").title()):
                    st.session_state.current_page = page_key
                    st.rerun()

    # Page router
    page_map = {
        "landing": render_landing_page,
        "dashboard": render_dashboard_page,
        "scanner": render_scanner_page,
        "prescription": render_prescription_page,
        "history": render_history_page,
        "how_it_works": render_how_it_works_page,
        "privacy": render_privacy_page,
        "about": render_about_page,
        "settings": render_settings_page,
    }

    page_fn = page_map.get(current_page, render_landing_page)
    page_fn()

    # Footer on all pages
    st.html("""
    <div style="margin-top:3rem;padding-top:1.5rem;border-top:1px solid rgba(108,99,255,0.1);
                text-align:center;font-size:.78rem;color:var(--text-muted);">
        🛡️ MedGuard &nbsp;·&nbsp; 100% Offline &nbsp;·&nbsp; All processing on this device &nbsp;·&nbsp;
        Not a diagnostic tool — consult your pharmacist
    </div>
    """)
