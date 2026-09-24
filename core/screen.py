"""
Zia Screen Grounding Engine
===========================

Reliable "look at the screen, then click / type in the right place" support.

Why this module exists
----------------------
The previous implementation lived inline in ``core/tools.py`` and failed for
four independent reasons:

1. **DPI blindness** — Windows display scaling means a screenshot is in
   *physical* pixels while ``pyautogui`` reports *logical* pixels. Every
   grounded box was therefore scaled wrong on any scaled display.
2. **Unit ambiguity** — the prompt asked for a bounding box without saying in
   which units, then the code blindly did ``coord / 1000``. Absolute-pixel
   answers produced clicks at roughly half the correct position.
3. **Brittle parsing** — a regex matching only plain integers rejected
   decimals, ``ymin:`` labels and JSON, which is what models actually emit.
4. **No validation or verification** — a failed detection still clicked the
   top-left corner and reported success.

Design
------
* ``init_dpi_awareness()`` is called once at startup so physical and logical
  pixel spaces agree. The scale factor is *still* measured and applied, so
  grounding stays correct even if DPI opt-in fails.
* ``ground()`` returns a ``Box`` in **logical screen coordinates**, already
  clamped and validated. The unit system is auto-detected, never assumed.
* Grounding is *ROI-constrained*: a small region of interest is searched first
  (much higher accuracy and lower latency), then the full screen as fallback.
  An ROI is only a hint — a wrong ROI cannot produce a wrong click, it can
  only cost one extra attempt.
* Typing goes through the clipboard, because ``pyautogui.write`` cannot emit
  Unicode (emojis and non-ASCII characters are silently dropped).
"""

from __future__ import annotations

import ctypes
import io
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from typing import Any, Sequence

log = logging.getLogger("Zia.screen")

# ---------------------------------------------------------------------------
# Tunables (env-overridable, mirroring core/config.py conventions)
# ---------------------------------------------------------------------------


def _env_float(name: str, default: float) -> float:
    raw = (os.environ.get(name) or "").strip()
    try:
        return float(raw) if raw else default
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = (os.environ.get(name) or "").strip().lower()
    if not raw:
        return default
    return raw in ("true", "1", "yes", "on")


#: Ordered grounding-model fallbacks, measured against the live API.
#:
#: Each Gemini model has its own free-tier daily quota, so a ladder spanning
#: *different* models multiplies the grounding calls available per day. Ordering
#: is by real latency, not by name: grounding is a simple localization task, so a
#: "lite" model is both accurate enough and an order of magnitude faster.
#:
#:   gemini-flash-lite-latest   ~1.1s   <- preferred
#:   gemini-flash-latest        ~0.6s to reject when its quota is spent
#:   gemini-3.1-flash-lite      ~6.6s
#:   gemini-3.6-flash           ~9.3s
#:
#: Deliberately excluded: ``gemini-3.5-flash`` (47s observed), and the retired
#: ``gemini-2.5-flash`` / ``gemini-2.0-flash`` / ``gemini-2.5-flash-lite`` (404).
DEFAULT_GROUNDING_MODELS: tuple[str, ...] = (
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemini-3.1-flash-lite",
    "gemini-3.6-flash",
)

GROUNDING_TIMEOUT_S = _env_float("VISION_GROUNDING_TIMEOUT", 25.0)
GROUNDING_ENABLED = _env_bool("USE_VISION_GROUNDING", True)
#: Longest side of the image actually sent to the model. Sending a full
#: 1920x1080 capture costs far more upload and latency than grounding needs,
#: and normalized answers are unaffected by the downscale.
GROUNDING_MAX_SIDE = int(_env_float("VISION_GROUNDING_MAX_SIDE", 1536))

#: Boxes smaller / larger than these screen fractions are treated as noise.
MIN_BOX_FRACTION = _env_float("VISION_MIN_BOX_FRACTION", 0.0001)
MAX_BOX_FRACTION = _env_float("VISION_MAX_BOX_FRACTION", 0.98)

_dpi_initialised = False


