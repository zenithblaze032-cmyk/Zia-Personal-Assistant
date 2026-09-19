from __future__ import annotations

import logging
import re
import urllib.parse
import webbrowser
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.context import Context
    from core.router import Router

log = logging.getLogger("Zia.skills.web")


def _handle_google_search(match: re.Match, ctx: Context) -> None:
    query = match.group("query").strip()
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    log.info("Google search: %r", query)
    webbrowser.open(url)
    ctx.say(f"Searching for {query}.")


def _handle_youtube_search(match: re.Match, ctx: Context) -> None:
    query = match.group("query").strip()
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    log.info("YouTube search: %r", query)
    webbrowser.open(url)
    ctx.say(f"Playing {query} on YouTube, sir.")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
PATTERNS = [
    # Google search: "search for X", "google X", "look up X"
    (r"^(?:search|google|look up)\s+(?:for\s+)?(?P<query>.+?)$", _handle_google_search),
    # YouTube: "play X on youtube", "find X on youtube"
    (r"^(?:play|find)\s+(?P<query>.+?)\s+on youtube$", _handle_youtube_search),
]


def register(router: Router) -> None:
    for pattern, handler in PATTERNS:
        router.register(pattern, handler)
