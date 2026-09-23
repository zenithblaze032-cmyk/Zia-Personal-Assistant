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
WAKE_WORD = (os.environ.get("WAKE_WORD") or "wake up").strip().lower()

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
    for a in (os.environ.get("WAKE_WORD_ALIASES")
              or "zia,hey zia,hi zia,ok zia,jarvis,hey jarvis,hi jarvis,ok jarvis,jervis,jarves,"
                 "arise,okiro,okiru,wake-up,wakeup,wake up zia,wake up jarvis,"
                 "ziya,zeah,zea,c-ya,see ya,see-ya,tsia,xea,zee ah,ziaa,ziaah,"
                 "sia,siya,seah,sea,see-ah,see ah,seea,siaa,"
                 "jia,jiya,jeah,jea,jee-ah,jee ah,jeea,jiaa").split(",")
    if a.strip()
)
WAKE_WORD_FUZZY_THRESHOLD = _env_float("WAKE_WORD_FUZZY_THRESHOLD", 0.78)
TRIGGER_COOLDOWN_S = 5.0
IDLE_TIMEOUT_S = _env_float("IDLE_TIMEOUT_S", 90.0)
POST_WAKE_COOLDOWN_S = _env_float("POST_WAKE_COOLDOWN_S", 3.0)
CLAP_THRESHOLD = 3000

# Shared events
mute_mic = threading.Event()
tts_active = threading.Event()
interrupt_event = threading.Event()
task_abort_event = threading.Event()

# Zen Mode phrases
ZEN_PHRASES = ["go zen", "start zen mode", "switch", "initialize zen mode", "go to zen mode", "activate zen mode"]

# Distinct phrases that will interrupt Zia when she is speaking
INTERRUPT_PHRASES = [
    "ok zia", 
    "stop talking", 
    "shut up", 
    "quiet zia",
    "enough zia",
    "stop listening",
    "go to sleep",
    "sleep zia"
]

# ---------------------------------------------------------------------------
# Workspace Layout
# ---------------------------------------------------------------------------
LEETCODE_URL = (os.environ.get("LEETCODE_URL")
                or "https://leetcode.com/problemset/all/").strip()
YOUTUBE_PLAYLIST_URL = (os.environ.get(
    "YOUTUBE_PLAYLIST_URL") or "https://music.youtube.com").strip()
VSCODE_OPEN_PATH = (os.environ.get("VSCODE_OPEN_PATH")
                    or str(Path.cwd())).strip()
VSCODE_OPEN_TERMINAL = (os.environ.get(
    "VSCODE_OPEN_TERMINAL") or "True").strip().lower() in ("true", "1", "yes")
TILED_LAYOUT_ENABLED = (os.environ.get(
    "TILED_LAYOUT_ENABLED") or "True").strip().lower() in ("true", "1", "yes")
TILED_LAYOUT_GAP = 6

# ---------------------------------------------------------------------------
# TTS Settings
# ---------------------------------------------------------------------------
Zia_WAKE_PHRASE = (os.environ.get("Zia_WAKE_PHRASE")
                   or "Welcome back sir, how can I help you?").strip()
Zia_WELCOME_PHRASE = (os.environ.get("Zia_WELCOME_PHRASE")
                      or "All systems online. Workspace ready, sir.").strip()
Zia_WORKSPACE_LAUNCH_PHRASE = (os.environ.get(
    "Zia_WORKSPACE_LAUNCH_PHRASE") or "All systems are online.... ready to ship some code...").strip()
Zia_SLEEP_PHRASE = (os.environ.get("Zia_SLEEP_PHRASE")
                    or "Going offline. I'll be here when you need me.").strip()
Zia_EXIT_PHRASE = (os.environ.get("Zia_EXIT_PHRASE")
                   or "Shutting down. Goodbye, sir.").strip()
Zia_WELCOME_ENABLED = (os.environ.get("Zia_WELCOME_ENABLED")
                       or "False").strip().lower() in ("true", "1", "yes")

Zia_ZEN_ON_PHRASE = (os.environ.get("Zia_ZEN_ON_PHRASE")
                     or "Zen Mode initialized. Lightning speed engaged.").strip()
Zia_ZEN_OFF_PHRASE = (os.environ.get("Zia_ZEN_OFF_PHRASE")
                      or "Falling back to normal mode, as our zen limits are reached.").strip()

Zia_SPEAK_DELAY_S = _env_float("Zia_SPEAK_DELAY_S", 1.0)
Zia_TTS_VOICE = (os.environ.get("Zia_TTS_VOICE") or "en-GB-RyanNeural").strip()
Zia_PIPER_VOICE = (os.environ.get("Zia_PIPER_VOICE")
                   or "en_GB-alan-medium").strip()

# ---------------------------------------------------------------------------
# Framework Integration Flags
# ---------------------------------------------------------------------------
USE_EFFGEN = (os.environ.get("USE_EFFGEN") or "True").strip().lower() in ("true", "1", "yes")
USE_AGENTNOVA = (os.environ.get("USE_AGENTNOVA") or "True").strip().lower() in ("true", "1", "yes")
# Disabled by default since OllamaClient does not support STT
USE_AGENTSDK_STT = (os.environ.get("USE_AGENTSDK_STT") or "False").strip().lower() in ("true", "1", "yes")
AGENTNOVA_CONFIRM_DANGEROUS = (os.environ.get("AGENTNOVA_CONFIRM_DANGEROUS") or "True").strip().lower() in ("true", "1", "yes")
AGENTNOVA_TIMEOUT_SEC = int(_env_float("AGENTNOVA_TIMEOUT_SEC", 120))
EFFGEN_COMPRESS_PROMPTS = (os.environ.get("EFFGEN_COMPRESS_PROMPTS") or "True").strip().lower() in ("true", "1", "yes")

# ---------------------------------------------------------------------------
# Vision grounding (screen clicking / typing)
# ---------------------------------------------------------------------------
# The strong model used to locate UI elements must be a *grounding* capable
# model. The local moondream vision model is kept for describing the screen,
# but it cannot return usable bounding boxes, so grounding is cloud-backed and
# degrades to a clear failure when no key is configured.
USE_VISION_GROUNDING = (os.environ.get("USE_VISION_GROUNDING") or "True").strip().lower() in ("true", "1", "yes")
VISION_GROUNDING_TIMEOUT = _env_float("VISION_GROUNDING_TIMEOUT", 25.0)
VISION_MIN_BOX_FRACTION = _env_float("VISION_MIN_BOX_FRACTION", 0.0001)
VISION_MAX_BOX_FRACTION = _env_float("VISION_MAX_BOX_FRACTION", 0.98)
# Seconds to wait for a freshly opened web app (WhatsApp Web, Instagram) to
# become interactive before attempting to ground anything inside it.
WEB_APP_READY_TIMEOUT = _env_float("WEB_APP_READY_TIMEOUT", 18.0)
