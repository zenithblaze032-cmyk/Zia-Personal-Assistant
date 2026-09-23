import re
import logging
import time
import pyautogui
import speech_recognition as sr
from core.context import Context
from core.tools import type_on_screen

log = logging.getLogger("Zia.skills.messaging")

PROVIDERS = {
    "whatsapp": {
        "aliases": {"whatsapp", "whatsapp web", "wa", "what's app", "what sapp"},
        "url": "https://web.whatsapp.com/",
        "window": "WhatsApp",
        "search": "WhatsApp chat search bar",
        "input": "WhatsApp type a message box at the bottom",
    },
    "telegram": {
        "aliases": {"telegram", "telegram web", "tg"},
        "url": "https://web.telegram.org/a/",
        "window": "Telegram",
        "search": "Telegram chat search field",
        "input": "Telegram message input box at the bottom",
    },
    "instagram": {
        "aliases": {"instagram", "insta", "ig", "insta gram"},
        "url": "https://www.instagram.com/direct/inbox/",
        "window": "Instagram",
        "search": "Instagram direct messages search field",
        "input": "Instagram direct message input box",
    },
    "messenger": {
        "aliases": {"messenger", "facebook messenger", "fb messenger"},
        "url": "https://www.messenger.com/",
        "window": "Messenger",
        "search": "Messenger chat search field",
        "input": "Messenger message input box",
    },
    "discord": {
        "aliases": {"discord"},
        "url": "https://discord.com/app",
        "window": "Discord",
        "search": "Discord direct message search field",
        "input": "Discord message input box",
    },
    "slack": {
        "aliases": {"slack"},
        "url": "https://app.slack.com/client",
        "window": "Slack",
        "search": "Slack search field",
        "input": "Slack message input box",
    },
}

_PROVIDER_ALIASES = {
    alias: provider
    for provider, config in PROVIDERS.items()
    for alias in config["aliases"]
}

AUTOMATED_MESSAGES = {
    ("ayush", "instagram"): "Heelo i am the best",
}


def _normalize_provider(value: str) -> str | None:
    return _PROVIDER_ALIASES.get(" ".join(value.lower().split()))


def _recipient_key(value: str) -> str:
    """Normalize a spoken username for automation lookup."""
    return value.strip().lstrip("@").lower()


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

    message = message or AUTOMATED_MESSAGES.get(
        (_recipient_key(person), provider), "")
    if not person or not message:
        return None
    return person, message, provider


def _focus_provider(provider: str) -> bool:
    import webbrowser
    import pygetwindow as gw

    config = PROVIDERS[provider]
    titles = {config["window"].lower(), *config["aliases"]}
    windows = [
        window
        for window in gw.getAllWindows()
        if any(title in (window.title or "").lower() for title in titles)
    ]
    if windows:
        try:
            windows[0].restore()
            windows[0].activate()
        except Exception:
            log.debug("Could not activate existing %s window",
                      provider, exc_info=True)
        time.sleep(1.5)
        return True
    else:
        webbrowser.open(config["url"])
        time.sleep(10)
        return True


def _confirm_and_send(ctx: Context) -> bool:
    ctx.say("The message is ready. Should I send it?")
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            audio = recognizer.listen(source, timeout=7, phrase_time_limit=5)
            response = recognizer.recognize_google(audio).lower()
            if any(word in response for word in ("yes", "send", "yeah", "do it")):
                pyautogui.press("enter")
                return True
        except sr.WaitTimeoutError:
            pass
        except Exception:
            log.exception("Error during messaging confirmation")
    return False


def _handle_message(match: re.Match, ctx: Context) -> None:
    parsed = parse_message_command(match.group("full_command"))
    if not parsed:
        ctx.say("I didn't catch the message you wanted to send.")
        return

    person, message, provider = parsed
    config = PROVIDERS[provider]
    ctx.say(f"Using {provider} to message {person}.")
    _focus_provider(provider)

    search_res = type_on_screen(config["search"], person)
    if "Error" in search_res or "Failed" in search_res:
        log.error("Vision failed for %s search bar: %s", provider, search_res)
        ctx.say("I couldn't find the search bar on screen.")
        return
    time.sleep(1.5)
    pyautogui.press("enter")
    time.sleep(1)

    msg_res = type_on_screen(config["input"], message)
    if "Error" in msg_res or "Failed" in msg_res:
        log.error("Vision failed for %s message field: %s", provider, msg_res)
        ctx.say("I couldn't find the message box.")
        return

    if _confirm_and_send(ctx):
        ctx.say(f"Message sent on {provider}.")
    else:
        ctx.say("Okay, I will not send it.")


def register(router) -> None:
    # Examples: "text Ayush saying I will be late on insta" or "message Mom that I am home on telegram".
    pattern = r"(?i)\b(?:message|text|send|whatsapp|telegram|instagram|insta|messenger|discord|slack)\s+(?P<full_command>.+)"
    router.register(pattern, _handle_message)