# ---------------------------------------------------------------------------
# DPI awareness — the single most important fix for correct clicks
# ---------------------------------------------------------------------------
def init_dpi_awareness() -> bool:
    """
    Opt this process into per-monitor DPI awareness so that screenshots
    (physical pixels) and pyautogui coordinates (logical pixels) match.

    Safe to call repeatedly; returns True if the process is DPI aware.
    """
    global _dpi_initialised
    if _dpi_initialised:
        return True
    if sys.platform != "win32":
        _dpi_initialised = True
        return False

    # Windows 10 1703+: PER_MONITOR_AWARE_V2 (-4)
    try:
        if ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            _dpi_initialised = True
            log.info("Screen: DPI awareness = PER_MONITOR_AWARE_V2")
            return True
    except Exception:
        pass

    # Windows 8.1+: PROCESS_PER_MONITOR_DPI_AWARE (2)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        _dpi_initialised = True
        log.info("Screen: DPI awareness = PROCESS_PER_MONITOR_DPI_AWARE")
        return True
    except Exception:
        pass

    # Vista+: system DPI aware (better than nothing)
    try:
        ctypes.windll.user32.SetProcessDPIAware()
        _dpi_initialised = True
        log.info("Screen: DPI awareness = system-aware")
        return True
    except Exception:
        log.warning("Screen: could not enable DPI awareness; "
                    "clicks will be scale-corrected at runtime instead.")
        return False


# ---------------------------------------------------------------------------
# Screen metrics
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ScreenMetrics:
    """Physical (screenshot) vs logical (mouse) pixel geometry."""

    physical_w: int
    physical_h: int
    logical_w: int
    logical_h: int

    @property
    def scale_x(self) -> float:
        return self.logical_w / self.physical_w if self.physical_w else 1.0

    @property
    def scale_y(self) -> float:
        return self.logical_h / self.physical_h if self.physical_h else 1.0

    @property
    def is_scaled(self) -> bool:
        return abs(self.scale_x - 1.0) > 0.01 or abs(self.scale_y - 1.0) > 0.01

    def describe(self) -> str:
        return (f"physical={self.physical_w}x{self.physical_h} "
                f"logical={self.logical_w}x{self.logical_h} "
                f"scale={self.scale_x:.3f}x{self.scale_y:.3f}")


def logical_size() -> tuple[int, int]:
    """Mouse/coordinate space size, i.e. what pyautogui clicks in."""
    try:
        import pyautogui  # type: ignore[import]
        w, h = pyautogui.size()
        return int(w), int(h)
    except Exception as exc:  # pragma: no cover - environment specific
        log.warning("Screen: pyautogui.size() failed (%s); assuming 1:1", exc)
        return 0, 0


def capture_metrics(image_size: tuple[int, int]) -> ScreenMetrics:
    """Build metrics from a captured image size and the logical screen size."""
    lw, lh = logical_size()
    pw, ph = int(image_size[0]), int(image_size[1])
    if lw <= 0 or lh <= 0:
        lw, lh = pw, ph
    return ScreenMetrics(physical_w=pw, physical_h=ph, logical_w=lw, logical_h=lh)


# ---------------------------------------------------------------------------
# Regions of interest (fractions of the screen: left, top, width, height)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Roi:
    """A fractional rectangle of the screen, used to narrow a grounding search."""

    left: float
    top: float
    width: float
    height: float
    label: str = ""

    def to_pixels(self, img_w: int, img_h: int) -> tuple[int, int, int, int]:
        """
        Convert to an absolute ``(left, top, right, bottom)`` pixel box.

        The result is always a positive-area rectangle inside the image, even
        for a degenerate ROI, because callers pass it straight to PIL's crop.
        """
        width = max(1, int(img_w))
        height = max(1, int(img_h))
        left = max(0, min(int(round(self.left * width)), width - 1))
        top = max(0, min(int(round(self.top * height)), height - 1))
        right = max(left + 1,
                    min(width, int(round((self.left + self.width) * width))))
        bottom = max(top + 1,
                     min(height, int(round((self.top + self.height) * height))))
        return left, top, right, bottom


#: Per-app regions that are stable across window sizes. These are *hints* that
#: make grounding faster and more accurate; a miss falls back to the full
#: screen, so an inaccurate entry can never cause a wrong click.
PROVIDER_ROIS: dict[str, dict[str, Roi]] = {
    "whatsapp": {
        "search": Roi(0.00, 0.00, 0.32, 0.22, "whatsapp search panel"),
        "input": Roi(0.33, 0.80, 0.67, 0.20, "whatsapp composer"),
    },
    "instagram": {
        "search": Roi(0.00, 0.00, 0.30, 0.25, "instagram inbox search"),
        "input": Roi(0.45, 0.80, 0.55, 0.20, "instagram composer"),
    },
    "telegram": {
        "search": Roi(0.00, 0.00, 0.30, 0.18, "telegram search"),
        "input": Roi(0.28, 0.82, 0.72, 0.18, "telegram composer"),
    },
    "messenger": {
        "search": Roi(0.00, 0.00, 0.32, 0.18, "messenger search"),
        "input": Roi(0.30, 0.82, 0.70, 0.18, "messenger composer"),
    },
    "discord": {
        "search": Roi(0.00, 0.00, 0.28, 0.14, "discord search"),
        "input": Roi(0.26, 0.82, 0.74, 0.18, "discord composer"),
    },
    "slack": {
        "search": Roi(0.00, 0.00, 0.28, 0.14, "slack search"),
        "input": Roi(0.26, 0.80, 0.74, 0.20, "slack composer"),
    },
}


