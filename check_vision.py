"""
Zia vision diagnostic
=====================

Prints everything needed to tell why "click on screen" is or is not working:

    python check_vision.py                      # environment + a live grounding test
    python check_vision.py "the search bar"     # ground a specific element
    python check_vision.py --no-api             # skip the API call (offline check)

Checks performed:
  1. DPI awareness and the physical/logical pixel geometry. If these disagree and
     awareness is off, every click lands at the wrong place on a scaled display.
  2. Which implementation is live for click_on_screen / type_on_screen.
  3. Whether a real capture works, and at what resolution.
  4. A real grounding round trip: capture -> model -> validated box in logical
     screen coordinates, i.e. exactly what gets clicked.
"""

from __future__ import annotations

import os
import sys
import time

# Importing core.config loads .env, exactly as the real startup path does.
from core.config import reload_settings

reload_settings()

from core.screen import (  # noqa: E402  (must follow the .env load)
    GROUNDING_ENABLED,
    capture,
    capture_metrics,
    ground,
    init_dpi_awareness,
    logical_size,
)


def _line(title: str) -> None:
    print(f"\n--- {title} " + "-" * max(0, 62 - len(title)))


def main() -> int:
    target = "the Windows Start button"
    use_api = "--no-api" not in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        target = " ".join(args)

    _line("DPI awareness")
    aware = init_dpi_awareness()
    print(f"DPI aware process : {aware}")

    _line("Screen geometry")
    logical = logical_size()
    print(f"logical (mouse)   : {logical[0]}x{logical[1]}")
    image = capture()
    metrics = capture_metrics(image.size)
    print(f"physical (capture): {metrics.physical_w}x{metrics.physical_h}")
    print(f"scale factor      : {metrics.scale_x:.3f} x {metrics.scale_y:.3f}")
    if metrics.is_scaled:
        print("NOTE: screenshot and mouse pixels differ; ground() corrects for "
              "this, but enabling DPI awareness (done at startup in Zia.py) is "
              "the better fix.")
    else:
        print("OK: screenshot and mouse pixel spaces match.")

    _line("Live tool implementations")
    from core.tools import available_tools
    wanted = {"click_on_screen", "type_on_screen"}
    for func in available_tools:
        if func.__name__ in wanted:
            module = func.__module__
            status = "OK (core.screen)" if module == "core.tools" else module
            print(f"{func.__name__:18} -> {status}")

    _line("Grounding config")
    print(f"USE_VISION_GROUNDING : {GROUNDING_ENABLED}")
    print(f"GEMINI_API_KEY set   : {bool((os.environ.get('GEMINI_API_KEY') or '').strip())}")

    if not use_api:
        print("\nSkipping the grounding round trip (--no-api).")
        return 0

    _line(f"Grounding test: {target!r}")
    started = time.monotonic()
    box = ground(target)
    elapsed = time.monotonic() - started
    if box is None:
        print(f"FAILED after {elapsed:.1f}s - element not found or box rejected.")
        print("Try a description that is definitely visible, e.g. "
              "\"the search bar\" or a visible button label.")
        return 1

    print(f"found in {elapsed:.1f}s")
    print(f"box        : {box.describe()}")
    print(f"click point: {box.center}")
    print("Open an image editor if you want to sanity-check that point.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
