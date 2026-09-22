# MedGuard

> **An offline, camera-first medication interaction checker for patients and caregivers.**

MedGuard is a privacy-first, on-device decision support prototype built for the **iQOO Hackathon 2026 HealthTech track**. It allows patients and caregivers managing polypharmacy to view a live camera preview of physical medicine strips, guide packaging into a scanning reticle using real-time local framing feedback, extract and normalize drug names strictly in volatile memory, and screen combinations against a local clinical interaction database—with **no cloud LLMs** and **no external network services**.

---

## 1. Problem Statement

Polypharmacy—the simultaneous use of multiple prescription medications—is a leading cause of preventable adverse drug events, especially among elderly individuals, chronic disease patients, and informal caregivers.

Traditional drug-interaction checkers suffer from critical barriers for non-clinicians:
- **Typing Friction**: Complex chemical names (e.g., *amoxicillin-clavulanate*, *spironolactone*) are difficult to spell accurately, especially for seniors or stressed caregivers.
- **Clinician-Centric Jargon**: Existing portals present dense pharmacokinetic tables rather than actionable, plain-language patient guidance.
- **Privacy & Connectivity Concerns**: Cloud-based checkers require continuous internet access and transmit sensitive health queries to remote servers.

---

## 2. The MedGuard Solution

MedGuard replaces cumbersome typing and cloud dependency with an intuitive, camera-first interaction flow:
1. **Live Camera Preview**: Users view their real-time webcam feed with a centered rectangular scanning reticle directly in the browser.
2. **Assistive Framing & Stability Heuristics**: Lightweight OpenCV heuristics evaluate target occupancy, centering, foil glare, and stationary stability (< 5% centroid drift, < 15% area variance).
3. **Automatic Capture**: When a medicine strip or packaging is held steady in the target zone for $\ge 0.8\text{s}$, MedGuard automatically triggers capture without requiring the user to press a button while balancing a blister pack.
4. **Captured Photo Review**: The user reviews the captured frame with **exactly two primary action buttons**: `[ ✓ Use Photo ]` and `[ ↻ Retake ]`. OCR is **never** executed before confirmation.
5. **Local Computer Vision Preprocessing**: Upon confirmation, images undergo CLAHE contrast enhancement, edge sharpening, and bicubic scaling.
6. **Local EasyOCR**: Text is extracted locally using pre-downloaded weights without runtime downloads.
7. **Packaging Noise Filtration**: Proprietary regex filters strip batch codes, expiry dates, dosages, and manufacturing stamps.
8. **Intelligent Normalization & Defensible Copy**: Brand names are mapped to generic active ingredients using RapidFuzz ($\ge 80\%$) with transparent labeling (`Brand recognized`, `Generic`, `Match type: Exact` / `Fuzzy / High confidence`), avoiding misleading "100% Match" claims.
9. **Deterministic Interaction Matching**: Symmetrical, order-independent lookup screens pairs against curated clinical interaction records.
10. **Plain-Language Explanations**: Patients receive clear risk summaries, severity classifications, and direct instructions to consult their pharmacist.

---

## 3. Architecture Overview

```mermaid
flowchart TD
    A[Live Camera Feed / Webcam] --> B[WebRTC Local Loopback Stream\niceServers: []]
    B --> C[Real-Time OpenCV Framing Heuristics\nGlare, Occupancy, Centering, Stability]
    C --> D[Target Held Steady >= 0.8s\nAutomatic Capture Triggered]
    D --> E[Review Screen: Exactly Two Buttons\n[✓ Use Photo] or [↻ Retake]]
    E -- Retake --> B
    E -- Use Photo --> F[In-Memory RAM Frame Buffer\nZero Disk Persistence]
    F --> G[Computer Vision Preprocessing\nCLAHE & Sharpening]
    G --> H[Local EasyOCR Engine\nStrictly Offline Weights]
    H --> I[Packaging Noise Cleaner\nBatch, Expiry, Dosage Stripping]
    I --> J[Medicine Normalizer\nBrand-to-Generic + RapidFuzz]
    J --> K{Both Recognized?}
    K -- No --> L[State C: Medicine Not Recognized\nNever Marked Safe]
    K -- Yes --> M[Deterministic Interaction Engine\nSymmetric Pair Lookup]
    M --> N{Interaction Found?}
    N -- Yes --> O[State A: Potential Interaction Detected\nWhy It Matters + Pharmacist Advice]
    N -- No --> P[State B: No Known Interaction\nExplicit Local Dataset Limitation Notice]
```

