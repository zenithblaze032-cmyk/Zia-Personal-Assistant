import logging
import pyperclip
from pathlib import Path
import datetime

log = logging.getLogger(__name__)

def read_clipboard(match, ctx):
    try:
        text = pyperclip.paste()
        if text:
            # We truncate reading it so it doesn't speak forever
            speak_text = text[:200] + "..." if len(text) > 200 else text
            ctx.say(f"Your clipboard says: {speak_text}")
        else:
            ctx.say("Your clipboard is empty, sir.")
    except Exception as e:
        log.error(f"Clipboard error: {e}")
        ctx.say("I couldn't read the clipboard.")

def save_clipboard(match, ctx):
    try:
        text = pyperclip.paste()
        if text:
            notes_file = Path("local.txt").resolve()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(notes_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] Clipboard: {text}\n")
            ctx.say("Clipboard saved to notes.")
        else:
            ctx.say("There is nothing on the clipboard to save.")
    except Exception as e:
        log.error(f"Clipboard save error: {e}")
        ctx.say("I couldn't save the clipboard.")

def register(router):
    router.register(r"(?i)\bread my clipboard\b", read_clipboard)
    router.register(r"(?i)\bsave my clipboard(?: to notes)?\b", save_clipboard)
