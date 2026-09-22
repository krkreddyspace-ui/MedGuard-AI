"""
MedGuard - Configuration and Settings
Centralized configuration for offline operation, matching thresholds, paths, camera heuristics, and demo presets.
"""
from pathlib import Path

# Base Paths
CONFIG_DIR = Path(__file__).resolve().parent
BASE_DIR = CONFIG_DIR.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
EASYOCR_MODEL_DIR = MODELS_DIR / "easyocr"
ASSETS_DIR = BASE_DIR / "assets"
DEMO_ASSETS_DIR = ASSETS_DIR / "demo"

# Local Data Files
INTERACTIONS_FILE = DATA_DIR / "interactions.json"
BRAND_GENERIC_MAP_FILE = DATA_DIR / "brand_generic_map.json"

# OCR and Image Processing Settings
SUPPORTED_IMAGE_TYPES = ["png", "jpg", "jpeg", "webp"]
MAX_IMAGE_DIMENSION = 1920
MIN_IMAGE_DIMENSION = 300
OCR_CONFIDENCE_THRESHOLD = 0.35  # Minimum OCR token confidence
DEFAULT_OCR_LANGUAGES = ["en"]

# Camera Scanning & Framing Heuristics (Assistive Only, Not an Object Classifier)
SCAN_ZONE_WIDTH_RATIO = 0.72   # Percentage of camera width for central target zone
SCAN_ZONE_HEIGHT_RATIO = 0.52  # Percentage of camera height for central target zone
GLARE_LUMINANCE_CUTOFF = 245   # Pixel brightness threshold for specular glare check
GLARE_AREA_RATIO_MAX = 0.18    # Max percentage of specular glare pixels before alert
MIN_OCCUPANCY_RATIO = 0.16     # Occupancy threshold below which user is prompted to move closer
MAX_CENTER_DEVIATION = 0.22    # Max fractional distance from scan zone center before centering prompt

# Automatic Capture & Temporal Stability Settings
AUTO_CAPTURE_STABILITY_SECONDS = 0.8  # Duration (seconds) target must remain stable in GOOD_POSITION
STABILITY_MAX_CENTROID_DRIFT = 0.05   # Max 5% normalized centroid movement between frames
STABILITY_MAX_AREA_DRIFT = 0.15       # Max 15% relative bounding box area variance

# Normalization & Fuzzy Matching Settings
FUZZY_MATCH_THRESHOLD = 80  # Conservative cutoff (out of 100) to avoid false matches
MIN_TOKEN_LENGTH = 3        # Discard spurious single/double char tokens

# UI Text and Framing Constants
APP_TITLE = "MedGuard"
APP_SUBTITLE = "Check medicine combinations privately, right on your device."
OFFLINE_BADGE_TEXT = "● OFFLINE · LOCAL PROCESSING"
CAMERA_STANDIN_NOTE = "Laptop prototype — phone camera will be used in the final on-device version."

# Networking Transparency Notice
NETWORKING_STATEMENT = (
    "Configured without external STUN/TURN servers. "
    "MedGuard requires no external service for camera streaming, OCR, normalization, or interaction screening."
)

# Standard Medical Framing & Safety Disclaimers
STANDARD_CONFIRMATION_MSG = (
    "Please confirm this combination with your pharmacist or healthcare professional."
)
STANDARD_DISCLAIMER_MSG = (
    "MedGuard is a screening prototype, not a diagnostic tool. "
    "Our local database is curated for demonstration and does not replace professional clinical advice."
)
NO_KNOWN_INTERACTION_MSG = (
    "No matching interaction was found in MedGuard's local dataset. "
    "Important: This does not rule out every possible interaction. Confirm with a pharmacist if you have concerns."
)
UNRECOGNIZED_MEDICINE_MSG = (
    "This medicine could not be confidently matched to our local database. "
    "We cannot determine interaction status."
)

# Assistive Framing Guidance Copy (Spatial positioning feedback)
FRAMING_GUIDANCE_COPY = {
    "NO_OBJECT": "Position the medicine or document inside the frame",
    "TOO_FAR": "Move closer",
    "OFF_CENTER": "Center the target",
    "PARTIALLY_OUT": "Keep the target fully visible",
    "GLARE": "Reduce glare or adjust angle",
    "GOOD_POSITION": "✓ Good position — hold steady",
}

