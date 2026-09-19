from core.tts import say_text
import ctypes
import logging
import os
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

from core.config import *

log = logging.getLogger(__name__)


def _chrome_executable() -> str | None:
    if sys.platform == "win32":
        for base in (
            os.environ.get("ProgramFiles", r"C:\Program Files"),
            os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
            os.environ.get("LOCALAPPDATA", ""),
        ):
            if not base:
                continue
            p = os.path.join(base, "Google", "Chrome",
                             "Application", "chrome.exe")
            if os.path.isfile(p):
                return p
    return shutil.which("google-chrome") or shutil.which("chrome")


def _win32_sorted_monitor_rects() -> list[tuple[int, int, int, int]]:
    if sys.platform != "win32":
        return []
    from ctypes import wintypes

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG), ("top", wintypes.LONG),
            ("right", wintypes.LONG), ("bottom", wintypes.LONG),
        ]

    collected: list[tuple[int, int, int, int]] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC,
                        ctypes.POINTER(RECT), wintypes.LPARAM)
    def _cb(_hm, _hdc, lprc, _lp):
        r = lprc.contents
        collected.append(
            (int(r.left), int(r.top), int(r.right), int(r.bottom)))
        return True

    ctypes.windll.user32.EnumDisplayMonitors(None, None, _cb, 0)
    collected.sort(key=lambda t: (t[0], t[1]))
    return collected


def _chrome_monitor_bounds(one_based_index: int) -> tuple[int, int, int, int]:
    rects = _win32_sorted_monitor_rects()
    if not rects:
        return (0, 0, 1920, 1080)
    idx = max(0, min(one_based_index - 1, len(rects) - 1))
    return rects[idx]


def _chrome_new_window_wait_timeout_s() -> float:
    try:
        return max(3.0, float((os.environ.get("CHROME_NEW_WINDOW_WAIT_S") or "25").strip()))
    except ValueError:
        return 25.0


def _chrome_top_level_browser_hwnds_win32() -> set[int]:
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    GW_OWNER = 4
    GWL_EXSTYLE = -20
    WS_EX_TOOLWINDOW = 0x00000080
    found: set[int] = set()

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def _enum(hwnd, _lp):
        if user32.GetWindow(hwnd, GW_OWNER):
            return True
        if user32.GetWindowLongW(hwnd, GWL_EXSTYLE) & WS_EX_TOOLWINDOW:
            return True
        if not user32.IsWindowVisible(hwnd) and not user32.IsIconic(hwnd):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == 0:
            return True
        hproc = kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not hproc:
            return True
        try:
            buf = ctypes.create_unicode_buffer(4096)
            sz = wintypes.DWORD(len(buf))
            if not kernel32.QueryFullProcessImageNameW(hproc, 0, buf, ctypes.byref(sz)):
                return True
            exe_path = buf.value
        finally:
            kernel32.CloseHandle(hproc)
        if os.path.basename(exe_path).lower() != "chrome.exe":
            return True
        r = wintypes.RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(r)):
            return True
        if (r.right - r.left) < 80 or (r.bottom - r.top) < 80:
            return True
        found.add(int(hwnd))
        return True

    user32.EnumWindows(_enum, 0)
    return found


def _wait_new_chrome_hwnd_win32(before: set[int], timeout: float) -> int | None:
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        time.sleep(0.12)
        new = _chrome_top_level_browser_hwnds_win32() - before
        if not new:
            continue
        best: int | None = None
        best_area = 0
        for h in new:
            r = wintypes.RECT()
            if user32.GetWindowRect(h, ctypes.byref(r)):
                a = max(0, r.right - r.left) * max(0, r.bottom - r.top)
                if a > best_area:
                    best_area = a
                    best = h
        if best is not None:
            return best
    return None


def _snap_hwnd_to_tile_win32(hwnd: int, col: int, total_cols: int, monitor: int = 1) -> None:
    x, y, w, h = _tiled_column_bounds(col, total_cols, monitor)
    user32 = ctypes.windll.user32
    SW_RESTORE = 9
    HWND_TOP = 0
    SWP_SHOWWINDOW = 0x0040
    SWP_FRAMECHANGED = 0x0020
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetWindowPos(hwnd, HWND_TOP, x, y, w, h,
                        SWP_SHOWWINDOW | SWP_FRAMECHANGED)


def _tiled_column_bounds(col: int, total_cols: int, monitor: int = 1) -> tuple[int, int, int, int]:
    l, t, r, b = _chrome_monitor_bounds(monitor)
    gap = TILED_LAYOUT_GAP
    col_w = (r - l - gap * (total_cols + 1)) // total_cols
    x = l + gap + col * (col_w + gap)
    y = t + gap
    h = b - t - 2 * gap
    return (x, y, col_w, h)


