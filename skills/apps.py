from __future__ import annotations

import difflib
import logging
import os
import re
import subprocess
import sys
import webbrowser
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.context import Context
    from core.router import Router

log = logging.getLogger("jarvis.skills.apps")

# ---------------------------------------------------------------------------
# App & site registry
# ---------------------------------------------------------------------------
# Maps spoken name → Windows command / executable name.
# Uses the Windows `start` command under the hood, so anything Windows
# can launch by name (registry App Paths) will work.
APPS: dict[str, str] = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "terminal": "wt.exe",
    "windows terminal": "wt.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "control panel": "control.exe",
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "firefox": "firefox",
    "brave": "brave",
    "spotify": "spotify",
    "vs code": "code",
    "vscode": "code",
    "visual studio code": "code",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "teams": "teams",
    "discord": "discord",
    "slack": "slack",
    "steam": "steam",
    "obs": "obs64",
}

# Maps spoken name → URL
SITES: dict[str, str] = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://www.github.com",
    "whatsapp": "https://web.whatsapp.com",
    "maps": "https://maps.google.com",
    "google maps": "https://maps.google.com",
    "stack overflow": "https://stackoverflow.com",
    "reddit": "https://www.reddit.com",
    "chatgpt": "https://chat.openai.com",
    "netflix": "https://www.netflix.com",
    "leetcode": "https://leetcode.com/problemset/",
    "twitter": "https://twitter.com",
    "x": "https://twitter.com",
    "instagram": "https://www.instagram.com",
    "linkedin": "https://www.linkedin.com",
}

# ---------------------------------------------------------------------------
# Phonetic alias table — maps common Vosk mis-hearings to canonical names.
# Vosk-small often splits compound words or hears phonetic approximations.
# Add entries here whenever you notice a mis-heard word in the logs.
# ---------------------------------------------------------------------------
PHONETIC_ALIASES: dict[str, str] = {
    # YouTube mis-hearings
    "you tube": "youtube",
    "utube": "youtube",
    "you chute": "youtube",
    "u tube": "youtube",
    "you tub": "youtube",
    "eu tube": "youtube",
    # Notepad mis-hearings
    "note pad": "notepad",
    "note pet": "notepad",
    "note bed": "notepad",
    "note bad": "notepad",
    "note path": "notepad",
    "notpad": "notepad",
    # Calculator mis-hearings
    "cal cu lator": "calculator",
    "calc later": "calculator",
    # Chrome mis-hearings
    "crome": "chrome",
    "chome": "chrome",
    # Spotify mis-hearings
    "spotif y": "spotify",
    "spot if y": "spotify",
    # GitHub mis-hearings
    "git hub": "github",
    "get hub": "github",
    # Stack Overflow mis-hearings
    "stack over flow": "stack overflow",
    # VS Code mis-hearings
    "vs cod": "vs code",
    "the s code": "vs code",
    # Discord mis-hearings
    "dis cord": "discord",
    # WhatsApp mis-hearings
    "what's app": "whatsapp",
    "what sapp": "whatsapp",
    "wats app": "whatsapp",
    # Reddit mis-hearings
    "red it": "reddit",
    # Netflix mis-hearings
    "net flicks": "netflix",
    "net flix": "netflix",
    # Instagram mis-hearings
    "in st a gram": "instagram",
    "insta gram": "instagram",
    # LinkedIn mis-hearings
    "linked in": "linkedin",
    # LeetCode mis-hearings
    "leet cod": "leetcode",
    "lead code": "leetcode",
    "leaf code": "leetcode",
    # ChatGPT mis-hearings
    "chat g p t": "chatgpt",
    "chap gpt": "chatgpt",
    "jat gpt": "chatgpt",
    # PowerPoint mis-hearings
    "power point": "powerpoint",
    # Task Manager mis-hearings
    "task manger": "task manager",
    # Control Panel mis-hearings
    "control pane": "control panel",
    # File Explorer mis-hearings
    "file explore": "file explorer",
    "files explorer": "file explorer",
    # Microsoft Edge mis-hearings
    "micro soft edge": "microsoft edge",
    "micro edge": "microsoft edge",
}

# Fuzzy-match threshold for app/site names (0–1). Lower = more permissive.
_FUZZY_THRESHOLD = 0.72

# Regex to detect bare domains like "github.com", "example.io"
_DOMAIN_RE = re.compile(
    r"^[\w-]+\.(com|org|io|net|dev|ai|in|co|uk|gov|edu|app)$",
    re.IGNORECASE,
)

# Settings URI prefixes — must use os.startfile, not subprocess
_URI_PREFIXES = ("ms-settings:", "ms-store:", "ms-")


