"""
MedGuard - Offline Medication Interaction Checker
Laptop prototype for iQOO Hackathon 2026 HealthTech track.
"""
import sys
from pathlib import Path
import streamlit as st

# Ensure repository root is on Python module search path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ui.screens import render_main_app
from ui.styles import CUSTOM_CSS


def main():
    st.set_page_config(
        page_title="MedGuard · Offline Drug Interaction Checker",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Inject neumorphic visual styling
    st.html(CUSTOM_CSS)

    # Render primary application workflow
    render_main_app()


if __name__ == "__main__":
    main()
