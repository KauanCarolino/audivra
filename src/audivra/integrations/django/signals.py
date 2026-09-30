"""Connect registered models to CREATE, UPDATE and DELETE tracking."""

from collections.abc import Iterable
from typing import Any

from django.db.models import Model
from django.db.models.signals import post_save, pre_delete, pre_save

from audivra.integrations.django.registry import limit_audited_names, registry
from audivra.services.collector import read_stored, read_values, record_create, record_delete, record_update

_OLD: dict[int, dict[str, Any]] = {}
_CONNECTED: set[type[Model]] = set()


def connect(model: type[Model]) -> None:
    if model in _CONNECTED:
        return
    pre_save.connect(_pre_save, sender=model, dispatch_uid=_uid(model, "pre_save"))
    post_save.connect(_post_save, sender=model, dispatch_uid=_uid(model, "post_save"))
    pre_delete.connect(_pre_delete, sender=model, dispatch_uid=_uid(model, "pre_delete"))
    _CONNECTED.add(model)


def disconnect(model: type[Model]) -> None:
    if model not in _CONNECTED:
        return
    pre_save.disconnect(sender=model, dispatch_uid=_uid(model, "pre_save"))
    post_save.disconnect(sender=model, dispatch_uid=_uid(model, "post_save"))
    pre_delete.disconnect(sender=model, dispatch_uid=_uid(model, "pre_delete"))
    _CONNECTED.discard(model)


def _pre_save(
    sender: type[Model],
    instance: Model,
    raw: bool = False,
    update_fields: Iterable[str] | None = None,
    **kwargs: Any,
) -> None:
    if raw or instance._state.adding:
        return
    config = registry.get(sender)
    if config is None:
        return
    names = limit_audited_names(sender, update_fields, config.audited_field_names())
    _OLD[id(instance)] = read_stored(instance, names)


def _post_save(
    sender: type[Model],
    instance: Model,
    created: bool = False,
    raw: bool = False,
    update_fields: Iterable[str] | None = None,
    **kwargs: Any,
) -> None:
    if raw:
        return
    config = registry.get(sender)
    if config is None:
        _OLD.pop(id(instance), None)
        return
    try:
        if created:
            record_create(instance, config)
            return
        old = _OLD.get(id(instance))
        if old is None:
            return
        names = limit_audited_names(sender, update_fields, config.audited_field_names())
        record_update(instance, config, old, read_values(instance, names))
    finally:
        _OLD.pop(id(instance), None)


def _pre_delete(sender: type[Model], instance: Model, **kwargs: Any) -> None:
    config = registry.get(sender)
    if config is None:
        return
    record_delete(instance, config)


def _uid(model: type[Model], signal_name: str) -> str:
    return f"audivra.{signal_name}.{model._meta.label}"
