"""
MedGuard - Assistive Camera Framing Guide & Stability Heuristics
Provides real-time, lightweight OpenCV camera positioning feedback and target stability estimation.
NOTE: This is NOT a machine learning object detector or medicine classifier.
It is an assistive positioning aid estimating target occupancy, centering, foil glare, and temporal stability.
"""
from enum import Enum
from typing import Optional, Tuple
import cv2
import numpy as np

from config.settings import (
    FRAMING_GUIDANCE_COPY,
    GLARE_AREA_RATIO_MAX,
    GLARE_LUMINANCE_CUTOFF,
    MAX_CENTER_DEVIATION,
    MIN_OCCUPANCY_RATIO,
    SCAN_ZONE_HEIGHT_RATIO,
    SCAN_ZONE_WIDTH_RATIO,
    STABILITY_MAX_AREA_DRIFT,
    STABILITY_MAX_CENTROID_DRIFT,
)


class FramingState(str, Enum):
    """Spatial/geometric camera positioning feedback states."""
    NO_OBJECT = "NO_OBJECT"
    TOO_FAR = "TOO_FAR"
    OFF_CENTER = "OFF_CENTER"
    PARTIALLY_OUT = "PARTIALLY_OUT"
    GLARE = "GLARE"
    GOOD_POSITION = "GOOD_POSITION"


def compute_scan_zone(frame_w: int, frame_h: int) -> Tuple[int, int, int, int]:
    """
    Computes coordinates (x1, y1, x2, y2) of the central rectangular scan zone.
    """
    zw = int(frame_w * SCAN_ZONE_WIDTH_RATIO)
    zh = int(frame_h * SCAN_ZONE_HEIGHT_RATIO)
    x1 = (frame_w - zw) // 2
    y1 = (frame_h - zh) // 2
    x2 = x1 + zw
    y2 = y1 + zh
    return x1, y1, x2, y2


