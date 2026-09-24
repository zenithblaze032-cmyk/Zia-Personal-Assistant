import time
from enum import Enum


class AssistantState(Enum):
    ASLEEP = 0   # Waiting for wake word
    AWAKE = 1    # Listening for commands
    WHATSAPP_PREPARING = 2
    WHATSAPP_AWAITING_CONFIRMATION = 3
    WHATSAPP_SENDING = 4

class State:
    def __init__(self):
        self.state = AssistantState.ASLEEP
        self.last_activity = time.monotonic()
        self.post_wake_until = 0.0

st = State()
