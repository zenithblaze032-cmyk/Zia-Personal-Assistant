import pytest
from core.router import Router
from core.context import Context

def test_router_dispatch():
    router = Router()
    
    # We would need to mock a context and register a skill, but we can do a basic test
    class MockContext(Context):
        def __init__(self):
            super().__init__(lambda x: None, lambda: None, lambda: None)
            self.spoken = []
        def say(self, text):
            self.spoken.append(text)
            
    ctx = MockContext()
    
    # Normally we would register skills here, but since the core doesn't register by default,
    # we just test that dispatching an unknown command returns False
    result = router.dispatch("this is an unknown command", ctx)
    assert result is False
