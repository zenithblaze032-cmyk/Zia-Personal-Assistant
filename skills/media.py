from __future__ import annotations

import ctypes
import logging
import re
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.context import Context
    from core.router import Router

log = logging.getLogger("Zia.skills.media")

# Windows virtual key codes for global media controls.
# These work across Spotify, Chrome, VLC, and any app that respects media keys.
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
KEYEVENTF_KEYUP = 0x0002


def _send_media_key(vk: int) -> None:
    """Send a single global media key press. No-op on non-Windows."""
    if sys.platform != "win32":
        return
    user32 = ctypes.windll.user32
    user32.keybd_event(vk, 0, 0, 0)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


def _handle_play_pause(match: re.Match, ctx: Context) -> None:
    _send_media_key(VK_MEDIA_PLAY_PAUSE)
    ctx.say("Done.")


def _handle_next(match: re.Match, ctx: Context) -> None:
    _send_media_key(VK_MEDIA_NEXT_TRACK)
    ctx.say("Next track.")


def _handle_prev(match: re.Match, ctx: Context) -> None:
    _send_media_key(VK_MEDIA_PREV_TRACK)
    ctx.say("Previous track.")


def _handle_stop(match: re.Match, ctx: Context) -> None:
    _send_media_key(VK_MEDIA_STOP)
    ctx.say("Stopped.")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
PATTERNS = [
    (r"^(?:play|pause|resume)(?:\s+(?:music|song|track|video|playback))?$|^pause$|^resume$", _handle_play_pause),
    (r"\b(?:next|skip)\b(?:\s+(?:track|song|video))?|\bskip it\b", _handle_next),
    (r"\b(?:previous|last|go back)\b(?:\s+(?:track|song|video))?", _handle_prev),
    (r"^stop(?:\s+(?:music|the music|playback))?$", _handle_stop),
]


def register(router: Router) -> None:
    for pattern, handler in PATTERNS:
        router.register(pattern, handler)
