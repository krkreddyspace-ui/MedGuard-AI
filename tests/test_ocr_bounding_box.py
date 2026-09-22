"""
Unit tests for OCR bounding box overlay generator.
Confirms zero-disk persistence and valid in-memory array modifications.
"""
from pathlib import Path
import tempfile
import numpy as np
from PIL import Image

from src.ocr.bounding_box import draw_ocr_bounding_boxes
from src.ocr.engine import OcrTextLine


def test_draw_ocr_bounding_boxes_in_memory_only():
    """
    Confirms draw_ocr_bounding_boxes returns a modified in-memory numpy image array
    without persisting anything to disk.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        files_before = set(tmp_path.iterdir())

        # Create a black 100x100 3-channel image array
        original_img = np.zeros((100, 100, 3), dtype=np.uint8)

        # Create a sample detected text line with polygon bounding box
        line = OcrTextLine(
            text="ECOSPRIN",
            confidence=0.98,
            bbox=[[10, 10], [60, 10], [60, 30], [10, 30]],
        )

        annotated_arr = draw_ocr_bounding_boxes(
            image=original_img,
            text_lines=[line],
            highlight_words=["ECOSPRIN"],
            box_color=(0, 255, 0),
            thickness=2,
        )

        # 1. Output must be numpy array of same dimension
        assert isinstance(annotated_arr, np.ndarray)
        assert annotated_arr.shape == (100, 100, 3)

        # 2. Output array must be modified (not identical to original blank black image)
        assert not np.array_equal(original_img, annotated_arr)
        # Green pixels should be present in annotated array
        assert np.max(annotated_arr) > 0

        # 3. Confirm zero-disk-persistence: no new files were written to disk
        files_after = set(tmp_path.iterdir())
        assert files_before == files_after, "Bounding box function wrote files to disk!"


def test_draw_ocr_bounding_boxes_pil_input():
    """Confirms draw_ocr_bounding_boxes handles PIL Image objects seamlessly in-memory."""
    pil_img = Image.new("RGB", (120, 120), color=(255, 255, 255))
    line = OcrTextLine(
        text="WARFARIN 5MG",
        confidence=0.95,
        bbox=[20, 20, 80, 50],
    )

    result_arr = draw_ocr_bounding_boxes(pil_img, [line])
    assert isinstance(result_arr, np.ndarray)
    assert result_arr.shape == (120, 120, 3)
