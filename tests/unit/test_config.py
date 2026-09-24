import pytest

from audivra.conf import DEFAULTS, get_config
from audivra.exceptions import ConfigurationError


def test_should_merge_audivra_defaults(settings) -> None:
    settings.AUDIVRA = {}
    config = get_config()
    assert config["BACKEND"] == DEFAULTS["BACKEND"]
    assert "password" in config["DEFAULT_EXCLUDE_FIELDS"]


def test_should_override_backend(settings) -> None:
    settings.AUDIVRA = {"BACKEND": "sync"}
    assert get_config()["BACKEND"] == "sync"


def test_should_reject_unknown_setting(settings) -> None:
    settings.AUDIVRA = {"UNKNOWN": True}
    with pytest.raises(ConfigurationError):
        get_config()


def test_should_reject_invalid_backend(settings) -> None:
    settings.AUDIVRA = {"BACKEND": "redis"}
    with pytest.raises(ConfigurationError):
        get_config()
