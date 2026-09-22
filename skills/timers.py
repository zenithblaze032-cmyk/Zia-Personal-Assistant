import logging
import threading
import time

log = logging.getLogger(__name__)

def _timer_done(ctx, duration):
    ctx.say(f"Sir, your timer for {duration} seconds is up.")

def set_timer(match, ctx):
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)
    
    total_seconds = hours * 3600 + minutes * 60 + seconds
    
    if total_seconds <= 0:
        ctx.say("I couldn't understand the duration for the timer.")
        return
        
    threading.Timer(total_seconds, _timer_done, args=[ctx, total_seconds]).start()
    
    parts = []
    if hours: parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes: parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds: parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    ctx.say(f"Timer set for {' and '.join(parts)}.")

def register(router):
    # Regex to capture optional hours, minutes, and seconds
    pattern = r"(?i)\bset a timer for(?:\s+(?P<hours>\d+)\s+hours?)?(?:\s+(?P<minutes>\d+)\s+minutes?)?(?:\s+(?P<seconds>\d+)\s+seconds?)?\b"
    router.register(pattern, set_timer)