def analyze_framing(frame_bgr: np.ndarray) -> Tuple[FramingState, str, dict]:
    """
    Evaluates real-time camera framing using fast, classical OpenCV operations (<2ms).

    Returns:
        tuple (FramingState, guidance_message, debug_metrics)
        where debug_metrics contains 'box': (gx1, gy1, gx2, gy2) if a candidate feature is found.
    """
    h, w = frame_bgr.shape[:2]
    zx1, zy1, zx2, zy2 = compute_scan_zone(w, h)
    zone_area = (zx2 - zx1) * (zy2 - zy1)
    zone_cx = (zx1 + zx2) / 2.0
    zone_cy = (zy1 + zy2) / 2.0

    # 1. Evaluate Specular Glare in the scan zone (critical for shiny foil packaging)
    zone_bgr = frame_bgr[zy1:zy2, zx1:zx2]
    gray_zone = cv2.cvtColor(zone_bgr, cv2.COLOR_BGR2GRAY)
    glare_pixels = np.count_nonzero(gray_zone >= GLARE_LUMINANCE_CUTOFF)
    glare_ratio = glare_pixels / float(zone_area)

    if glare_ratio > GLARE_AREA_RATIO_MAX:
        return (
            FramingState.GLARE,
            FRAMING_GUIDANCE_COPY["GLARE"],
            {"glare_ratio": glare_ratio, "box": None},
        )

    # 2. Downsample for fast edge detection and contour extraction
    scale = 0.5
    small_gray = cv2.resize(gray_zone, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    blurred = cv2.GaussianBlur(small_gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 40, 120)

    # Dilate edges to bridge gaps in packaging borders and printed text
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated = cv2.dilate(edges, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter significant contours
    min_contour_area = (small_gray.shape[0] * small_gray.shape[1]) * 0.03
    significant = [c for c in contours if cv2.contourArea(c) > min_contour_area]

    if not significant:
        return (
            FramingState.NO_OBJECT,
            FRAMING_GUIDANCE_COPY["NO_OBJECT"],
            {"contours_found": 0, "box": None},
        )

    # Merge bounding boxes of significant features
    all_points = np.vstack(significant)
    bx, by, bw, bh = cv2.boundingRect(all_points)

    # Scale back to original scan zone coordinates
    orig_bx = int(bx / scale)
    orig_by = int(by / scale)
    orig_bw = int(bw / scale)
    orig_bh = int(bh / scale)

    # Global coordinates in the camera frame
    gx1 = zx1 + orig_bx
    gy1 = zy1 + orig_by
    gx2 = gx1 + orig_bw
    gy2 = gy1 + orig_bh

    target_area = orig_bw * orig_bh
    occupancy = target_area / float(zone_area)
    target_box = (gx1, gy1, gx2, gy2)

    # 3. Check Occupancy: Target too small / far
    if occupancy < MIN_OCCUPANCY_RATIO:
        return (
            FramingState.TOO_FAR,
            FRAMING_GUIDANCE_COPY["TOO_FAR"],
            {"occupancy": occupancy, "box": target_box},
        )

    # 4. Check Boundary Clipping: Target extends outside scan zone
    margin_x = int((zx2 - zx1) * 0.04)
    margin_y = int((zy2 - zy1) * 0.04)
    if (gx1 <= zx1 + margin_x or gx2 >= zx2 - margin_x or
        gy1 <= zy1 + margin_y or gy2 >= zy2 - margin_y):
        return (
            FramingState.PARTIALLY_OUT,
            FRAMING_GUIDANCE_COPY["PARTIALLY_OUT"],
            {"occupancy": occupancy, "box": target_box},
        )

    # 5. Check Centering Deviation
    target_cx = (gx1 + gx2) / 2.0
    target_cy = (gy1 + gy2) / 2.0
    norm_dx = abs(target_cx - zone_cx) / float(zx2 - zx1)
    norm_dy = abs(target_cy - zone_cy) / float(zy2 - zy1)
    max_dev = max(norm_dx, norm_dy)

    if max_dev > MAX_CENTER_DEVIATION:
        return (
            FramingState.OFF_CENTER,
            FRAMING_GUIDANCE_COPY["OFF_CENTER"],
            {"deviation": max_dev, "box": target_box},
        )

    # 6. Good Position
    return (
        FramingState.GOOD_POSITION,
        FRAMING_GUIDANCE_COPY["GOOD_POSITION"],
        {"occupancy": occupancy, "deviation": max_dev, "glare_ratio": glare_ratio, "box": target_box},
    )


def is_target_stable(
    prev_box: Optional[Tuple[int, int, int, int]],
    curr_box: Optional[Tuple[int, int, int, int]],
    frame_w: int,
    frame_h: int,
) -> bool:
    """
    Evaluates whether the scan target has remained stationary between consecutive frames.
    Checks normalized centroid drift and bounding area variance against configured tolerances.
    """
    if prev_box is None or curr_box is None:
        return False

    # Centroid drift
    prev_cx = (prev_box[0] + prev_box[2]) / 2.0
    prev_cy = (prev_box[1] + prev_box[3]) / 2.0
    curr_cx = (curr_box[0] + curr_box[2]) / 2.0
    curr_cy = (curr_box[1] + curr_box[3]) / 2.0

    centroid_dist = np.sqrt((curr_cx - prev_cx) ** 2 + (curr_cy - prev_cy) ** 2)
    diag = np.sqrt(frame_w ** 2 + frame_h ** 2)
    normalized_drift = centroid_dist / max(1.0, diag)

    if normalized_drift > STABILITY_MAX_CENTROID_DRIFT:
        return False

    # Area drift
    prev_area = max(1, (prev_box[2] - prev_box[0]) * (prev_box[3] - prev_box[1]))
    curr_area = max(1, (curr_box[2] - curr_box[0]) * (curr_box[3] - curr_box[1]))
    area_delta = abs(curr_area - prev_area) / float(prev_area)

    if area_delta > STABILITY_MAX_AREA_DRIFT:
        return False

    return True


def draw_reticle_corner(
    img: np.ndarray,
    pt: Tuple[int, int],
    dx: int,
    dy: int,
    color: Tuple[int, int, int],
    thickness: int = 3,
):
    """Draws an L-shaped reticle corner accent."""
    x, y = pt
    cv2.line(img, (x, y), (x + dx, y), color, thickness)
    cv2.line(img, (x, y), (x, y + dy), color, thickness)


def render_guidance_overlay(
    frame_bgr: np.ndarray,
    state: FramingState,
    message: Optional[str] = None,
    is_holding_steady: bool = False,
) -> np.ndarray:
    """
    Renders the central rectangular scanning zone and assistive guidance badge
    directly onto the video frame with distinct visual feedback per heuristic state.
    """
    annotated = frame_bgr.copy()
    h, w = annotated.shape[:2]
    x1, y1, x2, y2 = compute_scan_zone(w, h)
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

    is_holding = is_holding_steady or ("hold steady" in (message or "").lower()) or ("captured" in (message or "").lower())

    # 1. Color mapping and state-specific accent setup
    if is_holding:
        accent_color = (129, 185, 16)   # Vibrant Emerald Green BGR
    elif state == FramingState.GOOD_POSITION:
        accent_color = (94, 197, 34)    # Green BGR
    elif state == FramingState.GLARE:
        accent_color = (30, 160, 245)   # Amber / Orange for Glare
    elif state in (FramingState.TOO_FAR, FramingState.OFF_CENTER, FramingState.PARTIALLY_OUT):
        accent_color = (40, 150, 245)   # Amber BGR
    else:
        accent_color = (220, 200, 30)   # Cyan / Teal BGR

    # 2. Semi-transparent darkened outer vignetting
    overlay = annotated.copy()
    cv2.rectangle(overlay, (0, 0), (w, y1), (15, 23, 42), -1)
    cv2.rectangle(overlay, (0, y2), (w, h), (15, 23, 42), -1)
    cv2.rectangle(overlay, (0, y1), (x1, y2), (15, 23, 42), -1)
    cv2.rectangle(overlay, (x2, y1), (w, y2), (15, 23, 42), -1)
    cv2.addWeighted(overlay, 0.35, annotated, 0.65, 0, annotated)

    # 3. Heuristic State Specific Reticle Visual Feedback
    if state == FramingState.GLARE:
        # Amber pulsing double-border for specular glare
        cv2.rectangle(annotated, (x1 - 4, y1 - 4), (x2 + 4, y2 + 4), (30, 160, 245), 2)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 200, 255), 1)
    elif is_holding:
        # "Locking in" contracted reticle frame
        cv2.rectangle(annotated, (x1, y1), (x2, y2), accent_color, 2)
        cv2.rectangle(annotated, (x1 + 8, y1 + 8), (x2 - 8, y2 - 8), (255, 255, 255), 1)
    else:
        border_thick = 2 if state == FramingState.GOOD_POSITION else 1
        cv2.rectangle(annotated, (x1, y1), (x2, y2), accent_color, border_thick)

    # Centering crosshair guide ticks
    tick_len = 10
    cv2.line(annotated, (cx, y1), (cx, y1 + tick_len), accent_color, 2)
    cv2.line(annotated, (cx, y2), (cx, y2 - tick_len), accent_color, 2)
    cv2.line(annotated, (x1, cy), (x1 + tick_len, cy), accent_color, 2)
    cv2.line(annotated, (x2, cy), (x2 - tick_len, cy), accent_color, 2)

    # Corner reticles
    corner_len = 28 if is_holding else 24
    t = 4 if is_holding else 3
    draw_reticle_corner(annotated, (x1, y1), corner_len, corner_len, accent_color, t)
    draw_reticle_corner(annotated, (x2, y1), -corner_len, corner_len, accent_color, t)
    draw_reticle_corner(annotated, (x1, y2), corner_len, -corner_len, accent_color, t)
    draw_reticle_corner(annotated, (x2, y2), -corner_len, -corner_len, accent_color, t)

    # 4. Status Pill Message
    display_msg = message or FRAMING_GUIDANCE_COPY.get(state.value, "Position medicine in frame")
    if is_holding and "locking" not in display_msg.lower():
        display_msg = f"🔒 {display_msg}"

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.55
    thickness = 1

    (text_w, text_h), baseline = cv2.getTextSize(display_msg, font, font_scale, thickness)
    pill_px = max(10, (w - text_w) // 2)
    pill_py = max(y1 - 32, 14)

    # Pill background
    pad_x, pad_y = 12, 6
    bg_pt1 = (pill_px - pad_x, pill_py - pad_y)
    bg_pt2 = (pill_px + text_w + pad_x, pill_py + text_h + pad_y)

    cv2.rectangle(annotated, bg_pt1, bg_pt2, (20, 24, 33), -1)
    cv2.rectangle(annotated, bg_pt1, bg_pt2, accent_color, 1)

    # Text inside pill
    text_origin = (pill_px, pill_py + text_h)
    cv2.putText(annotated, display_msg, text_origin, font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

    return annotated
