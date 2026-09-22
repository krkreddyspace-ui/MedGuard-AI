"""
Unit test for Step 5 in-app architecture pipeline diagram generator.
"""
from ui.components import render_architecture_diagram_html


def test_architecture_diagram_pipeline_stages_labeled():
    """
    Confirms architecture diagram includes all 4 pipeline stages labeled clearly as 'on-device / offline'.
    """
    html = render_architecture_diagram_html()

    assert isinstance(html, str)
    assert len(html) > 100

    # Confirm four stages
    assert "Camera" in html
    assert "On-device OCR" in html
    assert "Local Matching" in html
    assert "Explanation" in html

    # Confirm all 4 boxes are labeled 'on-device / offline'
    offline_label_count = html.count("on-device / offline")
    assert offline_label_count == 4, f"Expected 4 'on-device / offline' labels, found {offline_label_count}"
