"""
Screen capture helpers for Zia's vision features.

Coordinate-correct capture now lives in ``core/screen.py`` (which also enforces
DPI awareness so that screenshots and mouse coordinates agree). This module
keeps the byte-oriented helpers that the vision-LLM skills consume.
"""

from __future__ import annotations

import logging

log = logging.getLogger("Zia.vision")


def capture_screen_bytes(max_side: int = 1280, quality: int = 85) -> bytes:
    """
    Capture the primary screen and return JPEG bytes.

    Downscaled for speed and to stay within vision-model context limits. This
    path is for *describing* the screen; use ``core.screen.ground()`` when real
    coordinates are needed, because downscaling would invalidate them.
    """
    from core.screen import capture, image_to_jpeg_bytes

    return image_to_jpeg_bytes(capture(), max_side=max_side, quality=quality)


def capture_screen_image(region: tuple[int, int, int, int] | None = None):
    """Full-resolution, DPI-corrected screen capture as a PIL image."""
    from core.screen import capture

    return capture(region)

