from __future__ import annotations

import logging
import re
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.context import Context

log = logging.getLogger("Zia.router")


class Router:
    """
    Lightweight regex-based command dispatcher.

    Skills register (pattern, handler) pairs. On each utterance,
    the router tries every pattern in registration order and calls
    the first match. If no pattern matches, dispatch() returns False.
    """

    def __init__(self) -> None:
        self._routes: list[tuple[re.Pattern, Callable]] = []

    def register(self, pattern: str, handler: Callable) -> None:
        """Register a handler for a regex pattern. Case-insensitive by default."""
        self._routes.append((re.compile(pattern, re.IGNORECASE), handler))

    def dispatch(self, text: str, ctx: Context) -> bool:
        """
        Try each registered pattern against text.
        Calls the first matching handler and returns True.
        Returns False if nothing matched.

        All handler exceptions are caught here — a broken skill never
        crashes Zia. The error is logged and ctx.say() delivers a
        fallback line to the user.
        """
        for pattern, handler in self._routes:
            m = pattern.search(text)
            if m:
                try:
                    handler(m, ctx)
                except Exception:
                    log.exception(
                        "Unhandled error in skill handler '%s':", handler.__name__)
                    ctx.say("Something went wrong, sir.")
                return True
        return False
