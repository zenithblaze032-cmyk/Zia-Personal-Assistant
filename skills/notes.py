import logging
import datetime
from pathlib import Path
import os

log = logging.getLogger(__name__)

def take_note(match, ctx):
    note = match.group("note").strip()
    if not note:
        ctx.say("I didn't catch the note.")
        return
        
    try:
        notes_file = Path("memory.txt").resolve()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(notes_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {note}\n")
            
        log.info(f"Note saved to {notes_file}")
        ctx.say("Note saved.")
    except Exception as e:
        log.error(f"Failed to save note: {e}")
        ctx.say("I couldn't save the note.")

def register(router):
    router.register(
        pattern=r"(?i)\b(?:take a note that|remind me to|note down|remember that|remember)\s+(?P<note>.+)",
        handler=take_note
    )