def _open_url_in_chrome(
    url: str, *, new_window: bool = True, label: str = "URL",
    window_position: tuple[int, int] | None = None,
    window_size: tuple[int, int] | None = None,
) -> None:
    u = url.strip()
    if not u:
        return
    chrome = _chrome_executable()
    try:
        if chrome:
            args = [chrome]
            if new_window:
                args.append("--new-window")
            if window_position is not None:
                args.append(
                    f"--window-position={window_position[0]},{window_position[1]}")
            if window_size:
                args.append(f"--window-size={window_size[0]},{window_size[1]}")
            args.append(u)
            popen_kw: dict = {
                "args": args, "stdin": subprocess.DEVNULL,
                "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL,
            }
            if sys.platform == "win32":
                popen_kw["creationflags"] = subprocess.CREATE_NO_WINDOW
            subprocess.Popen(**popen_kw)
        else:
            log.warning(
                "Chrome not found; opening %s in default browser.", label)
            webbrowser.open(u)
    except OSError as e:
        log.warning("Could not open %s in Chrome: %s", label, e)


def _open_chrome_tiled(url: str, label: str, col: int, total_cols: int, monitor: int = 1) -> None:
    if not url:
        return
    before = _chrome_top_level_browser_hwnds_win32() if sys.platform == "win32" else set()
    x, y, w, h = _tiled_column_bounds(col, total_cols, monitor)
    _open_url_in_chrome(
        url, new_window=True, label=label,
        window_position=(x, y), window_size=(w, h),
    )
    if sys.platform == "win32":
        hwnd = _wait_new_chrome_hwnd_win32(
            before, _chrome_new_window_wait_timeout_s())
        if hwnd is not None:
            _snap_hwnd_to_tile_win32(hwnd, col, total_cols, monitor)
        else:
            log.warning(
                "Tiled layout: timed out waiting for Chrome window (%s).", label)


def open_leetcode_in_chrome(*, tiled: bool = False, tile_col: int = 0,
                            total_cols: int = 3, monitor: int = 1) -> None:
    if not LEETCODE_URL:
        return
    if tiled and sys.platform == "win32":
        _open_chrome_tiled(LEETCODE_URL, "LeetCode",
                           tile_col, total_cols, monitor)
    else:
        _open_url_in_chrome(LEETCODE_URL, new_window=True, label="LeetCode")


def open_youtube_playlist_in_chrome(*, tiled: bool = False, tile_col: int = 1,
                                    total_cols: int = 3, monitor: int = 1) -> None:
    if not YOUTUBE_PLAYLIST_URL:
        return
    if tiled and sys.platform == "win32":
        _open_chrome_tiled(YOUTUBE_PLAYLIST_URL,
                           "YouTube playlist", tile_col, total_cols, monitor)
    else:
        _open_url_in_chrome(YOUTUBE_PLAYLIST_URL,
                            new_window=True, label="YouTube playlist")


def _vscode_executable() -> str | None:
    if sys.platform == "win32":
        exe = shutil.which("code")
        if exe:
            real = Path(exe).resolve().parent.parent / "Code.exe"
            if real.is_file():
                return str(real)
            return exe
        local = os.environ.get("LOCALAPPDATA", "")
        for base in (
            os.path.join(local, "Programs", "Microsoft VS Code", "Code.exe"),
            os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"),
                         "Microsoft VS Code", "Code.exe"),
        ):
            if base and os.path.isfile(base):
                return base
        return None
    return shutil.which("code")


def _electron_top_level_main_hwnds_win32(process_name: str) -> set[int]:
    if sys.platform != "win32":
        return set()
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    GW_OWNER = 4
    GWL_EXSTYLE = -20
    WS_EX_TOOLWINDOW = 0x00000080
    found: set[int] = set()

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def _enum(hwnd, _lp):
        if user32.GetWindow(hwnd, GW_OWNER):
            return True
        if user32.GetWindowLongW(hwnd, GWL_EXSTYLE) & WS_EX_TOOLWINDOW:
            return True
        if not user32.IsWindowVisible(hwnd) and not user32.IsIconic(hwnd):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == 0:
            return True
        hproc = kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not hproc:
            return True
        try:
            buf = ctypes.create_unicode_buffer(4096)
            sz = wintypes.DWORD(len(buf))
            if not kernel32.QueryFullProcessImageNameW(hproc, 0, buf, ctypes.byref(sz)):
                return True
            exe_path = buf.value
        finally:
            kernel32.CloseHandle(hproc)
        if os.path.basename(exe_path).lower() != process_name:
            return True
        found.add(int(hwnd))
        return True

    user32.EnumWindows(_enum, 0)
    return found


