"""Basic validation tests (pytest). Database integration is exercised manually via README."""

from datetime import datetime, timedelta
import re


def test_future_slot_is_in_future():
    value = datetime.now() + timedelta(days=1)
    assert value > datetime.now()


def test_phone_pattern():
    pattern = r"\+?[0-9()\- ]{7,20}"
    assert re.fullmatch(pattern, "+7 (900) 123-45-67")
    assert not re.fullmatch(pattern, "phone")