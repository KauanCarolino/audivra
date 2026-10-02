"""Mask audited values before they are stored."""

from typing import Any


def mask_text(value: Any, *, visible: int = 2) -> str | None:
    """Hide a value, keeping the last digits and the original separators.

    ``123.456.789-12`` becomes ``***.***.***-12``. Short values are fully masked.
    """
    if value is None:
        return None
    text = str(value)
    if not text:
        return ""
    digit_positions = [index for index, char in enumerate(text) if char.isdigit()]
    if digit_positions:
        revealed = set(digit_positions[-visible:]) if len(digit_positions) > visible else set()
        hidden = set(digit_positions) - revealed
        return "".join("*" if index in hidden else char for index, char in enumerate(text))
    if len(text) <= visible:
        return "*" * len(text)
    return ("*" * (len(text) - visible)) + text[-visible:]