def roi_for(provider: str, role: str) -> Roi | None:
    """Look up a provider ROI; returns None when unknown."""
    return PROVIDER_ROIS.get((provider or "").lower(), {}).get(role)


# ---------------------------------------------------------------------------
# Bounding boxes
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Box:
    """A validated rectangle in **logical screen coordinates**."""

    x: int
    y: int
    w: int
    h: int
    label: str = ""
    confidence: float = 1.0
    source: str = ""

    @property
    def center(self) -> tuple[int, int]:
        return self.x + self.w // 2, self.y + self.h // 2

    def describe(self) -> str:
        cx, cy = self.center
        return (f"[{self.x},{self.y} {self.w}x{self.h}] center=({cx},{cy})"
                f" conf={self.confidence:.2f} via {self.source}")


def detect_unit(values: Sequence[float]) -> str:
    """
    Guess which coordinate system a model used, because they are inconsistent.

    Returns ``"fraction"`` (0..1), ``"normalized"`` (0..1000) or
    ``"absolute"`` (pixels). Values above 1.0 cannot be fractions; values at
    or below 1000 are assumed normalized, which is the documented Gemini
    ``box_2d`` convention.
    """
    if not values:
        return "absolute"
    vmax = max(abs(float(v)) for v in values)
    vmin = min(float(v) for v in values)
    if vmax <= 1.0 and vmin >= 0.0:
        return "fraction"
    if vmax <= 1000.0:
        return "normalized"
    return "absolute"


def resolve_unit(values: Sequence[float]) -> str:
    """
    Decide the coordinate system for a *whole box*, not one axis at a time.

    Deciding per axis and then reconciling creates a nasty failure: for
    ``[500, 800, 700, 1200]`` the x-axis looks absolute (1200 > 1000) while the
    y-axis looks normalized, and preferring "normalized" for both halves every
    coordinate. Because normalized boxes can never exceed 1000, a single value
    above 1000 proves the whole box is in pixels.
    """
    magnitudes = [abs(float(v)) for v in values]
    if not magnitudes:
        return "absolute"
    if max(magnitudes) <= 1.0:
        return "fraction"
    if max(magnitudes) > 1000.0:
        return "absolute"
    return "normalized"


def scale_coord(value: float, unit: str, axis: int) -> float:
    """Convert a single coordinate into absolute pixels for ``axis`` length."""
    if unit == "fraction":
        return float(value) * axis
    if unit == "normalized":
        return float(value) / 1000.0 * axis
    return float(value)


def _as_number_list(value: Any) -> list[float] | None:
    """Best-effort conversion of a nested structure into a flat number list."""
    out: list[float] = []

    def walk(node: Any) -> None:
        if isinstance(node, bool):
            return
        if isinstance(node, (int, float)):
            out.append(float(node))
        elif isinstance(node, (list, tuple)):
            for item in node:
                walk(item)

    walk(value)
    return out or None


def _extract_numbers(text: str) -> list[float] | None:
    """Pull the first four numbers out of an arbitrary model response."""
    matches = re.findall(r"-?\d+(?:\.\d+)?", text)
    if len(matches) < 4:
        return None
    return [float(m) for m in matches[:4]]


