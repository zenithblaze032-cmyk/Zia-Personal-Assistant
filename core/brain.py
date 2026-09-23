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
        # If heuristics miss, fallback to LLM for accurate routing
        prompt = (
            "Classify the following command into exactly one of three categories: "
            "SIMPLE, TOOL, or MULTI_STEP.\n\n"
            "Categories:\n"
            "- SIMPLE: Basic questions, greetings, or things an LLM can answer directly.\n"
            "- TOOL: Commands that require running exactly one specific tool (like weather, memory retrieval, open app).\n"
            "- MULTI_STEP: Complex requests needing multiple steps or AgentNova.\n\n"
            f"Command: '{text}'\n\n"
            "Reply ONLY with the category name (e.g. SIMPLE), nothing else."
        )
        
        try:
            from core.state import st
            if st.zen_mode:
                from core.llm_zen import generate_zen_chat
                result = generate_zen_chat([{"role": "user", "content": prompt}], use_tools=False)
            else:
                result = generate_chat([{"role": "user", "content": prompt}], use_tools=False)
                
            result = result.strip().upper()
            
            for cat in [CommandComplexity.SIMPLE, CommandComplexity.TOOL, CommandComplexity.MULTI_STEP]:
                if cat in result:
                    return cat
        except Exception as e:
            logging.error(f"Brain intent classification failed: {e}")
            
        return CommandComplexity.SIMPLE

    def compress_prompt(self, text: str) -> str:
        if self.optimizer:
            try:
                result = self.optimizer.optimize(text)
                return result.optimized_prompt
            except Exception as e:
                logging.error(f"EffGen prompt compression failed: {e}")
        return text
