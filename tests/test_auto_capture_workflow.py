"""
Unit and behavioral tests for MedGuard's Automatic Capture Workflow.
Verifies framing stability heuristics, single-trigger guards, atomic handoff,
defensible recognition copy, and the critical invariant:
automatic capture -> review frame exists -> OCR count == 0;
Use Photo -> OCR count == 1.
"""
from unittest.mock import MagicMock, patch
import av
import numpy as np
import pytest

from config.settings import AUTO_CAPTURE_STABILITY_SECONDS
from src.ocr.framing_guide import (
    FramingState,
    compute_scan_zone,
    is_target_stable,
)
from src.normalization.normalizer import DrugMatchResult
from ui.camera_stream import CaptureState, FramingVideoProcessor


def _make_frame_with_target(w: int = 640, h: int = 480, shift_x: int = 0, shift_y: int = 0) -> np.ndarray:
    """Creates a synthetic frame containing a well-centered, high-contrast mock medicine strip."""
    frame = np.full((h, w, 3), 40, dtype=np.uint8)
    x1, y1, x2, y2 = compute_scan_zone(w, h)
    zw = x2 - x1
    zh = y2 - y1

    pad_x = int(zw * 0.2)
    pad_y = int(zh * 0.2)
    # Draw simulated medicine packaging rectangle
    bx1 = x1 + pad_x + shift_x
    by1 = y1 + pad_y + shift_y
    bx2 = x2 - pad_x + shift_x
    by2 = y2 - pad_y + shift_y
    frame[by1:by2, bx1:bx2] = 215
    return frame


def test_target_stability_heuristic():
    """Verifies that is_target_stable tolerates micro-jitter but rejects large sudden movements."""
    w, h = 640, 480
    base_box = (150, 150, 450, 330)

    # Micro-jitter within 5% diagonal drift and 15% area variance
    slight_jitter_box = (152, 151, 451, 331)
    assert is_target_stable(base_box, slight_jitter_box, w, h) is True

    # Large sudden displacement (> 5% of diagonal = ~40px)
    displaced_box = (220, 150, 520, 330)
    assert is_target_stable(base_box, displaced_box, w, h) is False

    # Large area expansion (> 15%)
    expanded_box = (120, 120, 480, 360)
    assert is_target_stable(base_box, expanded_box, w, h) is False


def test_processor_auto_capture_lifecycle():
    """Verifies transition from SCANNING -> HOLD_STEADY -> CAPTURED upon elapsed stability."""
    proc = FramingVideoProcessor()
    assert proc.capture_state == CaptureState.SCANNING

    frame_arr = _make_frame_with_target()
    v_frame = av.VideoFrame.from_ndarray(frame_arr, format="bgr24")

    # Wrap entire temporal sequence in mock_time to track elapsed stability cleanly
    with patch("time.time") as mock_time:
        base_t = 1000.0

        # Frame 1: initial detection
        mock_time.return_value = base_t
        proc.recv(v_frame)
        assert proc.current_framing_state == FramingState.GOOD_POSITION
        assert proc.capture_state == CaptureState.HOLD_STEADY
        assert proc.take_pending_capture() is None

        # Elapsed < threshold (0.3s < 0.8s)
        mock_time.return_value = base_t + 0.3
        proc.recv(v_frame)
        assert proc.capture_state == CaptureState.HOLD_STEADY
        assert proc.take_pending_capture() is None

        # Elapsed >= threshold (>= 0.8s) -> CAPTURED
        mock_time.return_value = base_t + AUTO_CAPTURE_STABILITY_SECONDS + 0.05
        proc.recv(v_frame)
        assert proc.capture_state == CaptureState.CAPTURED

        # Atomic handoff
        pending = proc.take_pending_capture()
        assert pending is not None
        assert isinstance(pending, np.ndarray)
        assert proc.capture_state == CaptureState.REVIEW


