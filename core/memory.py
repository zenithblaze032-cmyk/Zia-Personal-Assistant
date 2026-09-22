import os
import logging
from collections import deque
from typing import List, Dict
from core.config import USE_EFFGEN

if USE_EFFGEN:
    try:
        from effgen import LongTermMemory, MemoryType, ImportanceLevel, SQLiteStorageBackend
        # Initialize effgen long term memory (RAG)
        _backend = SQLiteStorageBackend(os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory.db"))
        _ltm = LongTermMemory(backend=_backend)
        _ltm.start_session(name="zia_default_session")
    except ImportError:
        _ltm = None
else:
    _ltm = None

class Memory:
    """
    Short-term memory buffer for maintaining conversation context, 
    with EffGen LongTermMemory RAG integration.
    """
    def __init__(self, max_turns: int = 5):
        self.messages = deque(maxlen=max_turns * 2)
        self.system_prompt = {
            "role": "system",
            "content": (
                "You are Zia, a highly capable, concise, and helpful AI assistant. "
                "You are installed on the user's local PC to help them with tasks. "
                "Keep responses brief, natural, and helpful. "
                "Do not use markdown formatting like asterisks or bold text, because your responses will be read aloud via Text-to-Speech."
            )
        }

    def add_user_message(self, text: str):
        self.messages.append({"role": "user", "content": text})

    def add_assistant_message(self, text: str):
        self.messages.append({"role": "assistant", "content": text})
        
    def add_long_term_memory(self, text: str):
        """Saves a fact into long-term RAG memory."""
        if _ltm:
            try:
                _ltm.add_memory(
                    content=text, 
                    memory_type=MemoryType.FACT, 
                    importance=ImportanceLevel.HIGH
                )
                logging.info(f"Saved to LTM: {text}")
            except Exception as e:
                logging.error(f"Failed to add LTM: {e}")
        else:
            # Fallback to simple txt
            with open("memory.txt", "a", encoding="utf-8") as f:
                f.write(text + "\n")

    def get_context(self, current_query: str = None) -> List[Dict[str, str]]:
        system_prompt_copy = self.system_prompt.copy()
        
        # RAG Injection
        if _ltm and current_query:
            try:
                results = _ltm.search(query=current_query, limit=3)
                if results:
                    rag_context = "\n".join(r.content for r in results)
                    system_prompt_copy["content"] += "\n\nRelevant Memories:\n" + rag_context
            except Exception as e:
                logging.error(f"LTM search failed: {e}")
        elif not _ltm:
            # Fallback
            memory_file = "memory.txt"
            if os.path.exists(memory_file):
                try:
                    with open(memory_file, "r", encoding="utf-8") as f:
                        memory_content = f.read().strip()
                    if memory_content:
                        system_prompt_copy["content"] += "\n\nUser Notes and Preferences:\n" + memory_content
                except Exception as e:
                    pass
                
        return [system_prompt_copy] + list(self.messages)

    def clear(self):
        self.messages.clear()
