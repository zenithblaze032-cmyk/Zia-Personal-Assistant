import os
import threading
from pathlib import Path

from dotenv import load_dotenv

# Load .env
def reload_settings():
    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)
    
reload_settings()

def _env_float(name: str, default: float) -> float:
    raw = (os.environ.get(name) or "").strip()
    try:
        return float(raw) if raw else default
    except ValueError:
        return default

# ---------------------------------------------------------------------------
# Wake-word settings
# ---------------------------------------------------------------------------
WAKE_WORD = (os.environ.get("WAKE_WORD") or "jarvis").strip().lower()

# Audio settings
SAMPLE_RATE = 16000
BLOCK_MS = 32  

def _mic_gain_default() -> float:
    try:
        return float((os.environ.get("MIC_GAIN_FACTOR") or "4.0").strip() or "4.0")
    except ValueError:
        return 4.0

MIC_GAIN_FACTOR = _mic_gain_default()

WAKE_WORD_ALIASES: tuple[str, ...] = tuple(
    a.strip().lower()
    for a in (os.environ.get("WAKE_WORD_ALIASES") or "javis,jarves,jarvish").split(",")
    if a.strip()
)
WAKE_WORD_FUZZY_THRESHOLD = _env_float("WAKE_WORD_FUZZY_THRESHOLD", 0.78)
TRIGGER_COOLDOWN_S = 5.0
IDLE_TIMEOUT_S = _env_float("IDLE_TIMEOUT_S", 30.0)
POST_WAKE_COOLDOWN_S = _env_float("POST_WAKE_COOLDOWN_S", 3.0)
CLAP_THRESHOLD = 3000

# Shared mute event
mute_mic = threading.Event()

# ---------------------------------------------------------------------------
# Workspace Layout
# ---------------------------------------------------------------------------
LEETCODE_URL = (os.environ.get("LEETCODE_URL") or "https://leetcode.com/problemset/all/").strip()
YOUTUBE_PLAYLIST_URL = (os.environ.get("YOUTUBE_PLAYLIST_URL") or "https://music.youtube.com").strip()
VSCODE_OPEN_PATH = (os.environ.get("VSCODE_OPEN_PATH") or str(Path.cwd())).strip()
VSCODE_OPEN_TERMINAL = (os.environ.get("VSCODE_OPEN_TERMINAL") or "True").strip().lower() in ("true", "1", "yes")
TILED_LAYOUT_ENABLED = (os.environ.get("TILED_LAYOUT_ENABLED") or "True").strip().lower() in ("true", "1", "yes")
TILED_LAYOUT_GAP = 6

# ---------------------------------------------------------------------------
# TTS Settings
# ---------------------------------------------------------------------------
JARVIS_WAKE_PHRASE = (os.environ.get("JARVIS_WAKE_PHRASE") or "Welcome back sir, how can I help you?").strip()
JARVIS_WELCOME_PHRASE = (os.environ.get("JARVIS_WELCOME_PHRASE") or "All systems online. Workspace ready, sir.").strip()
JARVIS_WORKSPACE_LAUNCH_PHRASE = (os.environ.get("JARVIS_WORKSPACE_LAUNCH_PHRASE") or "All systems are online.... ready to ship some code...").strip()
JARVIS_SLEEP_PHRASE = (os.environ.get("JARVIS_SLEEP_PHRASE") or "Going offline. I'll be here when you need me.").strip()
JARVIS_EXIT_PHRASE = (os.environ.get("JARVIS_EXIT_PHRASE") or "Shutting down. Goodbye, sir.").strip()
JARVIS_WELCOME_ENABLED = (os.environ.get("JARVIS_WELCOME_ENABLED") or "False").strip().lower() in ("true", "1", "yes")
JARVIS_SPEAK_DELAY_S = _env_float("JARVIS_SPEAK_DELAY_S", 1.0)
JARVIS_TTS_VOICE = (os.environ.get("JARVIS_TTS_VOICE") or "en-GB-RyanNeural").strip()
JARVIS_PIPER_VOICE = (os.environ.get("JARVIS_PIPER_VOICE") or "en_GB-alan-high").strip()
