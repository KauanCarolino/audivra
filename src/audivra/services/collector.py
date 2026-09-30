"""Build audit events from a model instance."""

from typing import Any, cast

from django.db.models import Field, Model

from audivra.backends.sync import write_audit_log
from audivra.integrations.django.registry import ModelConfig
from audivra.models import AuditAction
from audivra.services.diff import diff_values
from audivra.services.serialize import to_jsonable


def read_values(instance: Model, names: frozenset[str]) -> dict[str, Any]:
    """Read concrete field values without loading related objects."""
    values: dict[str, Any] = {}
    for name in names:
        field = instance._meta.get_field(name)
        if isinstance(field, Field):
            values[name] = field.value_from_object(instance)
    return values


def read_stored(instance: Model, names: frozenset[str]) -> dict[str, Any]:
    """Read the current database row for an update diff."""
    if not names or instance.pk is None:
        return {name: None for name in names}
    manager = instance._meta.default_manager
    if manager is None:
        return {name: None for name in names}
    row = manager.filter(pk=instance.pk).values(*sorted(names)).first()
    if row is None:
        return {name: None for name in names}
    return {name: row.get(name) for name in names}


def record_create(instance: Model, config: ModelConfig) -> None:
    write_audit_log(
        action=cast(str, AuditAction.CREATE),
        instance=instance,
        meta_info={
            "object": _object_ref(instance),
            "snapshot": _json_map(read_values(instance, config.audited_field_names())),
        },
    )


def record_update(instance: Model, config: ModelConfig, old: dict[str, Any], new: dict[str, Any]) -> None:
    raw_changes = diff_values(old, new)
    if not raw_changes:
        return
    meta: dict[str, Any] = {
        "object": _object_ref(instance),
        "changes": {
            name: {"old": to_jsonable(item["old"]), "new": to_jsonable(item["new"])}
            for name, item in raw_changes.items()
        },
    }
    if config.snapshot:
        meta["snapshot"] = _json_map(read_values(instance, config.audited_field_names()))
    write_audit_log(action=cast(str, AuditAction.UPDATE), instance=instance, meta_info=meta)


def record_delete(instance: Model, config: ModelConfig) -> None:
    write_audit_log(
        action=cast(str, AuditAction.DELETE),
        instance=instance,
        meta_info={
            "object": _object_ref(instance),
            "snapshot": _json_map(read_values(instance, config.audited_field_names())),
        },
    )


def _object_ref(instance: Model) -> dict[str, str]:
    return {
        "model": instance._meta.label,
        "id": "" if instance.pk is None else str(instance.pk),
    }


def _json_map(values: dict[str, Any]) -> dict[str, Any]:
    return {name: to_jsonable(value) for name, value in values.items()}
