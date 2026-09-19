from __future__ import annotations

import ctypes
import datetime
import logging
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.context import Context
    from core.router import Router

log = logging.getLogger("jarvis.skills.system")

# ---------------------------------------------------------------------------
# Volume / media key codes
# ---------------------------------------------------------------------------
VK_VOLUME_UP   = 0xAF
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_MUTE = 0xAD
KEYEVENTF_KEYUP = 0x0002


def _send_key(vk: int, presses: int = 1) -> None:
    """Send a Windows virtual key press (keybd_event). No-op on non-Windows."""
    if sys.platform != "win32":
        return
    user32 = ctypes.windll.user32
    for _ in range(presses):
        user32.keybd_event(vk, 0, 0, 0)
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------
def _handle_time(match: re.Match, ctx: Context) -> None:
    now = datetime.datetime.now(datetime.timezone.utc).astimezone()
    ctx.say(f"It's {now.strftime('%I:%M %p')}, sir.")


def _handle_date(match: re.Match, ctx: Context) -> None:
    now = datetime.datetime.now(datetime.timezone.utc).astimezone()
    ctx.say(f"Today is {now.strftime('%A, %d %B %Y')}.")


def _handle_screenshot(match: re.Match, ctx: Context) -> None:
    try:
        from PIL import ImageGrab  # type: ignore[import]
        pic_dir = Path.home() / "Pictures" / "Jarvis"
        pic_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now(datetime.timezone.utc).astimezone().strftime("%Y%m%d_%H%M%S")
        path = pic_dir / f"Jarvis_{ts}.png"
        img = ImageGrab.grab()
        img.save(str(path))
        ctx.say("Screenshot saved, sir.")
        log.info("Screenshot saved to %s", path)
    except ImportError:
        ctx.say("Screenshot needs Pillow. Run pip install Pillow.")
    except Exception as e:  # noqa: BLE001
        log.warning("Screenshot failed: %s", e)
        ctx.say("I couldn't take the screenshot, sir.")


def _handle_lock(match: re.Match, ctx: Context) -> None:
    if sys.platform == "win32":
        ctx.say("Locking the screen.")
        ctypes.windll.user32.LockWorkStation()
    else:
        ctx.say("Screen lock is only supported on Windows.")


def _handle_volume_up(match: re.Match, ctx: Context) -> None:
    _send_key(VK_VOLUME_UP, presses=5)
    ctx.say("Volume up.")


def _handle_volume_down(match: re.Match, ctx: Context) -> None:
    _send_key(VK_VOLUME_DOWN, presses=5)
    ctx.say("Volume down.")


def _handle_mute(match: re.Match, ctx: Context) -> None:
    _send_key(VK_VOLUME_MUTE)
    ctx.say("Muted.")


def _handle_help(match: re.Match, ctx: Context) -> None:
    ctx.say(
        "Here's what I can do, sir. "
        "Open any app or website. "
        "Search the web or YouTube. "
        "Tell you the time or date. "
        "Control your volume and media. "
        "Take a screenshot. "
        "Lock your screen. "
        "And launch your coding workspace."
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
PATTERNS = [
    (r"\bwhat(?:'s| is) the time\b|\bwhat time is it\b|\bthe time\b|\btime\b$", _handle_time),
    (r"\bwhat(?:'s| is) the date\b|\bwhat day is it\b|\bwhat(?:'s| is) today\b|\bdate\b$", _handle_date),
    (r"\bscreenshot\b|\btake a screenshot\b|\bgrab (a |the )?screenshot\b", _handle_screenshot),
    (r"\block\b.*(pc|screen|computer|workstation)|\block it\b", _handle_lock),
    (r"\bvolume up\b|\bturn it up\b|\blouder\b|\bincrease (the )?volume\b", _handle_volume_up),
    (r"\bvolume down\b|\bturn it down\b|\bquieter\b|\bdecrease (the )?volume\b|\blower (the )?volume\b", _handle_volume_down),
    (r"\bmute\b|\bsilence\b|\bshut up\b", _handle_mute),
    (r"\bwhat can you do\b|\bwhat you can do\b|\blist commands\b|\bcommands\b", _handle_help),
]


def register(router: Router) -> None:
    for pattern, handler in PATTERNS:
        router.register(pattern, handler)