def _electron_wait_new_hwnd_win32(process_name: str, before: set[int], timeout: float) -> int | None:
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        time.sleep(0.15)
        new = _electron_top_level_main_hwnds_win32(process_name) - before
        if not new:
            continue
        best: int | None = None
        best_area = 0
        for h in new:
            r = wintypes.RECT()
            if user32.GetWindowRect(h, ctypes.byref(r)):
                a = max(0, r.right - r.left) * max(0, r.bottom - r.top)
                if a > best_area:
                    best_area = a
                    best = h
        if best is not None:
            return best
    return None


def _cursor_foreground_hwnd_win32(hwnd: int) -> None:
    user32 = ctypes.windll.user32
    SW_RESTORE = 9
    user32.ShowWindow(hwnd, SW_RESTORE)
    fg = user32.GetForegroundWindow()
    tid_tgt = user32.GetWindowThreadProcessId(hwnd, None)
    tid_fg = user32.GetWindowThreadProcessId(fg, None) if fg else 0
    if tid_fg and tid_tgt:
        user32.AttachThreadInput(tid_fg, tid_tgt, True)
    user32.SetForegroundWindow(hwnd)
    if tid_fg and tid_tgt:
        user32.AttachThreadInput(tid_fg, tid_tgt, False)


def _send_ctrl_hotkey_win32(hwnd: int, vk: int) -> None:
    user32 = ctypes.windll.user32
    KEYEVENTF_KEYUP = 0x0002
    VK_CONTROL = 0x11
    _cursor_foreground_hwnd_win32(hwnd)
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(vk, 0, 0, 0)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)


def _open_vscode_no_terminal_snap() -> None:
    if not VSCODE_OPEN_PATH:
        return
    exe = _vscode_executable()
    if not exe:
        log.warning(
            "Could not find VS Code (install it or add `code` to PATH).")
        return
    target = VSCODE_OPEN_PATH
    if not Path(target).exists():
        log.warning("VSCODE_OPEN_PATH does not exist yet: %s", target)
    popen_kw: dict = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if sys.platform == "win32":
        popen_kw["creationflags"] = subprocess.CREATE_NO_WINDOW
    try:
        subprocess.Popen(
            [exe, "-n", "--disable-workspace-trust", target], **popen_kw)
    except OSError as e:
        log.warning("Could not start VS Code: %s", e)


def _snap_vscode_to_tile_win32(
    col: int, total_cols: int, monitor: int = 1, before: set[int] | None = None
) -> None:
    if before is None:
        before = set()
    hwnd = _electron_wait_new_hwnd_win32("code.exe", before, 15.0)
    if hwnd is None:
        log.warning("Tiled layout: no new VS Code window found to snap.")
        return
    time.sleep(1.5)
    _snap_hwnd_to_tile_win32(hwnd, col, total_cols, monitor)
    if VSCODE_OPEN_TERMINAL:
        time.sleep(0.5)
        _send_ctrl_hotkey_win32(hwnd, 0xC0)  # Ctrl+`


# ===========================================================================
# Workspace launch action
# ===========================================================================

def run_workspace_launch(mode: str = "dsa") -> None:
    """Entry point to launch the workspace apps."""
    def _speak_workspace_launched_after_delay() -> None:
        time.sleep(Zia_SPEAK_DELAY_S)
        say_text(Zia_WORKSPACE_LAUNCH_PHRASE)

    total_cols = 3
    monitor = 1

    if TILED_LAYOUT_ENABLED and sys.platform == "win32":
        log.info("Launching tiled workspace: LeetCode | YouTube | VS Code")
        open_leetcode_in_chrome(tiled=True, tile_col=0,
                                total_cols=total_cols, monitor=monitor)
        open_youtube_playlist_in_chrome(
            tiled=True, tile_col=1, total_cols=total_cols, monitor=monitor)
        if Zia_WORKSPACE_LAUNCH_PHRASE.strip():
            threading.Thread(
                target=_speak_workspace_launched_after_delay, daemon=True).start()
        before_vscode = _electron_top_level_main_hwnds_win32("code.exe")
        _open_vscode_no_terminal_snap()
        threading.Thread(
            target=_snap_vscode_to_tile_win32,
            args=(2, total_cols, monitor),
            kwargs={"before": before_vscode},
            daemon=True,
        ).start()
    else:
        open_leetcode_in_chrome()
        open_youtube_playlist_in_chrome()
        if Zia_WORKSPACE_LAUNCH_PHRASE.strip():
            threading.Thread(
                target=_speak_workspace_launched_after_delay, daemon=True).start()
        _open_vscode_no_terminal_snap()


# ===========================================================================
# Main — voice keyword listener
# ===========================================================================
