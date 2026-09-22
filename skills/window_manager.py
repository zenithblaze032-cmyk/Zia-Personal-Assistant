from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING
import pygetwindow as gw

if TYPE_CHECKING:
    from core.context import Context
    from core.router import Router

log = logging.getLogger("Zia.skills.window_manager")

def _find_window(app_name: str):
    """Fuzzy search for a window title."""
    windows = gw.getAllTitles()
    app_name_lower = app_name.lower()
    for title in windows:
        if app_name_lower in title.lower():
            return gw.getWindowsWithTitle(title)[0]
    return None

def _handle_snap_left(match: re.Match, ctx: Context) -> None:
    app_name = match.group("app").strip()
    win = _find_window(app_name)
    if win:
        try:
            # Assumes a standard 1080p monitor for simplicity, can be improved using screeninfo
            # For now, we'll try to get the active screen resolution, but pygetwindow doesn't expose it easily.
            # However, we can maximize and read size, or just use half width.
            # Using win32api to get screen size is more robust but we'll do a simple fallback.
            import ctypes
            user32 = ctypes.windll.user32
            screen_width = user32.GetSystemMetrics(0)
            screen_height = user32.GetSystemMetrics(1)
            
            if win.isMinimized:
                win.restore()
            
            win.resizeTo(screen_width // 2, screen_height)
            win.moveTo(0, 0)
            ctx.say(f"Snapped {app_name} to the left.")
        except Exception as e:
            log.error(f"Failed to snap window: {e}")
            ctx.say("I couldn't move the window, sir.")
    else:
        ctx.say(f"I couldn't find a window for {app_name}, sir.")

def _handle_snap_right(match: re.Match, ctx: Context) -> None:
    app_name = match.group("app").strip()
    win = _find_window(app_name)
    if win:
        try:
            import ctypes
            user32 = ctypes.windll.user32
            screen_width = user32.GetSystemMetrics(0)
            screen_height = user32.GetSystemMetrics(1)
            
            if win.isMinimized:
                win.restore()
                
            win.resizeTo(screen_width // 2, screen_height)
            win.moveTo(screen_width // 2, 0)
            ctx.say(f"Snapped {app_name} to the right.")
        except Exception as e:
            log.error(f"Failed to snap window: {e}")
            ctx.say("I couldn't move the window, sir.")
    else:
        ctx.say(f"I couldn't find a window for {app_name}, sir.")

def _handle_maximize(match: re.Match, ctx: Context) -> None:
    app_name = match.group("app").strip()
    win = _find_window(app_name)
    if win:
        try:
            win.maximize()
            ctx.say(f"Maximized {app_name}.")
        except Exception as e:
            log.error(f"Failed to maximize window: {e}")
            ctx.say("I couldn't maximize the window, sir.")
    else:
        ctx.say(f"I couldn't find a window for {app_name}, sir.")

def _handle_close(match: re.Match, ctx: Context) -> None:
    app_name = match.group("app").strip()
    win = _find_window(app_name)
    if win:
        try:
            win.close()
            ctx.say(f"Closed {app_name}.")
        except Exception as e:
            log.error(f"Failed to close window: {e}")
            ctx.say(f"I couldn't close {app_name}, sir.")
    else:
        ctx.say(f"I couldn't find a window for {app_name}, sir.")

# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
PATTERNS = [
    (r"\bsnap\s+(?P<app>.+?)\s+to (?:the )?left\b", _handle_snap_left),
    (r"\bsnap\s+(?P<app>.+?)\s+to (?:the )?right\b", _handle_snap_right),
    (r"\bmaximize\s+(?P<app>.+?)\b", _handle_maximize),
    (r"\b(?:close|quit|exit)\s+(?P<app>.+?)\b", _handle_close),
]

def register(router: Router) -> None:
    for pattern, handler in PATTERNS:
        router.register(pattern, handler)
