"""
Tests for the screen grounding engine (core.screen).

These cover the pure logic that used to be wrong: unit detection, coordinate
scaling, box validation and the DPI correction. No screen, network or API key
is required, so they run anywhere.
"""

from core.screen import (
    Box,
    PROVIDER_ROIS,
    Roi,
    ScreenMetrics,
    detect_unit,
    init_dpi_awareness,
    parse_box_payload,
    resolve_unit,
    roi_for,
    scale_coord,
    signatures_differ,
    validate_box,
    _to_logical,
)

FULL_HD = ScreenMetrics(1920, 1080, 1920, 1080)


# ---------------------------------------------------------------------------
# DPI / metrics
# ---------------------------------------------------------------------------
def test_dpi_awareness_is_idempotent():
    first = init_dpi_awareness()
    assert init_dpi_awareness() == first


def test_metrics_scale_detects_scaling():
    scaled = ScreenMetrics(physical_w=2400, physical_h=1350,
                           logical_w=1920, logical_h=1080)
    assert round(scaled.scale_x, 3) == 0.8
    assert round(scaled.scale_y, 3) == 0.8
    assert scaled.is_scaled is True
    assert FULL_HD.is_scaled is False


def test_to_logical_applies_scale():
    scaled = ScreenMetrics(physical_w=2400, physical_h=1350,
                           logical_w=1920, logical_h=1080)
    mapped = _to_logical(Box(x=100, y=100, w=200, h=200), scaled)
    assert (mapped.x, mapped.y, mapped.w, mapped.h) == (80, 80, 160, 160)


# ---------------------------------------------------------------------------
# Regions of interest
# ---------------------------------------------------------------------------
def test_roi_pixel_conversion_and_clamping():
    roi = Roi(0.0, 0.0, 0.5, 0.5)
    assert roi.to_pixels(1920, 1080) == (0, 0, 960, 540)

    # A degenerate ROI must still yield a positive-area rectangle.
    sliver = Roi(1.0, 1.0, 0.0, 0.0)
    left, top, right, bottom = sliver.to_pixels(1920, 1080)
    assert right > left and bottom > top


def test_every_provider_has_search_and_input_rois():
    for provider, roles in PROVIDER_ROIS.items():
        assert "search" in roles, provider
        assert "input" in roles, provider
    assert roi_for("whatsapp", "search") is not None
    assert roi_for("whatsapp", "nope") is None
    assert roi_for("unknown-app", "search") is None


# ---------------------------------------------------------------------------
# Unit detection — the bug that made clicks land at half position
# ---------------------------------------------------------------------------
def test_detect_unit():
    assert detect_unit([0.1, 0.9]) == "fraction"
    assert detect_unit([100, 900]) == "normalized"
    assert detect_unit([500, 1500]) == "absolute"
    assert detect_unit([0]) == "fraction"


def test_scale_coord():
    assert scale_coord(500, "normalized", 1000) == 500.0
    assert scale_coord(500, "normalized", 2000) == 1000.0
    assert scale_coord(0.5, "fraction", 800) == 400.0
    assert scale_coord(640, "absolute", 1920) == 640.0


def test_resolve_unit_decides_over_the_whole_box():
    # A single value above 1000 proves the box is in pixels, even though the
    # other axis looks like it could be 0..1000 normalized.
    assert resolve_unit([500, 800, 700, 1200]) == "absolute"
    assert resolve_unit([100, 200, 300, 400]) == "normalized"
    assert resolve_unit([0.1, 0.2, 0.3, 0.4]) == "fraction"
    assert resolve_unit([0, 0, 0, 0]) == "fraction"


# ---------------------------------------------------------------------------
# Payload parsing — tolerant of everything the old regex rejected
# ---------------------------------------------------------------------------
def test_parse_normalized_json():
    box = parse_box_payload(
        '{"found": true, "box_2d": [100, 200, 300, 400], "confidence": 0.9}',
        1920, 1080)
    assert (box.x, box.y, box.w, box.h) == (384, 108, 384, 216)
    assert box.confidence == 0.9


def test_parse_absolute_pixels():
    box = parse_box_payload("[500, 800, 700, 1200]", 1920, 1080)
    assert (box.x, box.y, box.w, box.h) == (800, 500, 400, 200)


def test_parse_fractional_floats():
    box = parse_box_payload("[0.1, 0.2, 0.3, 0.4]", 1920, 1080)
    assert (box.x, box.y, box.w, box.h) == (384, 108, 384, 216)


def test_parse_labelled_decimal_text():
    # The old regex required plain integers with no labels, so this failed.
    box = parse_box_payload(
        "ymin: 100, xmin: 200.0, ymax: 300, xmax: 400", 1920, 1080)
    assert box is not None
    assert box.x == 384
    assert box.y == 108


def test_parse_fenced_json_block():
    box = parse_box_payload(
        '```json\n{"box_2d": [0, 0, 1000, 1000]}\n```', 1920, 1080)
    assert box is not None
    assert (box.x, box.y, box.w, box.h) == (0, 0, 1920, 1080)


def test_parse_xywh_shape():
    box = parse_box_payload(
        {"x": 10, "y": 20, "width": 30, "height": 40}, 1920, 1080)
    assert (box.x, box.y, box.w, box.h) == (10, 20, 30, 40)


def test_parse_respects_offset_from_crop():
    box = parse_box_payload(
        '{"box_2d": [100, 200, 300, 400]}', 1920, 1080, offset=(100, 50))
    assert (box.x, box.y) == (484, 158)


def test_parse_not_found_returns_none():
    assert parse_box_payload('{"found": false, "box_2d": []}', 1920, 1080) is None
    assert parse_box_payload("I could not find that element.", 1920, 1080) is None
    assert parse_box_payload("[0, 0, 0, 0]", 1920, 1080) is None
    assert parse_box_payload(None, 1920, 1080) is None


# ---------------------------------------------------------------------------
# Validation — a failed detection must never become a click
# ---------------------------------------------------------------------------
def test_validate_rejects_implausible_boxes():
    assert validate_box(Box(0, 0, 0, 0), FULL_HD) is None
    assert validate_box(Box(10, 10, 1, 1), FULL_HD) is None           # tiny
    assert validate_box(Box(0, 0, 1920, 1080), FULL_HD) is None       # whole screen
    assert validate_box(Box(800, 400, 200, 60), FULL_HD) is not None


def test_validate_clamps_into_screen():
    clamped = validate_box(Box(1900, 1000, 200, 200), FULL_HD)
    assert clamped is not None
    assert clamped.x + clamped.w <= 1920
    assert clamped.y + clamped.h <= 1080


# ---------------------------------------------------------------------------
# Verification helper
# ---------------------------------------------------------------------------
def test_signatures_differ():
    same = b"\x10" * 32
    assert signatures_differ(same, same) is False
    assert signatures_differ(same, b"\xff" * 32) is True
    assert signatures_differ(None, same) is False