def parse_box_payload(
    payload: Any,
    image_w: int,
    image_h: int,
    offset: tuple[int, int] = (0, 0),
    label: str = "",
) -> Box | None:
    """
    Turn a model response into a ``Box`` in *image* coordinates.

    Accepts a dict (structured output), a JSON string, or a raw text blob
    containing four numbers in ``[ymin, xmin, ymax, xmax]`` order. Decimals,
    ``ymin:`` labels and code fences are all tolerated — the old implementation
    rejected every one of those.

    ``offset`` is the ``(left, top)`` of the crop the image came from, so the
    result is always expressed relative to the full screen image.
    """
    if payload is None:
        return None

    confidence = 1.0
    raw_values: list[float] | None = None
    unit_hint: str | None = None
    data: Any = payload

    if isinstance(payload, str):
        text = payload.strip()
        data = None
        stripped = re.sub(r"^```(?:json)?|```$", "", text,
                          flags=re.MULTILINE).strip()
        try:
            parsed = json.loads(stripped)
        except Exception:
            parsed = None
        if isinstance(parsed, dict):
            data = parsed
        elif isinstance(parsed, list):
            raw_values = _as_number_list(parsed)
        if data is None and raw_values is None:
            raw_values = _extract_numbers(text)

    if isinstance(data, dict):
        if data.get("found") is False:
            return None
        try:
            confidence = float(data.get("confidence", 1.0))
        except (TypeError, ValueError):
            confidence = 1.0
        label = str(data.get("label") or label)
        hint = str(data.get("units") or "").strip().lower()
        unit_hint = hint or None
        for key in ("box_2d", "box", "bbox", "bounding_box", "rect"):
            if data.get(key) is not None:
                raw_values = _as_number_list(data[key])
                break
        if raw_values is None and data.get("x") is not None:
            try:
                x = float(data["x"])
                y = float(data["y"])
                w = float(data.get("width", data.get("w", 0)))
                h = float(data.get("height", data.get("h", 0)))
                raw_values = [y, x, y + h, x + w]
                unit_hint = unit_hint or "absolute"
            except (TypeError, ValueError, KeyError):
                raw_values = None

    if raw_values is None or len(raw_values) < 4:
        return None

    ymin, xmin, ymax, xmax = (float(v) for v in raw_values[:4])
    if max(ymin, xmin, ymax, xmax) <= 0:
        return None

    if unit_hint in ("normalized", "normalised", "0-1000", "0_1000"):
        unit_x = unit_y = "normalized"
    elif unit_hint in ("fraction", "fractional", "relative", "0-1"):
        unit_x = unit_y = "fraction"
    elif unit_hint in ("absolute", "pixels", "px"):
        unit_x = unit_y = "absolute"
    else:
        unit_x = unit_y = resolve_unit([ymin, xmin, ymax, xmax])

    left = scale_coord(min(xmin, xmax), unit_x, image_w) + offset[0]
    right = scale_coord(max(xmin, xmax), unit_x, image_w) + offset[0]
    top = scale_coord(min(ymin, ymax), unit_y, image_h) + offset[1]
    bottom = scale_coord(max(ymin, ymax), unit_y, image_h) + offset[1]

    return Box(
        x=int(round(left)),
        y=int(round(top)),
        w=int(round(right - left)),
        h=int(round(bottom - top)),
        label=label,
        confidence=confidence,
        source=f"vision:{unit_x}",
    )


def validate_box(
    box: Box | None,
    metrics: ScreenMetrics,
    min_fraction: float = MIN_BOX_FRACTION,
    max_fraction: float = MAX_BOX_FRACTION,
) -> Box | None:
    """
    Clamp a box into logical screen space and reject implausible detections.

    A model that "cannot find" an element often returns ``[0,0,0,0]`` or a
    full-screen box. Clicking either is worse than admitting failure, so both
    are rejected here instead of being acted on.
    """
    if box is None:
        return None
    if box.w <= 0 or box.h <= 0:
        log.info("Screen: rejected degenerate box %s", box.describe())
        return None

    screen_area = float(metrics.logical_w * metrics.logical_h) or 1.0
    area_fraction = (box.w * box.h) / screen_area
    if area_fraction < min_fraction:
        log.info("Screen: rejected tiny box (area %.5f) %s",
                 area_fraction, box.describe())
        return None
    if area_fraction > max_fraction:
        log.info("Screen: rejected oversized box (area %.3f) %s",
                 area_fraction, box.describe())
        return None

    x = max(0, min(box.x, metrics.logical_w - 1))
    y = max(0, min(box.y, metrics.logical_h - 1))
    w = max(1, min(box.w, metrics.logical_w - x))
    h = max(1, min(box.h, metrics.logical_h - y))
    return Box(x=x, y=y, w=w, h=h, label=box.label,
               confidence=box.confidence, source=box.source)


# ---------------------------------------------------------------------------
# Capture
# ---------------------------------------------------------------------------
def capture(region: tuple[int, int, int, int] | None = None):
    """
    Grab the primary screen (optionally a ``(left, top, right, bottom)`` crop).

    DPI awareness is enforced first so the returned image and mouse
    coordinates live in the same pixel space.
    """
    init_dpi_awareness()
    from PIL import ImageGrab  # type: ignore[import]

    if region is not None:
        return ImageGrab.grab(bbox=region)
    return ImageGrab.grab()


