from __future__ import annotations

import logging
import re
import threading
import time
import webbrowser

from core.context import Context
from core.pending import clear_interceptor, register_interceptor
from core.screen import click_element, focus_search, paste_text, press_key, type_into_element

log = logging.getLogger("Zia.skills.messaging")

# Each provider describes *where* to look, not a brittle fixed coordinate.
# The hint is fed to the vision grounding engine together with a region of
# interest (see core.screen.PROVIDER_ROIS) so the model only has to disambiguate
# inside a small crop instead of searching the whole screen.
PROVIDERS = {
    "whatsapp": {
        "aliases": {"whatsapp", "whatsapp web", "wa", "what's app", "what sapp"},
        "url": "https://web.whatsapp.com/",
        "window": "WhatsApp",
        "search_hint": "the search box at the top of the chat list on the left side",
        "input_hint": "the message text box at the bottom of the open chat",
    },
    "telegram": {
        "aliases": {"telegram", "telegram web", "tg"},
        "url": "https://web.telegram.org/a/",
        "window": "Telegram",
        "search_hint": "the search field at the top of the chat list",
        "input_hint": "the message input box at the bottom of the open chat",
    },
    "instagram": {
        "aliases": {"instagram", "insta", "ig", "insta gram"},
        "url": "https://www.instagram.com/direct/inbox/",
        "window": "Instagram",
        "search_hint": "the search field at the top of the direct messages list",
        "input_hint": "the message input box at the bottom of the open conversation",
    },
    "messenger": {
        "aliases": {"messenger", "facebook messenger", "fb messenger"},
        "url": "https://www.messenger.com/",
        "window": "Messenger",
        "search_hint": "the search field above the chat list",
        "input_hint": "the message input box at the bottom of the open chat",
    },
    "discord": {
        "aliases": {"discord"},
        "url": "https://discord.com/app",
        "window": "Discord",
        "search_hint": "the quick switcher search field",
        "input_hint": "the message input box at the bottom of the open channel",
    },
    "slack": {
        "aliases": {"slack"},
        "url": "https://app.slack.com/client",
        "window": "Slack",
        "search_hint": "the search field at the top of the window",
        "input_hint": "the message input box at the bottom of the open conversation",
    },
}

_PROVIDER_ALIASES = {
    alias: provider
    for provider, config in PROVIDERS.items()
    for alias in config["aliases"]
}

# NOTE: a hardcoded default message used to live here
# (``AUTOMATED_MESSAGES = {("ayush", "instagram"): "Heelo i am the best"}``).
# It meant "text Ayush on Instagram" silently sent a canned test string to a
# real person. A message must always come from the user, so that fallback is
# gone: an empty message now asks the user for the text instead.


def _normalize_provider(value: str) -> str | None:
    return _PROVIDER_ALIASES.get(" ".join(value.lower().split()))


def _provider_titles(provider: str) -> set[str]:
    """Window title fragments that identify a provider's browser tab/app."""
    config = PROVIDERS[provider]
    return {config["window"].lower(), *[a.lower() for a in config["aliases"]]}


def _find_provider_window(provider: str):
    """Return the first open window belonging to ``provider``, or None."""
    try:
        import pygetwindow as gw
    except ImportError:
        log.warning("Messaging: pygetwindow missing; cannot focus %s", provider)
        return None

    titles = _provider_titles(provider)
    for window in gw.getAllWindows():
        title = (window.title or "").lower()
        if title and any(fragment in title for fragment in titles):
            return window
    return None


def _focus_provider(provider: str, timeout: float | None = None) -> bool:
    """
    Focus the provider's window, opening the web app if it is not running.

    Replaces a blind ``time.sleep(10)`` with a poll for the window to actually
    appear, so a slow or partially-loaded page is not acted on too early — the
    main reason a search field could not be found straight after opening
    WhatsApp Web or Instagram.
    """
    from core.config import WEB_APP_READY_TIMEOUT

    if timeout is None:
        timeout = WEB_APP_READY_TIMEOUT

    config = PROVIDERS[provider]
    window = _find_provider_window(provider)

    if window is None:
        log.info("Messaging: opening %s at %s", provider, config["url"])
        try:
            webbrowser.open(config["url"])
        except Exception as exc:
            log.error("Messaging: could not open %s: %s", provider, exc)
            return False

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            time.sleep(1.0)
            window = _find_provider_window(provider)
            if window is not None:
                break
        else:
            log.warning("Messaging: %s window never appeared within %.0fs",
                        provider, timeout)
            return False

    try:
        window.restore()
        window.activate()
    except Exception:
        log.debug("Could not activate existing %s window",
                  provider, exc_info=True)

    # Give the tab a moment to paint after being raised.
    time.sleep(1.2)
    return True


def parse_message_command(command: str) -> tuple[str, str, str] | None:
    """Parse ``username``, ``message`` and ``provider`` from a voice command."""
    text = " ".join(command.strip().split())
    text = re.sub(r"^(?:message|text|send)\s+", "", text, flags=re.IGNORECASE)
    provider = "whatsapp"

    # Provider can appear anywhere: "on insta", "via Telegram", or "WhatsApp ...".
    provider_pattern = r"(?:\b(?:on|via|using)\s+)?(whatsapp(?:\s+web)?|what's\s+app|what\s+sapp|telegram(?:\s+web)?|tg|instagram|insta(?:\s+gram)?|ig|messenger|facebook\s+messenger|fb\s+messenger|discord|slack)\b"
    provider_match = re.search(provider_pattern, text, re.IGNORECASE)
    if provider_match:
        provider = _normalize_provider(provider_match.group(1)) or provider
        text = (text[:provider_match.start()] + " " +
                text[provider_match.end():]).strip()

    split_match = re.match(
        r"^(?P<person>.+?)\s+(?:saying|that)\s+(?P<message>.+)$", text, re.IGNORECASE)
    if not split_match:
        # Keep compatibility with the old form: "message Ayush to I am late".
        split_match = re.match(
            r"^(?P<person>.+?)\s+to\s+(?P<message>.+)$", text, re.IGNORECASE)
    if split_match:
        person = split_match.group("person").strip()
        message = split_match.group("message").strip()
    else:
        words = text.split(maxsplit=1)
        person, message = (words[0], words[1]) if len(
            words) == 2 else (text, "")

    message = message.strip()
    if not person or not message:
        return None
    return person, message, provider


