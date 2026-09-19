import time
from enum import Enum


class AssistantState(Enum):
    ASLEEP = 0   # Waiting for wake word
    AWAKE = 1    # Listening for commands

class State:
    def __init__(self):
        self.state = AssistantState.ASLEEP
        self.last_activity = time.monotonic()
        self.post_wake_until = 0.0

st = State()
