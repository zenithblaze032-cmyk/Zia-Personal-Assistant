from collections import deque
from typing import List, Dict

class Memory:
    """
    Short-term memory buffer for maintaining conversation context.
    """
    def __init__(self, max_turns: int = 5):
        # We store max_turns pairs of user/assistant messages.
        # This translates to max_turns * 2 messages in the deque.
        self.messages = deque(maxlen=max_turns * 2)
        # Always inject a system prompt so the LLM knows its identity
        self.system_prompt = {
            "role": "system",
            "content": (
                "You are Zia, a highly capable, concise, and helpful AI assistant. "
                "You are installed on the user's local PC to help them with tasks, "
                "coding, and answering questions. Keep responses brief, natural, and helpful. "
                "Do not use markdown formatting like asterisks or bold text, because your responses will be read aloud via Text-to-Speech."
            )
        }

    def add_user_message(self, text: str):
        self.messages.append({"role": "user", "content": text})

    def add_assistant_message(self, text: str):
        self.messages.append({"role": "assistant", "content": text})

    def get_context(self) -> List[Dict[str, str]]:
        """
        Returns the conversation history including the system prompt.
        """
        return [self.system_prompt] + list(self.messages)

    def clear(self):
        self.messages.clear()
