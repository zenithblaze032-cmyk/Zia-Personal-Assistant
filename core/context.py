from __future__ import annotations

from collections.abc import Callable


class Context:
    """
    Passed to every skill handler. Completely decouples skills from Zia.py.

    Skills must only use ctx.say(), ctx.sleep(), ctx.shutdown().
    They must NOT import anything from core/ or Zia.py directly.
    """

    def __init__(
        self,
        say_fn: Callable[[str], None],
        sleep_fn: Callable[[], None],
        shutdown_fn: Callable[[], None],
    ) -> None:
        self._say = say_fn
        self._sleep = sleep_fn
        self._shutdown = shutdown_fn

    def say(self, text: str) -> None:
        """Speak text via TTS (non-blocking from the caller's perspective)."""
        self._say(text)

    def sleep(self) -> None:
        """Tell Zia to go back to ASLEEP state."""
        self._sleep()

    def shutdown(self) -> None:
        """Clean up and exit the Zia process."""
        self._shutdown()
