class AudivraError(Exception):
    """Base exception for audivra."""


class ConfigurationError(AudivraError):
    """Invalid AUDIVRA configuration."""


class ImmutabilityError(AudivraError):
    """Raised when code tries to change or delete an AuditLog."""
