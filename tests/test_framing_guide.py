"""
Unit tests for OpenCV-based assistive camera framing heuristics.
Ensures framing feedback runs locally and reliably classifies scan positioning.
"""
import numpy as np
from src.ocr.framing_guide import (
    FramingState,
    analyze_framing,
    compute_scan_zone,
    render_guidance_overlay,
)


def _make_base_frame(w: int = 640, h: int = 480, bg_val: int = 40) -> np.ndarray:
    """Creates a neutral background frame."""
    return np.full((h, w, 3), bg_val, dtype=np.uint8)


def test_compute_scan_zone():
    w, h = 640, 480
    x1, y1, x2, y2 = compute_scan_zone(w, h)
    assert 0 < x1 < x2 < w
    assert 0 < y1 < y2 < h
    # Center of scan zone should align with center of frame
    assert abs((x1 + x2) // 2 - (w // 2)) <= 1
    assert abs((y1 + y2) // 2 - (h // 2)) <= 1


def test_no_object_on_blank_frame():
    frame = _make_base_frame()
    state, msg, _ = analyze_framing(frame)
    assert state == FramingState.NO_OBJECT
    assert "Position the medicine" in msg or "frame" in msg.lower()


def test_glare_detection():
    frame = _make_base_frame()
    x1, y1, x2, y2 = compute_scan_zone(640, 480)
    # Flood the center with saturated white glare
    frame[y1:y2, x1:x2] = 255
    state, msg, metrics = analyze_framing(frame)
    assert state == FramingState.GLARE
    assert "glare" in msg.lower()
    assert metrics["glare_ratio"] > 0.5


def test_too_far_small_object():
    frame = _make_base_frame()
    x1, y1, x2, y2 = compute_scan_zone(640, 480)
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    # Draw a very tiny simulated strip (20x15 pixels) in the center
    frame[cy - 8 : cy + 8, cx - 10 : cx + 10] = 220
    state, msg, _ = analyze_framing(frame)
    assert state in (FramingState.TOO_FAR, FramingState.NO_OBJECT)


def test_good_position_centered_object():
    frame = _make_base_frame()
    x1, y1, x2, y2 = compute_scan_zone(640, 480)
    zw = x2 - x1
    zh = y2 - y1

    # Draw a well-sized medicine strip occupying ~50% of the scan zone in the center
    pad_x = int(zw * 0.2)
    pad_y = int(zh * 0.2)
    frame[y1 + pad_y : y2 - pad_y, x1 + pad_x : x2 - pad_x] = 210

    state, msg, _ = analyze_framing(frame)
    assert state == FramingState.GOOD_POSITION
    assert "Good position" in msg


def test_render_guidance_overlay_shape():
    frame = _make_base_frame()
    overlay = render_guidance_overlay(frame, FramingState.GOOD_POSITION, "✓ Ready")
    assert overlay.shape == frame.shape
    assert overlay.dtype == frame.dtype
    # The overlay should modify pixels
    assert not np.array_equal(overlay, frame)
