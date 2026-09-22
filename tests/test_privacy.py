"""
Unit tests for memory-only image handling and privacy guarantees.
"""
import io
from pathlib import Path
from unittest.mock import patch
from PIL import Image

from src.explanation.formatter import format_explanation
from src.interaction.engine import get_interaction_engine
from src.normalization.normalizer import get_normalizer
from src.privacy.image_handler import (
    ImageBuffer,
    load_image_into_memory,
    validate_image_buffer,
)
from src.privacy.network_monitor import get_network_request_count, reset_network_counter
from ui.components import render_header


def _create_test_image_bytes() -> bytes:
    """Creates a small 100x100 RGB image in memory."""
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()


def test_in_memory_loading_bytes():
    raw_bytes = _create_test_image_bytes()
    buf, err = load_image_into_memory(raw_bytes)
    assert err is None
    assert buf is not None
    assert buf.format == "PNG"
    assert buf.size == (100, 100)
    assert not buf.is_released


def test_image_buffer_release():
    raw_bytes = _create_test_image_bytes()
    buf, _ = load_image_into_memory(raw_bytes)
    assert buf.image is not None

    buf.release()
    assert buf.is_released
    assert buf.image is None

    # Released buffer should fail validation
    valid, msg = validate_image_buffer(buf)
    assert valid is False
    assert "released" in msg.lower()


def test_zero_disk_persistence(tmp_path):
    """Verifies image loading does not create files on the filesystem."""
    before_files = set(Path(".").glob("**/*.png")) | set(Path(".").glob("**/*.jpg"))

    raw_bytes = _create_test_image_bytes()
    buf, _ = load_image_into_memory(raw_bytes)
    buf.release()

    after_files = set(Path(".").glob("**/*.png")) | set(Path(".").glob("**/*.jpg"))
    # No new image files should have been written to the repo
    assert before_files == after_files


def test_zero_network_requests_scan_flow():
    """Verifies that 0 external network requests occur through a full scan-to-result flow."""
    reset_network_counter()

    # 1. Load image in volatile RAM
    raw_bytes = _create_test_image_bytes()
    buf, err = load_image_into_memory(raw_bytes)
    assert err is None

    # 2. Normalize medicines
    normalizer = get_normalizer()
    drug1 = normalizer.normalize("Ecosprin 75")
    drug2 = normalizer.normalize("Combiflam")

    # 3. Check interaction
    engine = get_interaction_engine()
    res = engine.check_interaction(drug1, drug2)

    # 4. Format explanation & chemical profile
    expl = format_explanation(res)
    buf.release()

    assert expl.headline is not None
    assert get_network_request_count() == 0


def test_live_header_network_counter_matches():
    """Verifies header component renders the exact count returned by get_network_request_count()."""
    reset_network_counter()

    with patch("streamlit.html") as mock_html:
        render_header()
        mock_html.assert_called_once()
        rendered_html = mock_html.call_args[0][0]
        count = get_network_request_count()
        assert f"{count} network requests this session" in rendered_html
