"""
Zia Skills Package
=====================
Importing this package and calling register_all(router) loads every skill
into the router. To add a new skill:
  1. Create a new module in skills/ with a register(router) function.
  2. Import it here and add it to the list below.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.router import Router

import logging

log = logging.getLogger("Zia.skills")


def register_all(router: Router) -> None:
    """Register every skill module with the router, in priority order."""
    from skills import routines, apps, media, system, web, notes, weather, timers, clipboard, window_manager, automation, workspace

    # Registration order matters: first match wins.
    # More specific patterns should come before broad ones.
    for module in (workspace, routines, web, system, media, apps, notes, weather, timers, clipboard, window_manager, automation):
        try:
            module.register(router)
            log.debug("Registered skill module: %s", module.__name__)
        except Exception:
            log.exception(
                "Failed to register skill module '%s' — skipping.", module.__name__)
