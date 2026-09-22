from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING
import time

if TYPE_CHECKING:
    from core.context import Context
    from core.router import Router

log = logging.getLogger("Zia.skills.routines")

import webbrowser
import subprocess
import time

try:
    from skills.window_manager import _find_window
except ImportError:
    _find_window = None

def _snap_window(app_title_hint: str, x: int, y: int, w: int, h: int):
    if not _find_window: return
    win = _find_window(app_title_hint)
    if win:
        try:
            if win.isMinimized: win.restore()
            win.resizeTo(w, h)
            win.moveTo(x, y)
        except:
            pass

def _get_screen_size():
    try:
        import ctypes
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    except:
        return 1920, 1080

def _handle_dsa_work(match: re.Match, ctx: Context) -> None:
    ctx.say("Ready for DSA, sir. Opening your tools.")
    webbrowser.open("https://www.youtube.com/playlist?list=PLbJhGqY-mq47k_WLUtzVjmarUm1EuXPj2")
    webbrowser.open("https://leetcode.com/problemset/")
    subprocess.Popen(["code", r"D:\Programming\DSA\Code"], shell=True)
    
    time.sleep(3)
    sw, sh = _get_screen_size()
    _snap_window("Visual Studio Code", 0, 0, sw // 2, sh)
    
    # We snap the browser; the active tab might be LeetCode or YouTube, so we try both
    _snap_window("LeetCode", sw // 2, 0, sw // 2, sh)
    _snap_window("YouTube", sw // 2, 0, sw // 2, sh)

def _handle_dev_work(match: re.Match, ctx: Context) -> None:
    ctx.say("Web dev mode engaged.")
    webbrowser.open("https://www.youtube.com/playlist?list=PLu0W_9lII9agq5TrH9XLIKQvv0iaF2X3w")
    webbrowser.open("https://www.w3schools.com/js/default.asp")
    subprocess.Popen(["code", r"D:\Programming\WebDevelopment\JavaScript"], shell=True)
    
    time.sleep(3)
    sw, sh = _get_screen_size()
    _snap_window("Visual Studio Code", 0, 0, sw // 2, sh)
    _snap_window("YouTube", sw // 2, 0, sw // 2, sh // 2)
    _snap_window("JavaScript", sw // 2, sh // 2, sw // 2, sh // 2)

def _handle_jarvis_work(match: re.Match, ctx: Context) -> None:
    ctx.say("Opening Zia workspace, sir.")
    subprocess.Popen(["code", r"D:\Development\Zia"], shell=True)
    subprocess.Popen(["agy", r"D:\Development\Zia"], shell=True)
    
    time.sleep(3)
    sw, sh = _get_screen_size()
    _snap_window("Visual Studio Code", 0, 0, sw // 2, sh)
    _snap_window("Antigravity", sw // 2, 0, sw // 2, sh)

def _handle_hackathon_work(match: re.Match, ctx: Context) -> None:
    ctx.say("Hackathon mode active. Let's build.")
    subprocess.Popen(["code", r"D:\Development\Hackathon Projects"], shell=True)
    subprocess.Popen(["agy", r"D:\Development\Hackathon Projects"], shell=True)
    
    time.sleep(3)
    sw, sh = _get_screen_size()
    _snap_window("Visual Studio Code", 0, 0, sw // 2, sh)
    _snap_window("Antigravity", sw // 2, 0, sw // 2, sh)

# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
PATTERNS = [
    (r"\b(?:start|open)\s+(?:dsa|data structures?)\b.*", _handle_dsa_work),
    (r"\b(?:start|open)\s+(?:development|web dev)\b.*", _handle_dev_work),
    (r"\b(?:start|open)\s+(?:jarvis|zia)\s+work\b.*", _handle_jarvis_work),
    (r"\b(?:start|open)\s+hackathon\b.*", _handle_hackathon_work),
]

def register(router: Router) -> None:
    for pattern, handler in PATTERNS:
        router.register(pattern, handler)
