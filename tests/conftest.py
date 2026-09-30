"""Shared pytest fixtures for audivra."""

import pytest

from audivra.integrations.django.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry():
    registry.clear()
    yield
    registry.clear()
