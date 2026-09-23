"""
Regression tests for vision command routing.

The bug being locked down: skills/automation.py had a greedy ``\b(click)\b``
pattern that matched "click on the Submit button" *before* any vision handler
existed, so the command performed a blind click at the current cursor position
and the grounding engine was never invoked. Same for
"type hello into the search bar", which typed the whole literal sentence.

These tests assert which handler wins for a given utterance, without touching
the screen or the network.
"""

import re

import pytest

from skills import automation


def _first_handler(text: str):
    """Mirror the router: first pattern that matches wins."""
    for pattern, handler in automation.PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return handler.__name__
    return None


@pytest.mark.parametrize("text,expected", [
    ("click on the submit button", "_handle_vision_click"),
    ("click the search bar", "_handle_vision_click"),
    ("tap the X icon", "_handle_vision_click"),
    ("type hello into the search bar", "_handle_vision_type"),
    ("write I am late in the message box", "_handle_vision_type"),
    ("go to the search bar", "_handle_focus_search"),
    ("focus the search bar", "_handle_focus_search"),
])
def test_vision_commands_route_to_vision_handlers(text, expected):
    assert _first_handler(text) == expected


@pytest.mark.parametrize("text,expected", [
    ("click", "_handle_click"),
    ("double click", "_handle_click"),
    ("right click", "_handle_click"),
    ("press enter", "_handle_press_key"),
    ("mouse up by 50", "_handle_move_mouse"),
])
def test_blind_commands_still_work(text, expected):
    """Tightening the vision patterns must not break the direct commands."""
    assert _first_handler(text) == expected