def _normalize(text: str) -> str:
    """Normalize a spoken target for reliable lookup.

    Steps applied:
      1. Lowercase + strip surrounding whitespace
      2. Collapse multiple spaces (Vosk sometimes emits "you  tube")
      3. Apply the PHONETIC_ALIASES table to canonicalize mis-hearings
         (e.g. "you tube" → "youtube", "note pad" → "notepad")
    """
    t = " ".join(text.lower().split())
    return PHONETIC_ALIASES.get(t, t)


def _best_fuzzy_match(
    query: str,
    names: list[str],
    threshold: float = _FUZZY_THRESHOLD,
) -> str | None:
    """Return the best fuzzy match for *query* among *names*, or None."""
    best: str | None = None
    best_ratio = 0.0
    for name in names:
        ratio = difflib.SequenceMatcher(None, query, name).ratio()
        if ratio >= threshold and ratio > best_ratio:
            best_ratio = ratio
            best = name
    return best


def _launch_app(name: str) -> bool:
    """Open a Windows app by its executable/command name via `start`."""
    if name.startswith(_URI_PREFIXES):
        try:
            os.startfile(name)  # type: ignore[attr-defined]
            return True
        except OSError as e:
            log.warning("os.startfile(%r) failed: %s", name, e)
            return False
    return _start(name)


def _start(target: str) -> bool:
    """
    Use `cmd /c start "" <target>` to open anything Windows knows about.
    This leverages the Windows App Paths registry so Spotify, Chrome, etc.
    all work without hardcoding their install directories.
    """
    try:
        kw: dict = {
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        if sys.platform == "win32":
            kw["creationflags"] = subprocess.CREATE_NO_WINDOW
        subprocess.Popen(["cmd", "/c", "start", "", target], **kw)
        return True
    except OSError as e:
        log.warning("start(%r) failed: %s", target, e)
        return False


def _resolve_and_launch(target: str) -> bool:
    """
    Try to launch *target* using a layered priority chain:
      1. Normalize + apply phonetic alias table ("you tube" → "youtube")
      2. Exact site match → browser
      3. Exact app match  → start
      4. Substring site match → browser
      5. Substring app match  → start
      6. Fuzzy site match (difflib) → browser
      7. Fuzzy app match  (difflib) → start
      8. Bare domain (e.g. foo.com) → browser
      9. Windows start fallback      → start
    """
    raw = target.strip().lower()
    # Step 1: normalize + alias resolution
    t = _normalize(raw)
    if t != raw:
        log.info("Alias resolved: %r → %r", raw, t)

    # Step 2: exact site match
    if t in SITES:
        webbrowser.open(SITES[t])
        return True

    # Step 3: exact app match
    if t in APPS:
        return _launch_app(APPS[t])

    # Step 4–5: substring matches
    for name, url in SITES.items():
        if t in name or name in t:
            webbrowser.open(url)
            return True

    for name, cmd in APPS.items():
        if t in name or name in t:
            return _launch_app(cmd)

    # Step 6: fuzzy site match
    site_match = _best_fuzzy_match(t, list(SITES.keys()))
    if site_match:
        log.info("Fuzzy site match: %r ~ %r (%.0f%%)",
                 t, site_match,
                 difflib.SequenceMatcher(None, t, site_match).ratio() * 100)
        webbrowser.open(SITES[site_match])
        return True

    # Step 7: fuzzy app match
    app_match = _best_fuzzy_match(t, list(APPS.keys()))
    if app_match:
        log.info("Fuzzy app match: %r ~ %r (%.0f%%)",
                 t, app_match,
                 difflib.SequenceMatcher(None, t, app_match).ratio() * 100)
        return _launch_app(APPS[app_match])

    # Step 8: bare domain
    if _DOMAIN_RE.match(t):
        webbrowser.open(f"https://{t}")
        return True

    # Step 9: last resort
    return _start(target)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------
def _handle_open(match: re.Match, ctx: Context) -> None:
    target = match.group("target").strip()
    log.info("Opening: %r", target)
    if _resolve_and_launch(target):
        ctx.say(f"Opening {target}.")
    else:
        ctx.say(f"I couldn't open {target}, sir.")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
PATTERNS = [
    # Matches: "open X", "launch X", "start X", "run X",
    #          "open up X", "can you open X", "please open X",
    #          "hey open X", "go ahead and open X", "can you launch X", etc.
    (
        (r"^(?:(?:can you|please|hey|go ahead and)\s+)?"
        r"(?:open(?:\s+up)?|launch|start|run)\s+"
        r"(?:(?:the|a|an)\s+)?(?P<target>.+?)$"),
        _handle_open,
    ),
]


def register(router: Router) -> None:
    for pattern, handler in PATTERNS:
        router.register(pattern, handler)
