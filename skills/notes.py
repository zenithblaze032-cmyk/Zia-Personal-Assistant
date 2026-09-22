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
        if ctx.memory:
            ctx.memory.add_long_term_memory(note)
        ctx.say("Note saved.")
    except Exception as e:
        log.error(f"Failed to save note: {e}")
        ctx.say("I couldn't save the note.")

def register(router):
    router.register(
        pattern=r"(?i)\b(?:take a note that|remind me to|note down|remember that|remember)\s+(?P<note>.+)",
        handler=take_note
    )
