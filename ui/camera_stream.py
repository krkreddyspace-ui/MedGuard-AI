"""
MedGuard - Live WebRTC Camera Streamer with OpenCV Framing Reticle & Auto-Capture
Runs local browser camera streaming with empty iceServers.
Zero frames are persisted to disk; all frames exist strictly in volatile RAM.
"""
from enum import Enum
import threading
import time
from typing import Optional, Tuple
import av
import numpy as np
import streamlit as st
from streamlit_webrtc import RTCConfiguration, VideoProcessorBase, WebRtcMode, webrtc_streamer

from config.settings import (
    AUTO_CAPTURE_STABILITY_SECONDS,
    FRAMING_RECOMMENDATION_TIPS,
    NETWORKING_STATEMENT,
)
from src.ocr.framing_guide import (
    FramingState,
    analyze_framing,
    is_target_stable,
    render_guidance_overlay,
)

# Local WebRTC configuration without external STUN/TURN servers
LOCAL_RTC_CONFIG = RTCConfiguration({"iceServers": []})


class CaptureState(str, Enum):
    """Temporal lifecycle states for automatic scanning and capture handoff."""
    SCANNING = "SCANNING"
    HOLD_STEADY = "HOLD_STEADY"
    CAPTURED = "CAPTURED"
    REVIEW = "REVIEW"
    PROCESSING = "PROCESSING"


class FramingVideoProcessor(VideoProcessorBase):
    """
    In-memory video frame processor.
    Performs fast (<2ms) OpenCV framing analysis and stability tracking.
    When a scan target is stably held (>= 0.8s), automatically captures
    the raw BGR frame and holds it in memory for Streamlit handoff.
    Never runs OCR in this callback.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._latest_raw_frame: Optional[np.ndarray] = None
        self._current_framing_state: FramingState = FramingState.NO_OBJECT
        self._current_message: str = "Position medicine in frame"
        self._capture_state: CaptureState = CaptureState.SCANNING
        self._prev_box: Optional[Tuple[int, int, int, int]] = None
        self._stable_start_time: Optional[float] = None
        self._captured_frame: Optional[np.ndarray] = None
        self._handoff_complete: bool = False

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        """Video frame callback. Never calls EasyOCR; only runs lightweight framing heuristics."""
        raw_bgr = frame.to_ndarray(format="bgr24")
        h, w = raw_bgr.shape[:2]
        now = time.time()

        with self._lock:
            self._latest_raw_frame = raw_bgr.copy()

            # If already captured and waiting for review/processing, freeze reticle feedback
            if self._capture_state in (CaptureState.CAPTURED, CaptureState.REVIEW, CaptureState.PROCESSING):
                annotated_bgr = render_guidance_overlay(
                    raw_bgr,
                    FramingState.GOOD_POSITION,
                    "✓ Scan captured! Reviewing photo...",
                )
                return av.VideoFrame.from_ndarray(annotated_bgr, format="bgr24")

            # 1. Spatial framing evaluation
            f_state, f_msg, metrics = analyze_framing(raw_bgr)
            self._current_framing_state = f_state
            curr_box = metrics.get("box")

            # 2. Temporal stability evaluation
            if f_state == FramingState.GOOD_POSITION and curr_box is not None:
                if self._prev_box is not None and is_target_stable(self._prev_box, curr_box, w, h):
                    if self._stable_start_time is None:
                        self._stable_start_time = now

                    elapsed = now - self._stable_start_time
                    if elapsed >= AUTO_CAPTURE_STABILITY_SECONDS:
                        # AUTOMATIC CAPTURE TRIGGERED (Single trigger event)
                        self._capture_state = CaptureState.CAPTURED
                        self._captured_frame = raw_bgr.copy()
                        self._handoff_complete = False
                        f_msg = "✓ Scan captured! Reviewing photo..."
                    else:
                        self._capture_state = CaptureState.HOLD_STEADY
                        rem = max(0.0, AUTO_CAPTURE_STABILITY_SECONDS - elapsed)
                        f_msg = f"✓ Hold steady... {rem:.1f}s"
                else:
                    self._stable_start_time = now
                    self._capture_state = CaptureState.HOLD_STEADY
                    f_msg = "✓ Hold steady..."
                self._prev_box = curr_box
            else:
                self._stable_start_time = None
                self._prev_box = None
                self._capture_state = CaptureState.SCANNING

            self._current_message = f_msg

        annotated_bgr = render_guidance_overlay(raw_bgr, f_state, f_msg)
        return av.VideoFrame.from_ndarray(annotated_bgr, format="bgr24")

    def take_pending_capture(self) -> Optional[np.ndarray]:
        """
        Atomically transfers the captured frame to Streamlit session state.
        Guarantees frame survives until handoff occurs without being prematurely purged.
        """
        with self._lock:
            if self._capture_state in (CaptureState.CAPTURED, CaptureState.REVIEW) and self._captured_frame is not None:
                frame_copy = self._captured_frame.copy()
                self._capture_state = CaptureState.REVIEW
                self._handoff_complete = True
                return frame_copy
            return None

    def reset_capture(self):
        """Resets capture state back to SCANNING when user clicks Retake."""
        with self._lock:
            self._capture_state = CaptureState.SCANNING
            self._captured_frame = None
            self._prev_box = None
            self._stable_start_time = None
            self._handoff_complete = False

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Returns a copy of the latest raw frame held in memory."""
        with self._lock:
            if self._latest_raw_frame is not None:
                return self._latest_raw_frame.copy()
            return None

    @property
    def capture_state(self) -> CaptureState:
        with self._lock:
            return self._capture_state

    @property
    def current_framing_state(self) -> FramingState:
        with self._lock:
            return self._current_framing_state

    @property
    def current_state(self) -> FramingState:
        """Alias for backward compatibility."""
        with self._lock:
            return self._current_framing_state

    @property
    def current_message(self) -> str:
        with self._lock:
            return self._current_message


