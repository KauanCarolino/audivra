"""AUDIVRA settings namespace."""

from typing import Any

from django.conf import settings

from audivra.exceptions import ConfigurationError

BACKENDS = frozenset({"sync", "outbox", "celery"})

BUILTIN_SENSITIVE_FIELDS = frozenset(
    {
        "password",
        "password_hash",
        "token",
        "access_token",
        "refresh_token",
        "secret",
        "api_key",
        "private_key",
    }
)

DEFAULTS: dict[str, Any] = {
    "BACKEND": "outbox",
    "RETENTION_DAYS": None,
    "TRACK_REQUEST_CONTEXT": True,
    "DEFAULT_EXCLUDE_FIELDS": sorted(BUILTIN_SENSITIVE_FIELDS),
}


def get_config() -> dict[str, Any]:
    """Return AUDIVRA settings merged with defaults."""
    configured = getattr(settings, "AUDIVRA", {})
    if not isinstance(configured, dict):
        raise ConfigurationError("AUDIVRA must be a dict.")

    unknown = set(configured) - set(DEFAULTS)
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ConfigurationError(f"Unknown AUDIVRA settings: {names}.")

    merged = {**DEFAULTS, **configured}
    merged["DEFAULT_EXCLUDE_FIELDS"] = list(merged["DEFAULT_EXCLUDE_FIELDS"])
    if merged["BACKEND"] not in BACKENDS:
        raise ConfigurationError(f"AUDIVRA BACKEND must be one of: {', '.join(sorted(BACKENDS))}.")
    return merged
