import logging
import threading
import time

log = logging.getLogger(__name__)

def _timer_done(ctx, duration):
    ctx.say(f"Sir, your timer for {duration} seconds is up.")

def set_timer(match, ctx):
    raw_duration = match.group("duration")
    try:
        duration = int(raw_duration)
        threading.Timer(duration, _timer_done, args=[ctx, duration]).start()
        ctx.say(f"Timer set for {duration} seconds.")
    except ValueError:
        ctx.say("I couldn't understand the duration for the timer.")

def register(router):
    router.register(r"(?i)\bset a timer for (?P<duration>\d+)\s+seconds?\b", set_timer)
