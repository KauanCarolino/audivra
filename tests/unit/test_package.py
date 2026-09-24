from audivra import audit
from audivra.version import __version__


def test_should_export_audit_api() -> None:
    assert callable(audit.register)
    assert callable(audit.unregister)
    assert callable(audit.record)
    assert callable(audit.history)


def test_should_expose_initial_version() -> None:
    assert __version__ == "0.1.0"