def capture_with_metrics(region: tuple[int, int, int, int] | None = None):
    """Return ``(image, metrics)`` for the captured region."""
    image = capture(region)
    return image, capture_metrics(image.size)


def image_to_jpeg_bytes(image, max_side: int = 1280, quality: int = 85) -> bytes:
    """Encode for a vision model, downscaling only for description/summary use."""
    out = image
    if max_side and max(out.size) > max_side:
        ratio = max_side / float(max(out.size))
        out = out.resize((max(1, int(out.width * ratio)),
                          max(1, int(out.height * ratio))))
    buf = io.BytesIO()
    out.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Grounding model call
# ---------------------------------------------------------------------------
_GROUNDING_PROMPT = (
    "You are a UI grounding engine. Locate the requested UI element in the "
    "screenshot and return its bounding box.\n\n"
    "Target element: {description}\n\n"
    "Rules:\n"
    "- Boxes are normalized integers from 0 to 1000, as "
    "[ymin, xmin, ymax, xmax], from the TOP-LEFT of the image.\n"
    "- Only return an element you can actually see and read.\n"
    "- Prefer the interactive control the user must click: an input field "
    "means the clickable text box itself, not its label or placeholder text "
    "outside the field.\n"
    "- If the element is not visible, set found to false and leave the box "
    "empty. Never guess.\n"
    "- confidence is 0.0-1.0 and must be low when the element is ambiguous."
)


def _gemini_api_key() -> str:
    """
    Read the Gemini key, loading ``.env`` first if this module is used on its own.

    ``core.screen`` reads the environment directly, but ``.env`` is only loaded
    as a side effect of importing ``core.config``. Relying on that ordering made
    grounding silently unavailable in any entry point that did not import
    ``core.config`` first (the standalone vision diagnostic, for example).
    """
    key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if key and key != "mock":
        return key

    try:
        from core.config import reload_settings
        reload_settings()
    except Exception:
        log.debug("Screen: could not reload settings from .env", exc_info=True)
        return ""

    key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    return "" if key == "mock" else key


def _model_ladder() -> list[str]:
    """
    Ordered grounding models: env override first, then the known-good defaults.

    ``gemini-2.5-flash`` and ``gemini-2.0-flash`` were retired and now return
    404, so they are gone from this list. ``gemini-flash-latest`` is an alias
    that currently resolves to ``gemini-3.8-flash``.
    """
    override = (os.environ.get("VISION_GROUNDING_MODEL") or "").strip()
    ladder = [override] if override else []
    for model in DEFAULT_GROUNDING_MODELS:
        if model not in ladder:
            ladder.append(model)
    return ladder


def _is_quota_error(exc: Exception) -> bool:
    text = str(exc)
    return "429" in text or "RESOURCE_EXHAUSTED" in text


def _short_error(exc: Exception, limit: int = 180) -> str:
    """Providers return enormous multi-line JSON; keep logs readable."""
    text = " ".join(str(exc).split())
    return text[:limit] + ("..." if len(text) > limit else "")


def _call_legacy(image, prompt: str, api_key: str) -> str | None:
    """
    Fallback for environments where only the deprecated SDK is installed.

    Deliberately *not* called when the modern SDK exists but its request failed:
    retrying the same models there would double the quota burn on every
    rate-limit, and the package is end-of-life anyway.
    """
    try:
        import google.generativeai as legacy  # type: ignore[import]
    except ImportError:
        log.warning("Screen: no Gemini SDK installed (pip install google-genai)")
        return None

    legacy.configure(api_key=api_key)
    for model in _model_ladder():
        try:
            response = legacy.GenerativeModel(model).generate_content([image, prompt])
            text = getattr(response, "text", None)
            if text:
                log.debug("Screen: grounded with google-generativeai/%s", model)
                return text
        except Exception as exc:
            log.warning("Screen: google-generativeai/%s failed: %s",
                        model, _short_error(exc))
    return None


