from collections import deque
from typing import List, Dict
import os
import logging

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
        Returns the conversation history including the system prompt and long-term memory.
        """
        system_prompt_copy = self.system_prompt.copy()
        
        # Read long-term memory if it exists
        memory_file = "memory.txt"
        if os.path.exists(memory_file):
            try:
                with open(memory_file, "r", encoding="utf-8") as f:
                    memory_content = f.read().strip()
                if memory_content:
                    system_prompt_copy["content"] += "\n\nUser Notes and Preferences (Long-Term Memory):\n" + memory_content
            except Exception as e:
                logging.getLogger(__name__).error(f"Failed to read memory file: {e}")
                
        return [system_prompt_copy] + list(self.messages)

    def clear(self):
        self.messages.clear()
