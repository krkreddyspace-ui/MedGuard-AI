"""
MedGuard - Pre-download EasyOCR model weights for 100% offline execution.
Run this script once with network access to populate models/easyocr/.
At runtime, MedGuard runs strictly with download_enabled=False and zero network access.
"""
import sys
import os
from pathlib import Path

# Force UTF-8 on Windows console to prevent charmap codec errors with progress bars
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import EASYOCR_MODEL_DIR


def download_models():
    print("=" * 60)
    print("MedGuard: Pre-fetching EasyOCR offline model weights")
    print(f"Target Directory: {EASYOCR_MODEL_DIR.resolve()}")
    print("=" * 60)

    EASYOCR_MODEL_DIR.mkdir(parents=True, exist_ok=True)

    try:
        import easyocr
    except ImportError:
        print("[ERROR] easyocr is not installed. Please run: pip install easyocr")
        sys.exit(1)

    print("Downloading EasyOCR model weights (craft and english recognizer)...")
    try:
        # download_enabled=True only during this offline prep step
        reader = easyocr.Reader(
            ["en"],
            gpu=False,
            model_storage_directory=str(EASYOCR_MODEL_DIR),
            download_enabled=True,
            verbose=False,
        )
        print("\n[SUCCESS] Model weights successfully downloaded to:")
        for f in sorted(EASYOCR_MODEL_DIR.iterdir()):
            if f.is_file():
                print(f"  - {f.name} ({f.stat().st_size / (1024 * 1024):.2f} MB)")
        print("\nMedGuard can now run completely offline with Wi-Fi disabled.")
    except Exception as e:
        print(f"[ERROR] Failed to download model weights: {e}")
        sys.exit(1)


if __name__ == "__main__":
    download_models()
