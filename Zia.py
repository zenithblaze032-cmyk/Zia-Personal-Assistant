import logging
import sys
import threading
import time
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning, module="duckduckgo_search")
import skills as _skills_pkg
from core.asr import ASRPipeline
from core.config import *
from core.context import Context
from core.router import Router
from core.state import AssistantState, st
from core.tts import say_text
from core.memory import Memory
from core.llm import generate_chat
from core.brain import Brain, CommandComplexity
from core.executor import AgentNovaExecutor
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
    import os
    os._exit(0)


def _go_sleep():
    if st.state != AssistantState.ASLEEP:
        log.info("Zia going to sleep.")
        st.state = AssistantState.ASLEEP
        try:
            from core.memory import consolidate_memory
            consolidate_memory(memory)
        except Exception as e:
            log.error(f"Failed to trigger memory consolidation: {e}")


memory = Memory(max_turns=5)
brain = Brain()
executor = AgentNovaExecutor()
ctx = Context(say_fn=say_text, sleep_fn=_go_sleep, shutdown_fn=_go_shutdown, memory=memory, brain=brain, executor=executor)

# Hotwords
EXIT_PHRASES = ["exit Zia", "quit Zia", "shut down Zia", "shutdown Zia",
                "close Zia", "shut down", "shutdown"]
SLEEP_PHRASES = ["go to sleep", "sleep Zia", "Zia sleep", "standby", "sleep"]


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

    # Add user message to memory
    memory.add_user_message(text)

    matched = router.dispatch(text, ctx)
    if matched:
        st.last_activity = time.monotonic()
    else:
        log.info("No skill matched. Routing via Brain.")
        
        # Extract NLP context for better reasoning
        nlp_context = ""
        try:
            from core.nlp import extract_intent_entities, format_parsed_context
            parsed = extract_intent_entities(text)
            nlp_context = format_parsed_context(parsed)
            if nlp_context:
                text_with_context = text + nlp_context
            else:
                text_with_context = text
        except Exception as e:
            log.warning(f"NLP extraction failed: {e}")
            text_with_context = text

        category = brain.route_complexity(text)
        log.info(f"Brain classified intent as: {category}")
        
        if category == CommandComplexity.SIMPLE:
            compressed = brain.compress_prompt(text)
            if nlp_context:
                compressed += nlp_context
            response = generate_chat(memory.get_context(current_query=compressed), use_tools=False)
            ctx.say(response)
        else:
            if getattr(ctx, 'executor', None):
                response = ctx.executor.execute(text_with_context, ctx_memory=memory)
                ctx.say(response)
            else:
                log.info("Executor not initialized (Phase 3 pending). Falling back to basic LLM.")
                response = generate_chat(memory.get_context(current_query=text_with_context))
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

    asr = ASRPipeline(_wake_word_hit, _strip_wake_prefix, _dispatch, _go_sleep)

    # Start background proactive monitoring
    from core.proactive import start_proactive_monitoring
    start_proactive_monitoring(ctx, asr)

    setup_tray()

    try:
        asr.listen_loop(input_idx)
    except KeyboardInterrupt:
        log.info("Interrupted.")
        _go_shutdown()


if __name__ == "__main__":
    main()
