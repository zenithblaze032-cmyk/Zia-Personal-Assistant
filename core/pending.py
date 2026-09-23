"""
Pending-interaction interception
================================

Some skills need to ask the user a question and act on the *next* utterance
("Should I send it?" → "yes"). The old approach opened a second microphone
stream from inside the skill, which fights with the single ASR loop that already
owns the device, and any reply spoken while Zia was still talking was discarded
by the barge-in branch in ``core/asr.py``.

Instead, a skill registers a short-lived *interceptor* here. ``Zia.py`` offers
each transcript to the interceptor before routing, and ``core/asr.py`` does the
same even while TTS is playing. The interceptor returns True when it consumed
the text, so unrelated speech still flows to the normal pipeline.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

log = logging.getLogger("Zia.pending")

InterceptFn = Callable[[str], bool]

_interceptor: InterceptFn | None = None
_lock = threading.Lock()


def register_interceptor(fn: InterceptFn) -> None:
    """Install the active interceptor, replacing any previous one."""
    global _interceptor
    with _lock:
        _interceptor = fn
    log.info("Pending: interceptor registered (%s)", getattr(fn, "__name__", fn))


def clear_interceptor(fn: InterceptFn | None = None) -> None:
    """Remove the interceptor, optionally only if it is still ``fn``."""
    global _interceptor
    with _lock:
        if fn is not None and _interceptor is not fn:
            return
        _interceptor = None
    log.info("Pending: interceptor cleared")


def has_interceptor() -> bool:
    with _lock:
        return _interceptor is not None


def dispatch_interceptor(text: str) -> bool:
    """
    Offer ``text`` to the active interceptor.

    Returns True when the text was consumed and normal routing should be
    skipped. Never raises: a broken interceptor must not break the assistant.
    """
    if not text:
        return False
    with _lock:
        fn = _interceptor
    if fn is None:
        return False
    try:
        return bool(fn(text))
    except Exception:
        log.exception("Pending: interceptor failed; ignoring it")
        return False