# ---------------------------------------------------------------------------
# Verbal confirmation
#
# The previous implementation opened its own ``sr.Microphone()`` stream from
# inside the skill. The main ASR loop already owns that device and keeps reading
# it in another thread, so the two competed for the mic — and any reply spoken
# while Zia was still finishing her question was thrown away by the barge-in
# branch in core/asr.py.
#
# Confirmation is now routed through core.pending: the skill registers an
# interceptor, Zia.py and asr.py offer each transcript to it, and the skill
# waits on an event. One microphone owner, no contention, and an answer spoken
# during TTS is still heard.
# ---------------------------------------------------------------------------
_POSITIVE_RE = re.compile(
    r"\b(yes|yeah|yep|yup|sure|send(?:\s+it)?|confirm(?:ed)?|do\s+it|"
    r"go\s+ahead|ok(?:ay)?|correct|affirmative)\b")
# Checked before positives: "don't send it" contains both "don't" and "send".
_NEGATIVE_RE = re.compile(
    r"\b(no|nope|nah|don'?t|do\s+not|cancel|stop|abort|discard|negative|wait)\b")


class _Confirmer:
    """Consumes the next yes/no answer without touching the microphone."""

    def __init__(self) -> None:
        self._event = threading.Event()
        self.answer: bool | None = None

    def handle(self, text: str) -> bool:
        lowered = (text or "").lower()
        if _NEGATIVE_RE.search(lowered):
            self.answer = False
            self._event.set()
            return True
        if _POSITIVE_RE.search(lowered):
            self.answer = True
            self._event.set()
            return True
        # Unrelated speech is not ours to consume — let it route normally.
        return False

    def wait(self, timeout: float) -> bool | None:
        self._event.wait(timeout)
        return self.answer


def _confirm_and_send(ctx: Context, person: str, provider: str,
                      timeout: float = 20.0) -> bool:
    """
    Ask whether to send, and only press Enter on an explicit yes.

    A timeout or an explicit no leaves the text sitting in the chat box
    unsent rather than guessing.
    """
    confirmer = _Confirmer()
    register_interceptor(confirmer.handle)
    try:
        ctx.say(f"The message for {person} is ready. Should I send it?")
        answer = confirmer.wait(timeout)
    finally:
        clear_interceptor(confirmer.handle)

    if answer is True:
        press_key("enter")
        time.sleep(0.6)
        return True

    if answer is None:
        log.info("Messaging: no confirmation heard within %.0fs", timeout)
    else:
        log.info("Messaging: user declined to send")
    return False


def _handle_message(match: re.Match, ctx: Context) -> None:
    parsed = parse_message_command(match.group("full_command"))
    if not parsed:
        ctx.say("I didn't catch the message you wanted to send.")
        return

    person, message, provider = parsed
    config = PROVIDERS[provider]
    recipient = person.strip().lstrip("@")
    ctx.say(f"Using {provider} to message {recipient}.")

    if not _focus_provider(provider):
        ctx.say(f"I couldn't open {provider}, sir.")
        return

    # 1. Focus the search field: exact shortcut first, then vision grounding
    #    constrained to the provider's search region of interest.
    ok, detail = focus_search(provider, description=config["search_hint"])
    if not ok:
        log.info("Messaging: %s search focus failed (%s); grounding instead",
                 provider, detail)
        ok, detail = click_element(config["search_hint"],
                                   provider=provider, role="search")
    if not ok:
        log.error("Messaging: could not focus %s search: %s", provider, detail)
        ctx.say("I couldn't find the search bar, so I stopped.")
        return
    time.sleep(0.5)

    # 2. Look the contact up and open the conversation.
    paste_text(recipient)
    time.sleep(1.6)
    press_key("enter")
    time.sleep(1.6)

    # 3. Write into the composer, verifying that the text actually landed.
    ok, detail = type_into_element(
        config["input_hint"], message, provider=provider, role="input")
    if not ok:
        log.info("Messaging: composer ROI attempt failed (%s); retrying full screen",
                 detail)
        ok, detail = type_into_element(config["input_hint"], message)
    if not ok:
        log.error("Messaging: composer not verified for %s: %s", provider, detail)
        ctx.say("I couldn't put the message in the chat box, "
                "so I have not sent anything.")
        return

    # 4. Confirm before sending anything.
    if _confirm_and_send(ctx, recipient, provider):
        ctx.say(f"Message sent to {recipient} on {provider}.")
    else:
        ctx.say("Okay, I have not sent it. The text is still in the chat box.")


def register(router) -> None:
    # Examples: "text Ayush saying I will be late on insta" or "message Mom that I am home on telegram".
    pattern = r"(?i)\b(?:message|text|send|whatsapp|telegram|instagram|insta|messenger|discord|slack)\s+(?P<full_command>.+)"
    router.register(pattern, _handle_message)
