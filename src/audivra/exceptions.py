class AudivraError(Exception):
    """Base exception for audivra."""


class ConfigurationError(AudivraError):
    """Invalid AUDIVRA configuration."""