def _call_hf_grounding_model(image, prompt: str) -> str | None:
    """Ask Hugging Face Qwen2-VL for a bounding box."""
    hf_key = (os.environ.get("HUGGING_FACE_KEY") or "").strip()
    if not hf_key:
        return None
    try:
        from openai import OpenAI
        import base64
        import io
        
        client = OpenAI(base_url="https://api-inference.huggingface.co/v1/", api_key=hf_key)
        
        # Convert PIL image to base64
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=85)
        b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")
        
        import re
        desc_match = re.search(r"Target element:\s*(.*)", prompt)
        description = desc_match.group(1).strip() if desc_match else "the UI element"
        qwen_prompt = f"Find the bounding box of {description}."

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": qwen_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"},
                    },
                ],
            }
        ]
        
        response = client.chat.completions.create(
            model="Qwen/Qwen2-VL-7B-Instruct",
            messages=messages,
            max_tokens=256,
            temperature=0.0
        )
        text = response.choices[0].message.content
        if text:
            log.debug("Screen: grounded with HuggingFace (Qwen2-VL)")
            return text
    except Exception as exc:
        log.warning("Screen: HuggingFace vision failed: %s", _short_error(exc))
    return None


def _call_grounding_model(image, prompt: str) -> str | None:
    """
    Ask a vision model for a box, walking the model ladder.

    Returns raw response text, or None when grounding is unavailable.
    """
    # Try Hugging Face first
    hf_response = _call_hf_grounding_model(image, prompt)
    if hf_response:
        return hf_response

    api_key = _gemini_api_key()
    if not api_key:
        log.warning("Screen: GEMINI_API_KEY is not set; grounding unavailable")
        return None

    try:
        from google import genai  # type: ignore[import]
        from google.genai import types  # type: ignore[import]
    except ImportError:
        log.info("Screen: google-genai not installed; using the legacy SDK")
        return _call_legacy(image, prompt, api_key)

    try:
        # The SDK retries retryable errors with backoff by default, which turned
        # an observed 9s request into 47s and made a 4-model ladder take over a
        # minute. Grounding is interactive, so one attempt per model is right and
        # the model ladder below provides the fallback instead.
        http_options = types.HttpOptions(
            retry_options=types.HttpRetryOptions(attempts=1))
        client = genai.Client(api_key=api_key, http_options=http_options)
    except Exception as exc:
        log.debug("Screen: could not set retry options (%s); using defaults",
                  _short_error(exc))
        client = genai.Client(api_key=api_key)

    try:
        config = types.GenerateContentConfig(
            temperature=0.0,
        )
    except Exception as exc:
        log.warning("Screen: google-genai setup failed (%s); using legacy SDK",
                    _short_error(exc))
        return _call_legacy(image, prompt, api_key)

    quota_exhausted = False
    deadline = time.monotonic() + GROUNDING_TIMEOUT_S
    for model in _model_ladder():
        if time.monotonic() >= deadline:
            log.warning("Screen: grounding budget of %.0fs exhausted after "
                        "trying %s; giving up", GROUNDING_TIMEOUT_S, model)
            break
        try:
            response = client.models.generate_content(
                model=model, contents=[prompt, image], config=config)
            text = getattr(response, "text", None)
            if text:
                log.debug("Screen: grounded with google-genai/%s", model)
                return text
            log.warning("Screen: %s returned no text (blocked?)", model)
        except Exception as exc:
            if _is_quota_error(exc):
                quota_exhausted = True
                log.warning("Screen: %s quota exhausted (%s)",
                            model, _short_error(exc, 120))
            else:
                log.warning("Screen: google-genai/%s failed: %s",
                            model, _short_error(exc))

    if quota_exhausted:
        log.error(
            "Screen: Gemini grounding quota is exhausted for every model tried. "
            "Screen clicking and typing will not work until the quota resets. "
            "Point VISION_GROUNDING_MODEL at a model with available quota, or "
            "set a key with a paid tier.")
    return None


# ---------------------------------------------------------------------------
# Grounding orchestration
# ---------------------------------------------------------------------------
def _to_logical(box: Box, metrics: ScreenMetrics) -> Box:
    """Map a box from screenshot pixels into mouse/logical coordinates."""
    x = int(round(box.x * metrics.scale_x))
    y = int(round(box.y * metrics.scale_y))
    w = max(1, int(round(box.w * metrics.scale_x)))
    h = max(1, int(round(box.h * metrics.scale_y)))
    return Box(x=x, y=y, w=w, h=h, label=box.label,
               confidence=box.confidence, source=box.source)


