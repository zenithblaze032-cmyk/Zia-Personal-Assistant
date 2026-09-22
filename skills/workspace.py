import logging
from core.router import Router
from core.context import Context

log = logging.getLogger(__name__)

def register(router: Router) -> None:
    router.register(
        r".*get back to dsa work.*",
        _dsa_work
    )
    router.register(
        r".*get back to development work.*",
        _dev_work
    )
    router.register(
        r".*get back to improve you.*",
        _zia_work
    )

def _dsa_work(match, ctx: Context) -> None:
    from core.state import st
    from core.workspace import run_workspace_launch
    import threading
    
    if not getattr(st, 'dsa_workspace_launched', False):
        st.dsa_workspace_launched = True
        log.info("Launching DSA workspace on command.")
        threading.Thread(target=run_workspace_launch, kwargs={
                         "mode": "dsa"}, daemon=True).start()
    else:
        ctx.say("The DSA workspace is already open, sir.")

def _dev_work(match, ctx: Context) -> None:
    from core.state import st
    from core.workspace import run_workspace_launch
    import threading
    
    if not getattr(st, 'dev_workspace_launched', False):
        st.dev_workspace_launched = True
        log.info("Launching Dev workspace on command.")
        threading.Thread(target=run_workspace_launch, kwargs={
                         "mode": "dev"}, daemon=True).start()
    else:
        ctx.say("The Dev workspace is already open, sir.")

def _zia_work(match, ctx: Context) -> None:
    from core.state import st
    from core.workspace import run_workspace_launch
    import threading
    
    if not getattr(st, 'zia_workspace_launched', False):
        st.zia_workspace_launched = True
        log.info("Launching Zia workspace on command.")
        threading.Thread(target=run_workspace_launch, kwargs={
                         "mode": "Zia"}, daemon=True).start()
    else:
        ctx.say("The Zia workspace is already open, sir.")
