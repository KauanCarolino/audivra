import pytest
from django.contrib.auth.models import User

from audivra import audit
from audivra.exceptions import ConfigurationError
from audivra.integrations.django.registry import registry


@pytest.fixture(autouse=True)
def _clear_registry() -> None:
    registry.clear()


def test_should_exclude_sensitive_fields_by_default() -> None:
    audit.register(User, include=["username", "email", "password"])
    config = registry.get(User)
    assert config is not None
    assert config.audited_field_names() == frozenset({"username", "email"})


def test_should_let_exclude_override_include() -> None:
    audit.register(User, include=["username", "email"], exclude=["email"])
    config = registry.get(User)
    assert config is not None
    assert config.audited_field_names() == frozenset({"username"})


def test_should_audit_concrete_fields_when_include_is_omitted() -> None:
    audit.register(User)
    config = registry.get(User)
    assert config is not None
    names = config.audited_field_names()
    assert "username" in names
    assert "password" not in names


def test_should_reject_unknown_fields() -> None:
    with pytest.raises(ConfigurationError):
        audit.register(User, include=["missing"])


def test_should_reject_mask_on_excluded_field() -> None:
    with pytest.raises(ConfigurationError):
        audit.register(User, mask=["password"])


def test_should_store_mask_for_audited_fields() -> None:
    audit.register(User, include=["username", "email"], mask=["email"])
    config = registry.get(User)
    assert config is not None
    assert config.mask == frozenset({"email"})
    assert "email" in config.audited_field_names()


def test_should_unregister_model() -> None:
    audit.register(User)
    audit.unregister(User)
    assert registry.get(User) is None
    with pytest.raises(ConfigurationError):
        audit.unregister(User)


def test_should_reject_non_model() -> None:
    with pytest.raises(ConfigurationError):
        audit.register(object)  # type: ignore[arg-type]
