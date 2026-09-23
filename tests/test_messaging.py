from skills.messaging import (
    _Confirmer,
    _POSITIVE_RE,
    _NEGATIVE_RE,
    parse_message_command,
)


def test_parse_provider_aliases():
    assert parse_message_command("text Ayush saying I will be late on insta") == (
        "Ayush",
        "I will be late",
        "instagram",
    )
    assert parse_message_command("message Mom that I am home via Telegram") == (
        "Mom",
        "I am home",
        "telegram",
    )
    assert parse_message_command("text Alex hello on whatsapp web") == (
        "Alex",
        "hello",
        "whatsapp",
    )
    assert parse_message_command("send Sam to see you later on discord") == (
        "Sam",
        "see you later",
        "discord",
    )


def test_parse_message_requires_contact_and_message():
    assert parse_message_command("text Mom") is None


def test_message_command_without_text_is_rejected():
    """
    A message must always come from the user.

    This previously returned a hardcoded debug string registered for
    ("ayush", "instagram"), so "text @Ayush on Instagram" sent a canned
    "Heelo i am the best" to a real contact. Asking again is the safe behaviour.
    """
    assert parse_message_command("text @Ayush on Instagram") is None


# ---------------------------------------------------------------------------
# Confirmation channel (replaces the second microphone stream)
# ---------------------------------------------------------------------------
def test_confirmer_accepts_yes():
    confirmer = _Confirmer()
    assert confirmer.handle("yes send it") is True
    assert confirmer.wait(0.1) is True


def test_confirmer_rejects_no_even_with_send():
    confirmer = _Confirmer()
    # "do not send it" contains both a negative and "send"; negative must win,
    # otherwise a refusal would send the message.
    assert confirmer.handle("no do not send it") is True
    assert confirmer.wait(0.1) is False


def test_confirmer_ignores_unrelated_speech():
    confirmer = _Confirmer()
    assert confirmer.handle("what is the weather tomorrow") is False
    assert confirmer.wait(0.01) is None


def test_confirmation_patterns_use_word_boundaries():
    # Substring matching would read "yesterday" as "yes" and send by accident.
    assert _POSITIVE_RE.search("yesterday") is None
    assert _NEGATIVE_RE.search("nothing") is None
    assert _POSITIVE_RE.search("send it") is not None


def test_username_message_with_explicit_text():
    assert parse_message_command("text @friend saying Hello from Zia on Instagram") == (
        "@friend",
        "Hello from Zia",
        "instagram",
    )