def test_single_trigger_guard():
    """Verifies that subsequent video frames do NOT overwrite or retrigger an active capture."""
    proc = FramingVideoProcessor()
    frame1 = _make_frame_with_target(shift_x=0)
    frame2 = _make_frame_with_target(shift_x=5)

    with patch("time.time") as mock_time:
        mock_time.return_value = 100.0
        proc.recv(av.VideoFrame.from_ndarray(frame1, format="bgr24"))

        mock_time.return_value = 100.0 + AUTO_CAPTURE_STABILITY_SECONDS + 0.1
        proc.recv(av.VideoFrame.from_ndarray(frame1, format="bgr24"))
        assert proc.capture_state == CaptureState.CAPTURED

        captured1 = proc.take_pending_capture()
        assert captured1 is not None

        # Feed frame2 while in REVIEW state
        mock_time.return_value = 100.0 + AUTO_CAPTURE_STABILITY_SECONDS + 1.0
        proc.recv(av.VideoFrame.from_ndarray(frame2, format="bgr24"))

        # State should remain REVIEW, never re-triggering fresh capture
        assert proc.capture_state == CaptureState.REVIEW


def test_retake_resets_processor():
    """Verifies that reset_capture cleanly restores SCANNING state."""
    proc = FramingVideoProcessor()
    frame = _make_frame_with_target()

    with patch("time.time") as mock_time:
        mock_time.return_value = 10.0
        proc.recv(av.VideoFrame.from_ndarray(frame, format="bgr24"))
        mock_time.return_value = 10.0 + AUTO_CAPTURE_STABILITY_SECONDS + 0.1
        proc.recv(av.VideoFrame.from_ndarray(frame, format="bgr24"))
        assert proc.capture_state == CaptureState.CAPTURED

        # Call reset
        proc.reset_capture()
        assert proc.capture_state == CaptureState.SCANNING
        assert proc.take_pending_capture() is None


def test_capture_does_not_invoke_ocr():
    """
    CRITICAL BEHAVIORAL INVARIANT TEST:
    Verifies that:
      1. Automatic capture occurs and creates a review frame.
      2. OCR call count == 0 while in the review state.
      3. OCR call count == 1 only after user confirms by invoking 'Use Photo'.
    """
    proc = FramingVideoProcessor()
    target_frame = _make_frame_with_target()

    # Create mock OCR engine
    mock_ocr = MagicMock()
    mock_ocr.extract_text.return_value = MagicMock(success=True, raw_text="ECOSPRIN 75")

    with patch("ui.screens.get_ocr_engine", return_value=mock_ocr):
        # Step 1: Video frames arrive and auto-capture triggers
        with patch("time.time") as mock_time:
            mock_time.return_value = 50.0
            proc.recv(av.VideoFrame.from_ndarray(target_frame, format="bgr24"))

            mock_time.return_value = 50.0 + AUTO_CAPTURE_STABILITY_SECONDS + 0.1
            proc.recv(av.VideoFrame.from_ndarray(target_frame, format="bgr24"))

        # Step 2: Auto-capture completed, review frame exists
        assert proc.capture_state == CaptureState.CAPTURED
        review_frame = proc.take_pending_capture()
        assert review_frame is not None

        # CRITICAL CHECK: OCR has NOT been called at all during capture!
        assert mock_ocr.extract_text.call_count == 0

        # Step 3: User confirms by pressing "✓ Use Photo" (which triggers process_image_input)
        from ui.screens import process_image_input
        result = process_image_input(review_frame)

        # CRITICAL CHECK: OCR is invoked exactly once upon confirmation!
        assert mock_ocr.extract_text.call_count == 1
        assert result is not None
        assert result.recognized is True
        assert result.generic_name == "aspirin"


def test_medicine_recognition_copy_no_clinical_certainty():
    """Verifies that recognition copy excludes '100% Match' and uses defensible labeling."""
    drug = DrugMatchResult(
        raw_query="Ecosprin 75",
        recognized=True,
        generic_name="aspirin",
        brand_name="Ecosprin",
        confidence=100.0,
        match_type="exact_brand",
    )

    with patch("streamlit.html") as mock_html:
        from ui.components import render_detected_medicine_card
        render_detected_medicine_card(drug, "Medicine 1")

        mock_html.assert_called_once()
        rendered_html = mock_html.call_args[0][0]

        # Must NOT claim 100% Match
        assert "100% Match" not in rendered_html
        assert "100%" not in rendered_html

        # Must include defensible copy
        assert "Brand recognized:" in rendered_html
        assert "Generic:" in rendered_html
        assert "Match type: Exact" in rendered_html
