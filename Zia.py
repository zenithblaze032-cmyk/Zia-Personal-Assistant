import logging
import sys
import threading
import time

import skills as _skills_pkg
from core.asr import init_asr, listen_loop
from core.config import *
from core.context import Context
from core.router import Router
from core.state import AssistantState, st
from core.tts import say_text
from core.memory import Memory
from core.llm import generate_chat
import pystray
from PIL import Image, ImageDraw

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("Zia")

router = Router()
_skills_pkg.register_all(router)


def _go_shutdown():
    log.info("Exit command received. Shutting down.")
    say_text(Zia_EXIT_PHRASE)
    sys.exit(0)


def _go_sleep():
    if st.state != AssistantState.ASLEEP:
        log.info("Zia going to sleep.")
        st.state = AssistantState.ASLEEP


memory = Memory(max_turns=5)
ctx = Context(say_fn=say_text, sleep_fn=_go_sleep, shutdown_fn=_go_shutdown, memory=memory)

# Hotwords
EXIT_PHRASES = ["exit Zia", "quit Zia", "shut down Zia", "shutdown Zia",
                "close Zia", "exit", "quit", "shut down", "shutdown", "close"]
SLEEP_PHRASES = ["go to sleep", "sleep Zia", "Zia sleep", "standby", "sleep"]
DSA_WORK_PHRASES = ["get back to dsa work"]
DEV_WORK_PHRASES = ["get back to development work"]
Zia_WORK_PHRASES = ["get back to improve you"]


def _wake_word_hit(text: str) -> bool:
    if WAKE_WORD in text:
        return True
    return bool(any(a in text for a in WAKE_WORD_ALIASES))


def _strip_wake_prefix(text: str) -> str:
    import re
    # Longest first so "wake up zia" strips fully, leaving no stray "zia".
    words = sorted([WAKE_WORD] + list(WAKE_WORD_ALIASES), key=len, reverse=True)
    pattern = r'.*\b(' + '|'.join(words) + r')\b(.*)'
    m = re.match(pattern, text)
    if m:
        return m.group(2).strip()
    return text.strip()


def _dispatch(text: str) -> None:
    text = _strip_wake_prefix(text)
    if not text:
        st.last_activity = time.monotonic()
        return

    if any(cmd in text for cmd in EXIT_PHRASES):
        _go_shutdown()
        return
    if any(cmd in text for cmd in SLEEP_PHRASES):
        _go_sleep()
        return
    if any(cmd in text for cmd in DSA_WORK_PHRASES):
        from core.workspace import run_workspace_launch
        if not getattr(st, 'workspace_launched', False):
            st.workspace_launched = True
            log.info("Launching DSA workspace on command.")
            threading.Thread(target=run_workspace_launch, kwargs={
                             "mode": "dsa"}, daemon=True).start()
        else:
            ctx.say("The workspace is already open, sir.")
        st.last_activity = time.monotonic()
        return
    if any(cmd in text for cmd in DEV_WORK_PHRASES):
        from core.workspace import run_workspace_launch
        if not getattr(st, 'workspace_launched', False):
            st.workspace_launched = True
            log.info("Launching Dev workspace on command.")
            threading.Thread(target=run_workspace_launch, kwargs={
                             "mode": "dev"}, daemon=True).start()
        else:
            ctx.say("The workspace is already open, sir.")
        st.last_activity = time.monotonic()
        return
    if any(cmd in text for cmd in Zia_WORK_PHRASES):
        from core.workspace import run_workspace_launch
        if not getattr(st, 'workspace_launched', False):
            st.workspace_launched = True
            log.info("Launching Zia workspace on command.")
            threading.Thread(target=run_workspace_launch, kwargs={
                             "mode": "Zia"}, daemon=True).start()
        else:
            ctx.say("The workspace is already open, sir.")
        st.last_activity = time.monotonic()
        return

    # Add user message to memory
    memory.add_user_message(text)

    matched = router.dispatch(text, ctx)
    if matched:
        st.last_activity = time.monotonic()
    else:
        # LLM fallback
        log.info("No skill matched. Falling back to LLM.")
        response = generate_chat(memory.get_context())
        ctx.say(response)
        st.last_activity = time.monotonic()


def setup_tray():
    try:
        image = Image.new('RGB', (64, 64), color=(0, 0, 0))
        dc = ImageDraw.Draw(image)
        dc.rectangle((16, 16, 48, 48), fill=(0, 255, 0))

        def on_exit(icon, item):
            icon.stop()
            _go_shutdown()

        icon = pystray.Icon("Zia", image, "Zia", menu=pystray.Menu(
            pystray.MenuItem("Exit", on_exit)
        ))
        threading.Thread(target=icon.run, daemon=True).start()
    except Exception as e:
        log.error(f"Failed to setup tray: {e}")


def main():
    import sounddevice as sd
    input_idx = sd.default.device[0]

    print("\n ============================================================")
    print("   Z I A  -  Voice-Activated Workspace Launcher")
    print(" ============================================================\n")
    print(f" Say \"{WAKE_WORD.upper()}\" to launch your workspace:\n")
    print("   [LEFT]   LeetCode")
    print("   [CENTRE] YouTube Playlist")
    print("   [RIGHT]  VS Code + Terminal\n")
    print(" Press Ctrl+C or say \"shut down Zia\" to exit.")
    print(" ============================================================\n")

    log.info("Zia is listening...")

    init_asr(_wake_word_hit, _strip_wake_prefix, _dispatch, _go_sleep)

    # Start background proactive monitoring
    from core.proactive import start_proactive_monitoring
    start_proactive_monitoring(ctx)

    setup_tray()

    try:
        listen_loop(input_idx)
    except KeyboardInterrupt:
        log.info("Interrupted.")
        _go_shutdown()


if __name__ == "__main__":
    main()
