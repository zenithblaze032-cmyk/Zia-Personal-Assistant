import logging
from typing import Dict, Any
from core.llm import generate_chat
from core.config import USE_EFFGEN

class CommandComplexity:
    SIMPLE = "SIMPLE"
    TOOL = "TOOL"
    MULTI_STEP = "MULTI_STEP"

class Brain:
    """
    EffGen-powered routing and prompt optimization.
    """
    def __init__(self):
        if USE_EFFGEN:
            try:
                from effgen.prompts.optimizer import PromptOptimizer
                self.optimizer = PromptOptimizer()
            except ImportError:
                self.optimizer = None
        else:
            self.optimizer = None

    def route_complexity(self, text: str) -> str:
        """
        Classifies a user command into SIMPLE, TOOL, or MULTI_STEP.
        """
        t = text.lower()
        
        # Deterministic Heuristics
        multi_step_keywords = ["search", "find", "read", "summarize", "research", "look up", "navigate"]
        if any(k in t for k in multi_step_keywords):
            return CommandComplexity.MULTI_STEP
            
        tool_keywords = ["weather", "calculate", "math"]
        if any(k in t for k in tool_keywords):
            return CommandComplexity.TOOL
            
        return CommandComplexity.SIMPLE

    def compress_prompt(self, text: str) -> str:
        if self.optimizer:
            try:
                result = self.optimizer.optimize(text)
                return result.optimized_prompt
            except Exception as e:
                logging.error(f"EffGen prompt compression failed: {e}")
        return text