---

## 4. Technology Stack

- **Language & Runtime**: Python 3.10+ (Tested on Python 3.11 Windows 64-bit)
- **User Interface**: Streamlit (Custom responsive healthcare theme, accessible contrast)
- **Live Camera Streaming**: `streamlit-webrtc` (Configured with `iceServers: []`) & `av`
- **Computer Vision & Preprocessing**: OpenCV (`opencv-python`), Pillow (`PIL`)
- **Offline OCR Engine**: EasyOCR (`easyocr` running with `download_enabled=False` on PyTorch)
- **Fuzzy String Matching**: RapidFuzz (`token_sort_ratio`)
- **Testing & Validation**: Pytest

---

## 5. Project Directory Structure

```
medguard/
├── app.py                      # Main Streamlit application entry point
├── requirements.txt            # Pinned dependencies
├── README.md                   # Comprehensive documentation
├── .gitignore                  # Git exclusions
│
├── config/
│   └── settings.py             # Centralized paths, thresholds, and demo presets
│
├── data/
│   ├── interactions.json       # 25 curated, clinically documented drug pairs
│   ├── brand_generic_map.json  # 69 Indian & global brand-to-generic mappings
│   └── README.md               # Dataset documentation and provenance
│
├── models/
│   └── easyocr/                # Pre-downloaded offline weights
│       ├── craft_mlt_25k.pth   # 79.30 MB CRAFT detector
│       └── english_g2.pth      # 14.44 MB English recognizer
│
├── src/
│   ├── __init__.py
│   ├── ocr/
│   │   ├── __init__.py
│   │   ├── engine.py           # Offline EasyOCR wrapper (download_enabled=False)
│   │   ├── framing_guide.py    # Assistive OpenCV framing heuristics & reticle overlay
│   │   └── preprocessing.py    # CLAHE, bicubic scaling, sharpening
│   ├── normalization/
│   │   ├── __init__.py
│   │   ├── normalizer.py       # Brand-to-generic resolution & multi-token scanning
│   │   └── fuzzy_matcher.py    # Conservative RapidFuzz scoring
│   ├── interaction/
│   │   ├── __init__.py
│   │   ├── engine.py           # Order-independent symmetric matching engine
│   │   └── models.py           # InteractionResult, Status & Severity dataclasses
│   ├── explanation/
│   │   ├── __init__.py
│   │   └── formatter.py        # Rule-based plain-language explanation formatter
│   ├── privacy/
│   │   ├── __init__.py
│   │   └── image_handler.py    # Ephemeral RAM buffer (zero disk persistence)
│   └── utils/
│       ├── __init__.py
│       └── text_utils.py       # Packaging noise, batch, and dosage regex cleaner
│
├── ui/
│   ├── __init__.py
│   ├── camera_stream.py        # WebRTC live camera streamer with in-memory capture
│   ├── styles.py               # Healthcare CSS design system
│   ├── components.py           # Reusable status pills, scan cards, result views
│   └── screens.py              # Screen coordinator & Demo Mode manager
│
├── tests/
│   ├── __init__.py
│   ├── test_framing_guide.py   # Assistive framing heuristics & reticle tests
│   ├── test_normalization.py   # Exact, fuzzy, and unrecognized drug tests
│   ├── test_interaction_engine.py # Symmetrical pair tests, State A/B/C verification
│   ├── test_text_utils.py      # Noise removal and candidate extraction tests
│   └── test_privacy.py         # Zero disk persistence verification
│
├── scripts/
│   ├── download_models.py      # One-time setup script to pre-fetch EasyOCR weights
│   ├── validate_data.py        # Dataset syntax, schema, and uniqueness validator
│   └── run_tests.py            # Pytest test execution runner
│
└── assets/
    └── demo/
        ├── README.md           # Instructions for capturing sample packaging photos
        ├── sample_ecosprin.png # Sample blister pack for live upload test
        ├── sample_combiflam.png# Sample blister pack for live upload test
        ├── sample_crocin.png   # Sample blister pack for live upload test
        └── sample_cetzine.png  # Sample blister pack for live upload test
```

---

## 6. Installation & Setup (Windows)

### Step 1: Clone and Navigate to Directory
```powershell
cd "g:\Projects\iQOO Hackathon\medguard"
```