def _prepare_attempt(full_image, crop: tuple[int, int, int, int] | None,
                     max_side: int):
    """
    Build the region to send, and the factor needed to map its coordinates back.

    Returns ``(image_to_send, scale_back, offset)``. A model that answers in
    absolute pixels is answering in the coordinates of *this* image, so the
    scale-back factor is what keeps such an answer correct after a resize. Miss
    this and every pixel-based answer is off by the downscale ratio.
    """
    region = full_image.crop(crop) if crop else full_image
    offset = (crop[0], crop[1]) if crop else (0, 0)
    sent = region
    if max_side and max(region.size) > max_side:
        ratio = max_side / float(max(region.size))
        sent = region.resize((max(1, int(region.width * ratio)),
                              max(1, int(region.height * ratio))))
    scale_back = region.width / float(sent.width) if sent.width else 1.0
    return sent, scale_back, offset


def ground(
    description: str,
    roi: Roi | None = None,
    provider: str | None = None,
    role: str | None = None,
    allow_full_fallback: bool = True,
) -> Box | None:
    """
    Locate ``description`` on screen and return a validated ``Box`` in logical
    screen coordinates, or ``None`` if it could not be found reliably.

    The optional region of interest is searched first because a tight crop
    enormously improves grounding accuracy; a miss falls back to the full
    screen, so an inaccurate ROI costs latency, never correctness.
    """
    if not GROUNDING_ENABLED:
        log.info("Screen: grounding disabled by USE_VISION_GROUNDING")
        return None
    if not description or not description.strip():
        return None

    if roi is None and provider and role:
        roi = roi_for(provider, role)

    try:
        full_image, metrics = capture_with_metrics()
    except Exception as exc:
        log.error("Screen: capture failed: %s", exc)
        return None

    if metrics.is_scaled:
        log.info("Screen: DPI scale detected (%s); correcting coordinates",
                 metrics.describe())

    crops: list[tuple[tuple[int, int, int, int] | None, str]] = []
    if roi is not None:
        try:
            crops.append((roi.to_pixels(metrics.physical_w, metrics.physical_h),
                          f"roi:{roi.label or 'region'}"))
        except Exception as exc:
            log.warning("Screen: ROI crop failed (%s); using full screen", exc)
    if allow_full_fallback or not crops:
        crops.append((None, "full"))

    prompt = _GROUNDING_PROMPT.format(description=description.strip())

    for crop, source in crops:
        image, scale_back, offset = _prepare_attempt(
            full_image, crop, GROUNDING_MAX_SIDE)
        raw = _call_grounding_model(image, prompt)
        if not raw:
            continue
        parsed = parse_box_payload(raw, image.width, image.height)
        if parsed is None:
            log.info("Screen: no usable box from %s response: %r",
                     source, raw[:160])
            continue

        # sent-image pixels -> full-capture pixels -> logical mouse pixels
        parsed = Box(
            x=int(round(parsed.x * scale_back)) + offset[0],
            y=int(round(parsed.y * scale_back)) + offset[1],
            w=max(1, int(round(parsed.w * scale_back))),
            h=max(1, int(round(parsed.h * scale_back))),
            label=parsed.label,
            confidence=parsed.confidence,
            source=f"{parsed.source}/{source}",
        )
        validated = validate_box(_to_logical(parsed, metrics), metrics)
        if validated is not None:
            log.info("Screen: grounded %r -> %s", description,
                     validated.describe())
            return validated
        log.info("Screen: %s box rejected; retrying", source)

    log.warning("Screen: could not ground %r", description)
    return None


# ---------------------------------------------------------------------------
# Region signatures — cheap post-action verification
# ---------------------------------------------------------------------------
def region_signature(image, box: Box, grid: int = 24) -> bytes | None:
    """
    A coarse fingerprint of a screen region, used to detect whether an action
    changed it. Resolution is deliberately low so anti-aliasing does not read
    as a change.
    """
    try:
        crop = image.crop((box.x, box.y, box.x + box.w, box.y + box.h))
        return crop.convert("L").resize((grid, grid)).tobytes()
    except Exception as exc:
        log.debug("Screen: signature failed: %s", exc)
        return None


def signatures_differ(before: bytes | None, after: bytes | None,
                      threshold: float = 0.5) -> bool:
    """True when two signatures differ by more than ``threshold`` grey levels."""
    if before is None or after is None:
        return False
    if len(before) != len(after):
        return True
    total = sum(abs(a - b) for a, b in zip(before, after))
    return (total / float(len(before))) > threshold


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------
def _pyautogui():
    import pyautogui  # type: ignore[import]

    # Zia drives the machine deliberately; the corner failsafe would abort a
    # legitimate flow mid-task. Matches skills/automation.py behaviour.
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.02
    return pyautogui


