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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("jarvis")

router = Router()
_skills_pkg.register_all(router)

def _go_shutdown():
    log.info("Exit command received. Shutting down.")
    say_text(JARVIS_EXIT_PHRASE)
    sys.exit(0)

def _go_sleep():
    if st.state != AssistantState.ASLEEP:
        log.info("Jarvis going to sleep.")
        st.state = AssistantState.ASLEEP

ctx = Context(say_fn=say_text, sleep_fn=_go_sleep, shutdown_fn=_go_shutdown)

# Hotwords
EXIT_PHRASES = ["exit jarvis", "quit jarvis", "shut down jarvis", "shutdown jarvis", "close jarvis", "exit", "quit", "shut down", "shutdown", "close"]
SLEEP_PHRASES = ["go to sleep", "sleep jarvis", "jarvis sleep", "standby", "sleep"]
DSA_WORK_PHRASES = ["get back to dsa work"]
DEV_WORK_PHRASES = ["get back to development work"]
JARVIS_WORK_PHRASES = ["get back to improve you"]

def _wake_word_hit(text: str) -> bool:
    if WAKE_WORD in text: return True
    return bool(any(a in text for a in WAKE_WORD_ALIASES))

def _strip_wake_prefix(text: str) -> str:
    import re
    pattern = r'.*\b(' + '|'.join([WAKE_WORD] + list(WAKE_WORD_ALIASES)) + r')\b(.*)'
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
            threading.Thread(target=run_workspace_launch, kwargs={"mode": "dsa"}, daemon=True).start()
        else:
            ctx.say("The workspace is already open, sir.")
        st.last_activity = time.monotonic()
        return
    if any(cmd in text for cmd in DEV_WORK_PHRASES):
        from core.workspace import run_workspace_launch
        if not getattr(st, 'workspace_launched', False):
            st.workspace_launched = True
            log.info("Launching Dev workspace on command.")
            threading.Thread(target=run_workspace_launch, kwargs={"mode": "dev"}, daemon=True).start()
        else:
            ctx.say("The workspace is already open, sir.")
        st.last_activity = time.monotonic()
        return
    if any(cmd in text for cmd in JARVIS_WORK_PHRASES):
        from core.workspace import run_workspace_launch
        if not getattr(st, 'workspace_launched', False):
            st.workspace_launched = True
            log.info("Launching Jarvis workspace on command.")
            threading.Thread(target=run_workspace_launch, kwargs={"mode": "jarvis"}, daemon=True).start()
        else:
            ctx.say("The workspace is already open, sir.")
        st.last_activity = time.monotonic()
        return
        
    matched = router.dispatch(text, ctx)
    if matched:
        st.last_activity = time.monotonic()
    else:
        ctx.say("I don't know that one yet.")

def main():
    import sounddevice as sd
    input_idx = sd.default.device[0]
    
    print("\n ============================================================")
    print("   J A R V I S  -  Voice-Activated Workspace Launcher")
    print(" ============================================================\n")
    print(f" Say \"{WAKE_WORD.upper()}\" to launch your workspace:\n")
    print("   [LEFT]   LeetCode")
    print("   [CENTRE] YouTube Playlist")
    print("   [RIGHT]  VS Code + Terminal\n")
    print(" Press Ctrl+C or say \"shut down Jarvis\" to exit.")
    print(" ============================================================\n")
    
    log.info("JARVIS is listening...")

    init_asr(_wake_word_hit, _strip_wake_prefix, _dispatch, _go_sleep)
    
    try:
        listen_loop(input_idx)
    except KeyboardInterrupt:
        log.info("Interrupted.")
        _go_shutdown()

if __name__ == "__main__":
    main()