### Step 2: Create and Activate Virtual Environment (Optional but Recommended)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Pre-download Offline OCR Model Weights (One-Time Setup)
To guarantee that the application runs locally without triggering network requests when Wi-Fi is disabled, run the one-time weight preparation script:

```powershell
python scripts/download_models.py
```
This stores the CRAFT detector (`craft_mlt_25k.pth`) and English recognition model (`english_g2.pth`) directly inside `models/easyocr/`.

---

## 7. Running the Application

Launch the prototype with Streamlit:

```powershell
streamlit run app.py
```

The application will immediately open in your default browser at `http://localhost:8501`.

---

## 8. Offline & Privacy Architecture

MedGuard is engineered around absolute local sovereignty:
- **No External WebRTC Services**: MedGuard is configured without external STUN/TURN servers (`rtc_configuration={"iceServers": []}`) and requires no external network service for camera streaming, OCR, normalization, or interaction screening.
- **Zero Cloud APIs**: No OpenAI, Gemini, Claude, Firebase, or remote endpoints.
- **Zero Continuous OCR Overhead**: Live video callbacks only perform lightweight OpenCV geometric framing (<2ms). Deep character recognition runs **only** after the user confirms a photo via `✓ Use Photo`.
- **Zero Image Disk Persistence**: Neither live camera frames nor uploaded packaging photos are ever written to disk, temporary folders, or databases. Images reside strictly in volatile RAM and are released immediately after feature extraction.
- **Encrypted-at-Rest Local History**: When users explicitly choose to save a prescription, only structured text (brand and generic drug names) is stored locally on-device in `data/prescription_history.json`. This history file is encrypted at rest using a locally-generated key file (`data/.history.key` via `cryptography.fernet`) and is never transmitted anywhere.
- **Persistent Offline Indicator**: The header prominently displays `● OFFLINE · LOCAL PROCESSING`.

---

## 9. Local Datasets & Provenance

MedGuard utilizes two local, curated datasets located in `data/`:
1. **`brand_generic_map.json`**: 182 verified commercial brand names and active ingredient formulations mapped to canonical generic compounds (e.g., *Crocin* &rarr; *paracetamol*, *Combiflam* &rarr; *ibuprofen*, *Ecosprin* &rarr; *aspirin*, *Pan-D* &rarr; *pantoprazole*, *Unienzyme* &rarr; *fungal diastase + papain + activated charcoal*, *DGL* &rarr; *deglycyrrhizinated licorice*).
2. **`interactions.json`**: 25 clinically documented high-risk interaction pairs.

### Provenance Notice
Every record has been cross-referenced against authoritative clinical pharmacology references:
- **British National Formulary (BNF 84)**
- **FDA Drug Safety Communications & Package Inserts**
- **Stockley's Drug Interactions**
- **American Heart Association (AHA) Guidelines**

To validate dataset syntax and deduplication at any time:
```powershell
python scripts/validate_data.py
```

---

## 10. Automated Testing

Run the full automated test suite (31 unit, stability, and invariant tests):

```powershell
python scripts/run_tests.py
```
or directly via pytest:
```powershell
python -m pytest tests/ -v
```

All 31 tests verify:
- Invariant: Automatic capture produces review frame with **0 OCR calls**; OCR is called **1 time** only after `✓ Use Photo`.
- Assistive OpenCV framing heuristics (glare detection, occupancy, centering, stability drift, and reticle overlay).
- Single-trigger auto-capture guard and Retake state restoration.
- Exact and fuzzy brand normalization without misleading "100% Match" claims.
- Symmetrical order independence: `check(A, B) == check(B, A)`.
- Isolation of unrecognized drugs (unrecognized drugs **never** yield "no interaction").
- In-memory lifecycle and zero disk persistence.
- Regex packaging noise removal.

---

## 11. Recommended 2–3 Minute Demo Walkthrough Video Script

When recording your prototype walkthrough video for the iQOO Hackathon submission:

