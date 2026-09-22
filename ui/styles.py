"""
MedGuard - UI Styles & Custom CSS
Neumorphic Medical HealthTech Design System
Primary background: #E0E5EC | Accent: #6C63FF | Medical: #38B2AC
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap');

/* ============================================================
   ROOT DESIGN TOKENS — NEUMORPHIC SYSTEM
   ============================================================ */
:root {
    --bg: #E0E5EC;
    --bg-card: #E0E5EC;
    --text-primary: #3D4852;
    --text-secondary: #6B7280;
    --text-muted: #9CA3AF;
    --accent: #6C63FF;
    --accent-hover: #5B52EE;
    --accent-medical: #38B2AC;
    --accent-medical-hover: #2C9A94;
    --danger: #EF4444;
    --warning: #F59E0B;
    --success: #10B981;
    --info: #3B82F6;

    --shadow-light: rgba(255, 255, 255, 0.85);
    --shadow-dark: rgba(166, 180, 200, 0.75);
    --shadow-neu-out: 8px 8px 20px rgba(166, 180, 200, 0.75), -8px -8px 20px rgba(255, 255, 255, 0.85);
    --shadow-neu-in: inset 4px 4px 10px rgba(166, 180, 200, 0.6), inset -4px -4px 10px rgba(255, 255, 255, 0.9);
    --shadow-neu-sm: 4px 4px 10px rgba(166, 180, 200, 0.6), -4px -4px 10px rgba(255, 255, 255, 0.8);
    --shadow-neu-lg: 12px 12px 32px rgba(166, 180, 200, 0.8), -12px -12px 32px rgba(255, 255, 255, 0.9);
    --shadow-accent: 0 8px 24px rgba(108, 99, 255, 0.3);

    --radius-card: 24px;
    --radius-btn: 14px;
    --radius-pill: 9999px;
    --radius-sm: 10px;
    --radius-md: 16px;

    --transition: all 0.28s cubic-bezier(0.4, 0, 0.2, 1);
    --transition-fast: all 0.15s ease-out;
}

/* ============================================================
   GLOBAL LAYOUT OVERRIDES
   ============================================================ */
.stApp {
    background-color: var(--bg) !important;
    font-family: 'Inter', 'Plus Jakarta Sans', system-ui, sans-serif !important;
    color: var(--text-primary) !important;
}

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 4rem !important;
    max-width: 1100px !important;
}

/* Hide default Streamlit toolbar & hamburger in production */
#MainMenu { visibility: hidden !important; }
.stToolbar { visibility: hidden !important; }
footer { visibility: hidden !important; }
header { background: transparent !important; }

/* Streamlit element text color overrides */
.stMarkdown, .stText, p, label, .stCaption {
    color: var(--text-primary) !important;
}

h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary) !important;
    font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
    font-weight: 700 !important;
    line-height: 1.3 !important;
}

/* ============================================================
   MATERIAL ICONS & STREAMLIT ICON PROTECTION
   ============================================================ */
[data-testid="stIconMaterial"],
[data-testid*="stIcon"],
.material-symbols-rounded,
.material-symbols-outlined,
.material-icons,
[data-testid="stExpanderToggleIcon"],
[data-testid="stExpanderToggleIcon"] span,
[data-testid="stExpanderToggleIcon"] i,
[data-testid="stFileUploadDropzone"] span[data-testid="stIconMaterial"],
[data-testid="stFileUploadDropzone"] i,
i[class*="material"],
span[class*="material"] {
    font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
    font-weight: normal !important;
    font-style: normal !important;
    font-size: 20px !important;
    line-height: 1 !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    white-space: nowrap !important;
    word-wrap: normal !important;
    direction: ltr !important;
    -webkit-font-feature-settings: 'liga' 1 !important;
    -moz-font-feature-settings: 'liga' 1 !important;
    font-feature-settings: 'liga' 1 !important;
    -webkit-font-smoothing: antialiased !important;
}

/* ============================================================
   NEUMORPHIC NAV BAR
   ============================================================ */
.mg-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--bg);
    border-radius: var(--radius-card);
    box-shadow: var(--shadow-neu-out);
    padding: 0.75rem 1.5rem;
    margin-bottom: 2rem;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.mg-nav-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
}

.mg-nav-logo-icon {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, var(--accent), var(--accent-medical));
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    box-shadow: var(--shadow-neu-sm);
    flex-shrink: 0;
}

.mg-nav-logo-text {
    font-size: 1.3rem;
    font-weight: 800;
    background: linear-gradient(135deg, var(--accent), var(--accent-medical));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-family: 'Plus Jakarta Sans', sans-serif;
    letter-spacing: -0.03em;
}

.mg-nav-links {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    flex-wrap: wrap;
}

.mg-nav-link {
    padding: 0.45rem 0.9rem;
    border-radius: var(--radius-btn);
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-secondary);
    cursor: pointer;
    transition: var(--transition-fast);
    border: none;
    background: transparent;
    letter-spacing: 0.01em;
}

.mg-nav-link:hover {
    color: var(--accent);
    background: rgba(108, 99, 255, 0.06);
}

.mg-nav-link-active {
    color: var(--accent) !important;
    background: var(--bg) !important;
    box-shadow: var(--shadow-neu-in) !important;
}

.mg-nav-cta {
    background: linear-gradient(135deg, var(--accent), var(--accent-medical));
    color: #ffffff !important;
    border-radius: var(--radius-btn);
    padding: 0.55rem 1.2rem;
    font-size: 0.85rem;
    font-weight: 700;
    cursor: pointer;
    box-shadow: var(--shadow-accent);
    transition: var(--transition);
    border: none;
    letter-spacing: 0.01em;
}

.mg-nav-cta:hover {
    box-shadow: 0 12px 32px rgba(108, 99, 255, 0.4);
    transform: translateY(-1px);
}

/* ============================================================
   NEUMORPHIC CARDS
   ============================================================ */
.mg-card {
    background: var(--bg);
    border-radius: var(--radius-card);
    box-shadow: var(--shadow-neu-out);
    padding: 1.8rem;
    margin-bottom: 1.2rem;
    transition: var(--transition);
}

.mg-card:hover {
    box-shadow: var(--shadow-neu-lg);
    transform: translateY(-2px);
}

.mg-card-sm {
    background: var(--bg);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-neu-sm);
    padding: 1.2rem;
    margin-bottom: 0.8rem;
}

.mg-card-inset {
    background: var(--bg);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-neu-in);
    padding: 1.2rem;
}

.mg-card-accent {
    background: linear-gradient(135deg, rgba(108, 99, 255, 0.08), rgba(56, 178, 172, 0.08));
    border-radius: var(--radius-card);
    box-shadow: var(--shadow-neu-out);
    padding: 1.8rem;
    border-left: 4px solid var(--accent);
    margin-bottom: 1.2rem;
}

/* ============================================================
   NEUMORPHIC BUTTONS
   ============================================================ */
.mg-btn-primary {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    background: linear-gradient(135deg, var(--accent), var(--accent-medical));
    color: #ffffff;
    border: none;
    border-radius: var(--radius-btn);
    padding: 0.8rem 2rem;
    font-size: 0.95rem;
    font-weight: 700;
    cursor: pointer;
    box-shadow: var(--shadow-accent);
    transition: var(--transition);
    letter-spacing: 0.02em;
    font-family: 'Inter', sans-serif;
    min-width: 160px;
}

.mg-btn-primary:hover {
    box-shadow: 0 16px 40px rgba(108, 99, 255, 0.4);
    transform: translateY(-2px);
}

.mg-btn-primary:active {
    box-shadow: var(--shadow-neu-in);
    transform: translateY(0);
}

.mg-btn-secondary {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    background: var(--bg);
    color: var(--text-primary);
    border: none;
    border-radius: var(--radius-btn);
    padding: 0.8rem 2rem;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    box-shadow: var(--shadow-neu-out);
    transition: var(--transition);
    letter-spacing: 0.01em;
    font-family: 'Inter', sans-serif;
    min-width: 160px;
}

.mg-btn-secondary:hover {
    box-shadow: var(--shadow-neu-lg);
    transform: translateY(-2px);
}

.mg-btn-secondary:active {
    box-shadow: var(--shadow-neu-in);
    transform: translateY(0);
}

/* ============================================================
   STREAMLIT BUTTON OVERRIDES
   ============================================================ */
.stButton > button {
    background: var(--bg) !important;
    color: var(--text-primary) !important;
    border: none !important;
    border-radius: var(--radius-btn) !important;
    box-shadow: var(--shadow-neu-out) !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    transition: var(--transition) !important;
    padding: 0.65rem 1.5rem !important;
    letter-spacing: 0.01em !important;
}

.stButton > button:hover {
    box-shadow: var(--shadow-neu-lg) !important;
    transform: translateY(-1px) !important;
    color: var(--accent) !important;
    border: none !important;
}

.stButton > button:active {
    box-shadow: var(--shadow-neu-in) !important;
    transform: translateY(0) !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent), var(--accent-medical)) !important;
    color: #ffffff !important;
    box-shadow: var(--shadow-accent) !important;
}

.stButton > button[kind="primary"]:hover {
    box-shadow: 0 12px 32px rgba(108, 99, 255, 0.4) !important;
}

/* ============================================================
   STREAMLIT TABS OVERRIDE
   ============================================================ */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg) !important;
    border-radius: var(--radius-card) !important;
    box-shadow: var(--shadow-neu-in) !important;
    padding: 0.4rem !important;
    gap: 0.25rem !important;
    border: none !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: var(--radius-btn) !important;
    color: var(--text-secondary) !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    border: none !important;
    padding: 0.55rem 1.1rem !important;
    transition: var(--transition) !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--accent) !important;
    background: rgba(108, 99, 255, 0.06) !important;
}

.stTabs [aria-selected="true"] {
    background: var(--bg) !important;
    color: var(--accent) !important;
    box-shadow: var(--shadow-neu-out) !important;
}

.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1.5rem !important;
}

.stTabBar, [data-testid="stTabBar"] {
    background: var(--bg) !important;
}

/* ============================================================
   STREAMLIT INPUT OVERRIDES
   ============================================================ */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background: var(--bg) !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    box-shadow: var(--shadow-neu-in) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    padding: 0.75rem 1rem !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    box-shadow: var(--shadow-neu-in), 0 0 0 2px rgba(108, 99, 255, 0.25) !important;
}

/* ============================================================
   STREAMLIT EXPANDER OVERRIDE
   ============================================================ */
.stExpander {
    background: var(--bg) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-neu-sm) !important;
    border: none !important;
    margin-bottom: 0.75rem !important;
    overflow: hidden !important;
}

.stExpander > details {
    background: transparent !important;
    border: none !important;
}

.stExpander > details > summary {
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    cursor: pointer !important;
    padding: 0.6rem 0.9rem !important;
    border-radius: var(--radius-sm) !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.5rem !important;
}

.stExpander > details > summary:hover {
    color: var(--accent) !important;
    background: rgba(108, 99, 255, 0.04) !important;
}

.stExpander > details > summary p {
    margin: 0 !important;
    display: inline !important;
}

/* ============================================================
   STREAMLIT FILE UPLOADER OVERRIDE
   ============================================================ */
[data-testid="stFileUploader"] {
    margin-bottom: 1rem !important;
}

[data-testid="stFileUploadDropzone"] {
    background: var(--bg) !important;
    border: 2px dashed rgba(108, 99, 255, 0.25) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-neu-in) !important;
    padding: 1.5rem 1rem !important;
}

[data-testid="stFileUploadDropzone"]:hover {
    border-color: var(--accent) !important;
    box-shadow: var(--shadow-neu-in), 0 0 12px rgba(108, 99, 255, 0.15) !important;
}

[data-testid="stFileUploadDropzone"] button {
    background: linear-gradient(135deg, var(--accent), var(--accent-medical)) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: var(--radius-btn) !important;
    box-shadow: var(--shadow-accent) !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.2rem !important;
    font-family: 'Inter', sans-serif !important;
}

[data-testid="stFileUploadDropzone"] button:hover {
    box-shadow: 0 8px 20px rgba(108, 99, 255, 0.4) !important;
    color: #ffffff !important;
}

[data-testid="stFileUploadDropzone"] small,
[data-testid="stFileUploadDropzone"] p {
    color: var(--text-secondary) !important;
    font-size: 0.82rem !important;
}

/* ============================================================
   LANDING HERO SECTION
   ============================================================ */
.mg-hero {
    text-align: center;
    padding: 3rem 1rem 2rem;
}

.mg-hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--bg);
    border-radius: var(--radius-pill);
    box-shadow: var(--shadow-neu-sm);
    padding: 0.35rem 1rem;
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--accent);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}

.mg-hero-title {
    font-size: 3rem;
    font-weight: 900;
    line-height: 1.1;
    letter-spacing: -0.04em;
    color: var(--text-primary);
    margin-bottom: 1.2rem;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

.mg-hero-title-accent {
    background: linear-gradient(135deg, var(--accent), var(--accent-medical));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.mg-hero-subtitle {
    font-size: 1.15rem;
    color: var(--text-secondary);
    line-height: 1.65;
    max-width: 580px;
    margin: 0 auto 2.5rem;
    font-weight: 400;
}

.mg-hero-ctas {
    display: flex;
    justify-content: center;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 3rem;
}

.mg-hero-badge-row {
    display: flex;
    justify-content: center;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin-top: 1rem;
}

.mg-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--bg);
    border-radius: var(--radius-pill);
    box-shadow: var(--shadow-neu-sm);
    padding: 0.4rem 0.9rem;
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--text-secondary);
}

/* ============================================================
   STAT CARDS (DASHBOARD)
   ============================================================ */
.mg-stat-card {
    background: var(--bg);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-neu-out);
    padding: 1.2rem 1.4rem;
    text-align: center;
    transition: var(--transition);
}

.mg-stat-card:hover {
    box-shadow: var(--shadow-neu-lg);
    transform: translateY(-3px);
}

.mg-stat-icon {
    font-size: 1.8rem;
    margin-bottom: 0.5rem;
    display: block;
}

.mg-stat-value {
    font-size: 2rem;
    font-weight: 800;
    color: var(--accent);
    font-family: 'Plus Jakarta Sans', sans-serif;
    letter-spacing: -0.03em;
    line-height: 1;
    margin-bottom: 0.3rem;
}

.mg-stat-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ============================================================
   FEATURE CARDS
   ============================================================ */
.mg-feature-card {
    background: var(--bg);
    border-radius: var(--radius-card);
    box-shadow: var(--shadow-neu-out);
    padding: 1.8rem;
    text-align: center;
    transition: var(--transition);
    height: 100%;
}

.mg-feature-card:hover {
    box-shadow: var(--shadow-neu-lg);
    transform: translateY(-4px);
}

.mg-feature-icon {
    width: 64px;
    height: 64px;
    border-radius: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.8rem;
    margin: 0 auto 1rem;
    box-shadow: var(--shadow-neu-sm);
}

.mg-feature-icon-accent {
    background: linear-gradient(135deg, rgba(108, 99, 255, 0.12), rgba(56, 178, 172, 0.12));
}

.mg-feature-title {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
}

.mg-feature-desc {
    font-size: 0.88rem;
    color: var(--text-secondary);
    line-height: 1.5;
}

/* ============================================================
   PIPELINE STEPS (HOW IT WORKS)
   ============================================================ */
.mg-pipeline {
    display: flex;
    flex-direction: column;
    gap: 0;
    align-items: center;
    padding: 1rem 0;
}

.mg-pipeline-step {
    background: var(--bg);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-neu-out);
    padding: 1.1rem 1.5rem;
    width: 100%;
    max-width: 520px;
    display: flex;
    align-items: center;
    gap: 1rem;
    transition: var(--transition);
}

.mg-pipeline-step:hover {
    box-shadow: var(--shadow-neu-lg);
    transform: translateX(4px);
}

.mg-pipeline-number {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent), var(--accent-medical));
    color: white;
    font-weight: 800;
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    box-shadow: var(--shadow-accent);
}

.mg-pipeline-arrow {
    text-align: center;
    font-size: 1.2rem;
    color: var(--accent);
    padding: 0.3rem 0;
    opacity: 0.6;
}

.mg-pipeline-content {
    flex: 1;
}

.mg-pipeline-step-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.2rem;
}

.mg-pipeline-step-desc {
    font-size: 0.82rem;
    color: var(--text-secondary);
    line-height: 1.4;
}

/* ============================================================
   MEDICINE SCAN CARD
   ============================================================ */
.med-card {
    background: var(--bg);
    border-radius: var(--radius-card);
    box-shadow: var(--shadow-neu-out);
    padding: 1.6rem;
    margin-bottom: 1rem;
    transition: var(--transition);
}

.med-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.8rem;
    border-bottom: 2px solid rgba(108, 99, 255, 0.06);
}

.med-card-title {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 8px;
}

.camera-standin-badge {
    font-size: 0.72rem;
    color: var(--text-muted);
    background: var(--bg);
    border-radius: var(--radius-pill);
    box-shadow: var(--shadow-neu-in);
    padding: 3px 10px;
    font-weight: 500;
}

/* ============================================================
   STATUS PILLS & OFFLINE BADGE
   ============================================================ */
.mg-status-bar {
    display: flex;
    justify-content: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 2rem;
}

.status-pill-container {
    display: flex;
    justify-content: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 2rem;
}

.offline-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: var(--bg);
    color: var(--success);
    border-radius: var(--radius-pill);
    box-shadow: var(--shadow-neu-sm);
    padding: 0.4rem 1rem;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.pulse-dot {
    width: 9px;
    height: 9px;
    background-color: var(--success);
    border-radius: 50%;
    display: inline-block;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
    animation: pulse-glow 2s infinite;
}

@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2); }
    50% { box-shadow: 0 0 0 5px rgba(16, 185, 129, 0.08); }
}

/* ============================================================
   DETECTED MEDICINE CARDS
   ============================================================ */
.detected-pill {
    background: var(--bg);
    box-shadow: var(--shadow-neu-sm);
    border-radius: var(--radius-md);
    padding: 1rem 1.2rem;
    margin-top: 0.75rem;
    border-left: 3px solid var(--success);
}

.detected-pill-unrecognized {
    background: var(--bg);
    box-shadow: var(--shadow-neu-sm);
    border-radius: var(--radius-md);
    padding: 1rem 1.2rem;
    margin-top: 0.75rem;
    border-left: 3px solid var(--warning);
}

.detected-label {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--success);
    margin-bottom: 0.3rem;
}

.detected-name {
    font-size: 1.15rem;
    font-weight: 800;
    color: var(--text-primary);
    font-family: 'Plus Jakarta Sans', sans-serif;
}

.detected-meta {
    font-size: 0.83rem;
    color: var(--text-secondary);
    margin-top: 0.25rem;
}

/* ============================================================
   SCAN DIVIDER
   ============================================================ */
.scan-divider {
    text-align: center;
    margin: 0.75rem 0;
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--accent);
    opacity: 0.5;
}

/* ============================================================
   RESULT CARDS — STATE A/B/C
   ============================================================ */
.result-card-interaction {
    background: var(--bg);
    border-radius: var(--radius-card);
    box-shadow: var(--shadow-neu-out);
    padding: 2rem;
    margin-top: 1.5rem;
    border-top: 4px solid var(--danger);
    animation: slide-up 0.35s ease-out;
}

.result-header-interaction {
    display: flex;
    align-items: center;
    gap: 12px;
    color: var(--danger);
    font-size: 1.4rem;
    font-weight: 800;
    margin-bottom: 1.2rem;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

.result-card-no-interaction {
    background: var(--bg);
    border-radius: var(--radius-card);
    box-shadow: var(--shadow-neu-out);
    padding: 2rem;
    margin-top: 1.5rem;
    border-top: 4px solid var(--info);
    animation: slide-up 0.35s ease-out;
}

.result-header-no-interaction {
    display: flex;
    align-items: center;
    gap: 12px;
    color: var(--info);
    font-size: 1.4rem;
    font-weight: 800;
    margin-bottom: 1.2rem;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

.result-card-unrecognized {
    background: var(--bg);
    border-radius: var(--radius-card);
    box-shadow: var(--shadow-neu-out);
    padding: 2rem;
    margin-top: 1.5rem;
    border-top: 4px solid var(--warning);
    animation: slide-up 0.35s ease-out;
}

.result-header-unrecognized {
    display: flex;
    align-items: center;
    gap: 12px;
    color: var(--warning);
    font-size: 1.4rem;
    font-weight: 800;
    margin-bottom: 1.2rem;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ============================================================
   RESULT INNER ELEMENTS
   ============================================================ */
.drugs-pairing-banner {
    background: var(--bg);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-neu-in);
    padding: 1.1rem;
    text-align: center;
    margin-bottom: 1.5rem;
}

.drugs-pairing-text {
    font-size: 1.3rem;
    font-weight: 800;
    color: var(--text-primary);
    letter-spacing: 0.02em;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

.result-section-title {
    font-size: 0.82rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-secondary);
    margin-top: 1.2rem;
    margin-bottom: 0.4rem;
    padding-bottom: 0.35rem;
    border-bottom: 1px solid rgba(108, 99, 255, 0.1);
}

.result-section-content {
    font-size: 1.02rem;
    line-height: 1.65;
    color: var(--text-primary);
}

.recommendation-box {
    background: var(--bg);
    box-shadow: var(--shadow-neu-in);
    border-left: 4px solid var(--accent);
    padding: 1rem 1.2rem;
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    margin: 1rem 0;
    font-weight: 600;
    color: var(--accent);
}

.meta-footer {
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(108, 99, 255, 0.08);
    font-size: 0.83rem;
    color: var(--text-muted);
}

.disclaimer-box {
    background: var(--bg);
    box-shadow: var(--shadow-neu-in);
    border-radius: var(--radius-sm);
    padding: 0.9rem 1rem;
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-top: 1.2rem;
    text-align: center;
}

/* ============================================================
   LIVE CAMERA / FRAMING GUIDANCE
   ============================================================ */
.framing-guidance-bar {
    display: flex;
    align-items: center;
    gap: 10px;
    background: var(--bg);
    border-radius: var(--radius-sm);
    box-shadow: var(--shadow-neu-sm);
    padding: 0.6rem 1rem;
    margin-top: 0.7rem;
    font-size: 0.88rem;
    color: var(--text-primary);
}

.guidance-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
}

.guidance-dot-steady {
    background-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(108, 99, 255, 0.2);
    animation: pulse-glow-purple 1.5s infinite;
}

.guidance-dot-good {
    background-color: var(--success);
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
}

.guidance-dot-adjust {
    background-color: var(--warning);
    box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.2);
}

@keyframes pulse-glow-purple {
    0%, 100% { box-shadow: 0 0 0 2px rgba(108, 99, 255, 0.2); }
    50% { box-shadow: 0 0 0 6px rgba(108, 99, 255, 0.06); }
}

.scan-hints-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px 14px;
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-top: 0.5rem;
}

.captured-review-card {
    background: var(--bg);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-neu-sm);
    padding: 1.2rem;
    margin-top: 0.8rem;
}

/* ============================================================
   MEDGUARD HEADER (LEGACY + NEUMORPHIC)
   ============================================================ */
.medguard-header {
    text-align: center;
    margin-bottom: 0.5rem;
}

.medguard-title {
    font-size: 2.6rem;
    font-weight: 900;
    letter-spacing: -0.04em;
    background: linear-gradient(135deg, var(--accent), var(--accent-medical));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.25rem;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

.medguard-subtitle {
    font-size: 1.1rem;
    color: var(--text-secondary);
    margin-bottom: 0.8rem;
    font-weight: 400;
}

/* ============================================================
   PRIVACY PAGE
   ============================================================ */
.mg-privacy-item {
    background: var(--bg);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-neu-out);
    padding: 1.2rem 1.4rem;
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 0.75rem;
    transition: var(--transition);
}

.mg-privacy-item:hover {
    box-shadow: var(--shadow-neu-lg);
    transform: translateX(4px);
}

.mg-privacy-icon {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
    flex-shrink: 0;
    box-shadow: var(--shadow-neu-sm);
}

.mg-privacy-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
}

.mg-privacy-desc {
    font-size: 0.84rem;
    color: var(--text-secondary);
    line-height: 1.5;
}

/* ============================================================
   PAGE SECTION HEADERS
   ============================================================ */
.mg-page-title {
    font-size: 2rem;
    font-weight: 800;
    color: var(--text-primary);
    margin-bottom: 0.4rem;
    font-family: 'Plus Jakarta Sans', sans-serif;
    letter-spacing: -0.03em;
}

.mg-page-subtitle {
    font-size: 1rem;
    color: var(--text-secondary);
    margin-bottom: 2rem;
    line-height: 1.55;
}

.mg-section-divider {
    height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--accent-medical), transparent);
    border-radius: 2px;
    margin: 2rem 0;
    opacity: 0.2;
}

/* ============================================================
   HISTORY PAGE
   ============================================================ */
.mg-history-item {
    background: var(--bg);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-neu-sm);
    padding: 1rem 1.3rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.6rem;
    transition: var(--transition);
    flex-wrap: wrap;
    gap: 0.5rem;
}

.mg-history-item:hover {
    box-shadow: var(--shadow-neu-out);
    transform: translateY(-1px);
}

/* ============================================================
   ANIMATIONS
   ============================================================ */
@keyframes slide-up {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}

@keyframes fade-in {
    from { opacity: 0; }
    to   { opacity: 1; }
}

.mg-animate-in {
    animation: slide-up 0.35s ease-out;
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}

/* ============================================================
   RESPONSIVE
   ============================================================ */
@media (max-width: 768px) {
    .mg-hero-title { font-size: 2rem; }
    .mg-nav-links { display: none; }
    .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
    .mg-card { padding: 1.2rem; }
    .mg-stat-value { font-size: 1.5rem; }
}

/* ============================================================
   SCROLLBAR STYLING
   ============================================================ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: rgba(108, 99, 255, 0.25); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(108, 99, 255, 0.45); }

/* ============================================================
   STALE ELEMENT CLEANUP
   ============================================================ */
.stAlert > div {
    border-radius: var(--radius-md) !important;
    border: none !important;
    box-shadow: var(--shadow-neu-sm) !important;
}

.stSuccess > div { border-left: 4px solid var(--success) !important; }
.stWarning > div { border-left: 4px solid var(--warning) !important; }
.stError > div   { border-left: 4px solid var(--danger) !important; }
.stInfo > div    { border-left: 4px solid var(--info) !important; }

[data-testid="stSpinner"] > div { color: var(--accent) !important; }

/* Radio widget override */
.stRadio > div {
    background: var(--bg) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-neu-in) !important;
    padding: 0.5rem !important;
    gap: 0.25rem !important;
}

</style>
"""
