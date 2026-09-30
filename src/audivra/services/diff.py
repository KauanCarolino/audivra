"""Compare two field maps and keep only real changes."""

from collections.abc import Mapping
from typing import Any


def diff_values(old: Mapping[str, Any], new: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Return `{field: {"old", "new"}}` for values that are not equal."""
    changes: dict[str, dict[str, Any]] = {}
    for name in sorted(set(old) | set(new)):
        before = old.get(name)
        after = new.get(name)
        if before != after:
            changes[name] = {"old": before, "new": after}
    return changes