def paste_text(text: str) -> None:
    """
    Type ``text`` into the focused control via the clipboard.

    ``pyautogui.write`` only knows characters present in the keyboard mapping,
    so emojis and non-ASCII text were silently dropped. The clipboard round
    trip handles any Unicode and is far faster for long messages.
    """
    if not text:
        return
    host = _pyautogui()
    previous = None
    try:
        import pyperclip
        try:
            previous = pyperclip.paste()
        except Exception:
            previous = None
        pyperclip.copy(text)
        time.sleep(0.05)
        host.hotkey("ctrl", "v")
        time.sleep(0.05)
    except ImportError:
        # No clipboard available — degrade to ASCII-only typing.
        log.warning("Screen: pyperclip missing; falling back to slow typing")
        host.write(text, interval=0.01)
    finally:
        if previous is not None:
            try:
                import pyperclip
                pyperclip.copy(previous)
            except Exception:
                pass


def click_box(box: Box, clicks: int = 1, button: str = "left") -> bool:
    """Move to a box centre and click it."""
    try:
        host = _pyautogui()
        cx, cy = box.center
        host.moveTo(cx, cy, duration=0.12)
        time.sleep(0.05)
        host.click(clicks=clicks, button=button)
        return True
    except Exception as exc:
        log.error("Screen: click failed: %s", exc)
        return False


def press_key(*keys: str) -> None:
    """Press a single key, or a hotkey combination when given several."""
    host = _pyautogui()
    if len(keys) > 1:
        host.hotkey(*keys)
    else:
        host.press(keys[0])


def click_element(
    description: str,
    roi: Roi | None = None,
    provider: str | None = None,
    role: str | None = None,
    clicks: int = 1,
) -> tuple[bool, str]:
    """
    Ground an element by description, click it, and report what happened.

    Returns ``(ok, message)``. Nothing is clicked when grounding fails, so a
    failed detection can no longer press whatever happens to sit at the
    top-left of the screen.
    """
    box = ground(description, roi=roi, provider=provider, role=role)
    if box is None:
        return False, f"Failed to find '{description}' on screen."
    if not click_box(box, clicks=clicks):
        return False, f"Failed to click '{description}'."
    return True, f"Clicked '{description}' at {box.center}."


def type_into_element(
    description: str,
    text: str,
    roi: Roi | None = None,
    provider: str | None = None,
    role: str | None = None,
    verify: bool = True,
) -> tuple[bool, str]:
    """
    Ground a text field, click it, and paste ``text`` into it.

    When ``verify`` is on, the target region is fingerprinted before and after
    pasting, so a silent miss is reported as a failure instead of being
    mistaken for success.
    """
    box = ground(description, roi=roi, provider=provider, role=role)
    if box is None:
        return False, f"Failed to find '{description}' on screen."

    before = None
    if verify:
        try:
            before = region_signature(capture(), box)
        except Exception:
            before = None

    if not click_box(box):
        return False, f"Failed to focus '{description}'."

    time.sleep(0.25)
    paste_text(text)
    time.sleep(0.6)

    if verify and before is not None:
        try:
            after = region_signature(capture(), box)
        except Exception:
            after = None
        if not signatures_differ(before, after):
            log.info("Screen: typing into %r did not change the region",
                     description)
            return False, f"Typed into '{description}' but nothing changed."

    return True, f"Typed into '{description}'."


#: Keyboard routes that focus a search / quick-switch field with no vision at
#: all. Tried before grounding because they cannot mis-click.
PROVIDER_SEARCH_KEYS: dict[str, tuple[str, ...]] = {
    "whatsapp": ("ctrl", "alt", "/"),
    "instagram": ("/",),
    "messenger": ("ctrl", "k"),
    "discord": ("ctrl", "k"),
    "slack": ("ctrl", "k"),
    "telegram": ("/",),
    "_web": ("ctrl", "l"),
}


def focus_search(provider: str, description: str | None = None
                 ) -> tuple[bool, str]:
    """
    Put the cursor in a messaging app's search field.
    
    Prefers an exact keyboard shortcut, then falls back to vision grounding.
    """
    keys = PROVIDER_SEARCH_KEYS.get((provider or "").lower())
    if keys:
        try:
            from core.screen import press_key
            import time
            press_key(*keys)
            time.sleep(0.5)
            return True, f"Focused {provider} search with {'+'.join(keys)}."
        except Exception as exc:
            log.warning("Screen: %s shortcut failed: %s", provider, exc)

    return click_element(
        description or "the search input field where you type a name to find a chat",
        provider=provider, role="search")