| Step | Action | On-Screen Demonstration | Narration Talking Point |
| :--- | :--- | :--- | :--- |
| **1. Hook & Positioning** | Open `http://localhost:8501` | Show the hero header, `● OFFLINE · LOCAL PROCESSING` indicator, and camera stand-in note. | *"MedGuard is an offline, camera-first medication interaction checker built to protect patients and caregivers managing polypharmacy."* |
| **2. Privacy Guarantee** | Scroll briefly over header | Highlight the local processing pill and in-memory reassurance. | *"Because health data privacy is paramount, zero frames leave this device. All processing happens in local memory with no external servers."* |
| **3. Live Camera Preview** | Look at the **Scan Medicine 1** card | Show the live webcam stream, the centered scanning reticle, and real-time positioning tips. | *"MedGuard displays a real-time camera preview with an assistive scan reticle to guide physical packaging into optimal view."* |
| **4. Automatic Capture (Hold Steady)** | Hold a medicine strip inside the reticle for 0.8s | Reticle updates to `✓ Hold steady...` and automatically captures without requiring a manual button press. | *"Notice how the user does not need to press a button while balancing a strip. When held steady for 0.8 seconds, MedGuard automatically captures the frame."* |
| **5. Review Screen Confirmation** | Show the **Review your scan** screen with photo and exactly two buttons (`[ ✓ Use Photo ]`, `[ ↻ Retake ]`) | Highlight that OCR has not run yet. Click **✓ Use Photo**. | *"Before any OCR runs, the user verifies text clarity. Clicking 'Use Photo' runs our local EasyOCR and normalization engine in volatile RAM."* |
| **6. Defensible Identification** | Point to the recognized medicine pill | Displays `Brand recognized: Ecosprin | Generic: Aspirin | Match type: Exact`. | *"MedGuard clearly distinguishes brand from active compound with transparent confidence labeling, avoiding misleading clinical certainty claims."* |
| **7. Retake Demo** | Click **🔄 Retake** | Returns cleanly to the live camera preview without reloading Streamlit. | *"Caregivers can retake at any time with a single click."* |
| **8. Fast Walkthrough: Scenario 1 (Interaction)** | Open **Mode Selection**, select **Demo: Potential Interaction**, click **Check Interaction**. | Screen displays **State A (Red Card)**: `ASPIRIN + IBUPROFEN`, highlighting bleeding risk, mechanism, and pharmacist confirmation advice. | *"When checking Ecosprin and Combiflam, MedGuard flags the gastrointestinal bleeding risk and blunted cardioprotection, urging pharmacist consultation."* |
| **9. Scenario 2 (No Known Interaction)** | Reset, select **Demo: No Known Interaction**, click **Check Interaction**. | Screen displays **State B (Blue Card)**: `PARACETAMOL + CETIRIZINE` with explicit local dataset limitation note. | *"For Crocin and Cetzine, MedGuard transparently confirms no known interaction in our dataset without falsely claiming universal safety."* |
| **10. Scenario 3 (Unrecognized Medicine)** | Reset, select **Demo: Unrecognized Medicine**, click **Check Interaction**. | Screen displays **State C (Amber Card)**: `Medicine not recognized`. | *"If a medicine cannot be confidently identified, MedGuard refuses to guess. An unknown drug is NEVER marked safe."* |

---

## 12. Safety Framing & Prototype Limitations

- **Screening Tool Only**: MedGuard is a decision-support prototype, not a diagnostic system. It does not recommend dosages, alter prescriptions, or provide clinical diagnoses.
- **Assistive Framing Heuristic**: The OpenCV framing overlay is a positioning aid, not an object detector or medical classifier. It never blocks capture.
- **Curated Prototype Scope**: The database contains 25 curated demonstration pairs. Absence of an interaction record does **not** prove two drugs are safe together.
- **Physical Packaging Variance**: Extreme foil glare or heavily creased packaging may require angling or manual name entry.
- **Formulation Scope**: Ayurvedic, homeopathic, and unstandardized herbal preparations are outside current prototype coverage.

---

## 13. Roadmap: Porting to Android & On-Device Phone Hardware

This laptop prototype establishes the camera-first pipeline. The final hackathon implementation will be ported directly to an Android smartphone:

```
[Laptop Prototype]                         [Android On-Device Target]
Streamlit & streamlit-webrtc ───────►      Native Android Jetpack Compose CameraX View
OpenCV CLAHE & Framing       ───────►      On-Device GPU Image Pipeline
EasyOCR Engine               ───────►      Google ML Kit On-Device Text Recognition
rapidfuzz Normalizer         ───────►      Kotlin / C++ Fuzzy Token Matcher
Local JSON Databases         ───────►      Room SQLite Encrypted Database
Local Explanation Layer      ───────►      Deterministic Android ViewModels
```

---

## 14. Hackathon Evaluation Notice

*Developed for the iQOO Hackathon 2026 HealthTech track. All code, datasets, and intellectual property remain with the author for competition evaluation.*
