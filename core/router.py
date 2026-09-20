from __future__ import annotations

import logging
import re
from collections.abc import Callable
from typing import TYPE_CHECKING, List, Tuple
import numpy as np

if TYPE_CHECKING:
    from core.context import Context

from core.llm import generate_embedding

log = logging.getLogger("Zia.router")


def cosine_similarity(a: List[float], b: List[float]) -> float:
    a_arr = np.array(a)
    b_arr = np.array(b)
    if np.linalg.norm(a_arr) == 0 or np.linalg.norm(b_arr) == 0:
        return 0.0
    return np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr))


class Router:
    """
    Command dispatcher supporting regex routes and fuzzy intent matching via text embeddings.
    """

    def __init__(self) -> None:
        self._routes: list[tuple[re.Pattern, Callable]] = []
        self._intents: list[tuple[List[float], Callable]] = []
        self._similarity_threshold = 0.70  # adjust based on embedding model testing

    def register(self, pattern: str, handler: Callable) -> None:
        """Register a handler for a regex pattern. Case-insensitive by default."""
        self._routes.append((re.compile(pattern, re.IGNORECASE), handler))

    def register_intent(self, examples: List[str], handler: Callable) -> None:
        """
        Register a handler for natural language examples.
        Pre-computes the embeddings for the examples.
        """
        for example in examples:
            emb = generate_embedding(example)
            if emb:
                self._intents.append((emb, handler))
            else:
                log.warning(f"Failed to generate embedding for intent example: {example}")

    def dispatch(self, text: str, ctx: Context) -> bool:
        """
        1. Try each registered regex pattern against text.
        2. If no regex match, try fuzzy matching against registered intents.
        Calls the first matching handler and returns True.
        Returns False if nothing matched or similarity is below threshold.
        """
        # 1. Regex Exact / Substring Matches
        for pattern, handler in self._routes:
            m = pattern.search(text)
            if m:
                try:
                    handler(m, ctx)
                except Exception:
                    log.exception("Unhandled error in regex skill handler '%s':", handler.__name__)
                    ctx.say("Something went wrong with that skill, sir.")
                return True
                
        # 2. Fuzzy Intent Matching via Embeddings
        if self._intents:
            text_emb = generate_embedding(text)
            if text_emb:
                best_score = 0.0
                best_handler = None
                
                for intent_emb, handler in self._intents:
                    score = cosine_similarity(text_emb, intent_emb)
                    if score > best_score:
                        best_score = score
                        best_handler = handler
                
                if best_handler and best_score >= self._similarity_threshold:
                    log.info(f"Fuzzy intent match found with score {best_score:.2f}")
                    try:
                        # We pass None for the regex match object in fuzzy matching
                        best_handler(None, ctx)
                    except Exception:
                        log.exception("Unhandled error in fuzzy skill handler '%s':", best_handler.__name__)
                        ctx.say("Something went wrong executing that intent, sir.")
                    return True
                else:
                    log.debug(f"No intent matched above threshold (best score: {best_score:.2f})")

        return False