@st.fragment(run_every="400ms")
def _auto_capture_watcher(ctx, med_idx: int):
    """
    Sub-second reactive watcher polling video processor capture state.
    Executes within an isolated fragment to prevent full-app re-renders
    until an automatic capture is successfully triggered.
    """
    if ctx is not None and ctx.video_processor is not None:
        try:
            if ctx.video_processor.capture_state == CaptureState.CAPTURED:
                frame = ctx.video_processor.take_pending_capture()
                if frame is not None:
                    st.session_state[f"med{med_idx}_review_frame"] = frame
                    st.rerun(scope="app")
        except Exception:
            pass


def render_live_camera_scanner(med_idx: int, label: str):
    """
    Renders the live camera preview with framing guide reticle and automatic capture.
    When a scan target is stably centered (>=0.8s), it automatically captures
    the frame into memory and triggers the review state.
    NO manual 'Capture & Analyze' button is presented.
    """
    st.markdown(
        f"""
        <div style="font-size: 0.95rem; font-weight: 600; color: #1e293b; margin-bottom: 0.2rem;">
            Live Camera Preview ({label})
        </div>
        <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 0.6rem;">
            Position the medicine strip inside the scanning zone. Hold steady for automatic capture.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # WebRTC Streamer (protected for headless test runner environments)
    ctx = None
    try:
        ctx = webrtc_streamer(
            key=f"webrtc_camera_{med_idx}",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=LOCAL_RTC_CONFIG,
            video_processor_factory=FramingVideoProcessor,
            media_stream_constraints={
                "video": {
                    "width": {"ideal": 640},
                    "height": {"ideal": 480},
                    "frameRate": {"ideal": 24},
                },
                "audio": False,
            },
            async_processing=True,
        )
    except Exception:
        st.info("🎥 Live WebRTC camera is ready for real browser sessions. In headless mode, use Snapshot Camera or Upload.")
        ctx = None

    if ctx is not None and ctx.video_processor:
        st.session_state[f"processor_{med_idx}"] = ctx.video_processor

    # Extract framing state and recommendations
    framing_state = FramingState.NO_OBJECT
    capture_state = CaptureState.SCANNING
    if ctx is not None and ctx.video_processor:
        framing_state = ctx.video_processor.current_framing_state
        capture_state = ctx.video_processor.capture_state

    # Synchronous check for completed capture in current render cycle
    if ctx is not None and ctx.video_processor:
        if capture_state == CaptureState.CAPTURED:
            captured_bgr = ctx.video_processor.take_pending_capture()
            if captured_bgr is not None:
                st.session_state[f"med{med_idx}_review_frame"] = captured_bgr
                st.rerun()

    # Dynamic status bar
    if capture_state == CaptureState.HOLD_STEADY:
        tip_text = "Target detected! Hold steady to auto-capture..."
        dot_class = "guidance-dot-steady"
    elif capture_state in (CaptureState.CAPTURED, CaptureState.REVIEW):
        tip_text = "Captured! Reviewing photo..."
        dot_class = "guidance-dot-good"
    elif framing_state == FramingState.GOOD_POSITION:
        tip_text = "Good position! Hold still..."
        dot_class = "guidance-dot-good"
    else:
        tip_text = FRAMING_RECOMMENDATION_TIPS.get(
            framing_state.value,
            "Position medicine inside the target box with text facing forward.",
        )
        dot_class = "guidance-dot-adjust"

    st.markdown(
        f"""
        <div class="framing-guidance-bar">
            <span class="guidance-dot {dot_class}"></span>
            <strong>{tip_text}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Scanning hints
    st.markdown(
        """
        <div class="scan-hints-list">
            <span>✓ Keep medicine name visible</span>
            <span>✓ Center strip in frame</span>
            <span>✓ Avoid glare & reflections</span>
            <span>✓ Hold steady for auto-capture</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(f"🔒 {NETWORKING_STATEMENT}")

    # Start watcher fragment if streamer is playing
    if ctx is not None and ctx.state.playing:
        _auto_capture_watcher(ctx, med_idx)