# Capture Lifecycle Guidance Copy (Temporal progress feedback)
CAPTURE_LIFECYCLE_COPY = {
    "SCANNING": "Position the medicine or document inside the frame",
    "HOLD_STEADY": "✓ Hold steady...",
    "CAPTURED": "✓ Captured! Reviewing...",
    "REVIEW": "Review your scan",
    "PROCESSING": "Analyzing medicine packaging...",
}

FRAMING_RECOMMENDATION_TIPS = {
    "NO_OBJECT": "Tip: Hold the strip inside the target box with text facing forward.",
    "TOO_FAR": "Tip: Bring the package closer so printed drug text is clearly readable.",
    "OFF_CENTER": "Tip: Align the brand or generic name within the center crosshairs.",
    "PARTIALLY_OUT": "Tip: Pull back slightly so all edges of the blister pack are in view.",
    "GLARE": "Tip: Tilt the foil pack slightly away from direct light to avoid blinding reflections.",
    "GOOD_POSITION": "Steady: Hold still for automatic capture...",
    "HOLD_STEADY": "Holding steady: Capturing automatically...",
}

# Deterministic Demo Scenarios
DEMO_SCENARIOS = {
    "INTERACTION": {
        "id": "interaction",
        "name": "Demo 1: Potential Interaction (Ecosprin + Combiflam)",
        "med1_raw": "Ecosprin 75 Tablets",
        "med2_raw": "Combiflam Pain Relief",
        "expected_med1_generic": "aspirin",
        "expected_med2_generic": "ibuprofen",
        "description": "Ecosprin (Aspirin) + Combiflam (Ibuprofen) — documented gastrointestinal and antiplatelet interaction.",
    },
    "NO_KNOWN_INTERACTION": {
        "id": "no_interaction",
        "name": "Demo 2: No Known Interaction (Crocin + Cetzine)",
        "med1_raw": "Crocin 650 Paracetamol IP",
        "med2_raw": "Cetzine 10mg Tablets",
        "expected_med1_generic": "paracetamol",
        "expected_med2_generic": "cetirizine",
        "description": "Crocin (Paracetamol) + Cetzine (Cetirizine) — no known interaction in local curated dataset.",
    },
    "UNRECOGNIZED": {
        "id": "unrecognized",
        "name": "Demo 3: Unrecognized Medicine (Zyxolamin + Combiflam)",
        "med1_raw": "Zyxolamin Forte 250mg",
        "med2_raw": "Combiflam",
        "expected_med1_generic": None,
        "expected_med2_generic": "ibuprofen",
        "description": "Demonstrates safe handling: unrecognized medicine is NEVER marked safe.",
    },
    "SEVERE_CARDIAC": {
        "id": "severe_cardiac",
        "name": "Demo 4: Severe Cardiovascular Warning (Viagra + Nitrocontin)",
        "med1_raw": "Viagra 50mg",
        "med2_raw": "Nitrocontin 2.6",
        "expected_med1_generic": "sildenafil",
        "expected_med2_generic": "nitroglycerin",
        "description": "Viagra (Sildenafil) + Nitrocontin (Nitroglycerin) — critical, life-threatening blood pressure drop warning.",
    },
    "STATIN_CYP3A4": {
        "id": "statin_cyp3a4",
        "name": "Demo 5: Enzyme Inhibition Toxicity (Atorlip + Biaxin)",
        "med1_raw": "Atorlip 10",
        "med2_raw": "Biaxin 500",
        "expected_med1_generic": "atorvastatin",
        "expected_med2_generic": "clarithromycin",
        "description": "Atorlip (Atorvastatin) + Biaxin (Clarithromycin) — CYP3A4 enzyme blockage elevating statin levels to toxic threshold.",
    },
    "FULL_PRESCRIPTION": {
        "id": "full_prescription",
        "name": "Demo 6: Multi-Medicine Prescription Regimen",
        "presc_text": "1. Ecosprin 75mg - 1 tab daily\n2. Combiflam - 1 tab as needed\n3. Pan-D - 1 cap before meals\n4. Glycomet 500 - 1 tab after lunch",
        "description": "Multi-drug full prescription screening with automatic medicine parsing, severity sorting, and chemical profiling.",
    },
}
