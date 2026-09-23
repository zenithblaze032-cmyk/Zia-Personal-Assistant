from skills.messaging import parse_message_command


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


def test_ayush_instagram_automation_message():
    assert parse_message_command("text @Ayush on Instagram") == (
        "@Ayush",
        "Heelo i am the best",
        "instagram",
    )


def test_username_message_with_explicit_text():
    assert parse_message_command("text @friend saying Hello from Zia on Instagram") == (
        "@friend",
        "Hello from Zia",
        "instagram",
    )
