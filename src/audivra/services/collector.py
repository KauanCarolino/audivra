"""Build audit events from a model instance."""

from typing import Any, cast

from django.db.models import Field, Model

from audivra.backends.sync import write_audit_log
from audivra.integrations.django.registry import ModelConfig
from audivra.models import AuditAction
from audivra.services.diff import diff_values
from audivra.services.serialize import to_jsonable
from audivra.utils.masking import mask_text


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
            "snapshot": _present(read_values(instance, config.audited_field_names()), config),
        },
    )


def record_update(instance: Model, config: ModelConfig, old: dict[str, Any], new: dict[str, Any]) -> None:
    raw_changes = diff_values(old, new)
    if not raw_changes:
        return
    meta: dict[str, Any] = {
        "object": _object_ref(instance),
        "changes": {
            name: {"old": _present_value(name, item["old"], config), "new": _present_value(name, item["new"], config)}
            for name, item in raw_changes.items()
        },
    }
    if config.snapshot:
        meta["snapshot"] = _present(read_values(instance, config.audited_field_names()), config)
    write_audit_log(action=cast(str, AuditAction.UPDATE), instance=instance, meta_info=meta)


def record_delete(instance: Model, config: ModelConfig) -> None:
    write_audit_log(
        action=cast(str, AuditAction.DELETE),
        instance=instance,
        meta_info={
            "object": _object_ref(instance),
            "snapshot": _present(read_values(instance, config.audited_field_names()), config),
        },
    )


def _object_ref(instance: Model) -> dict[str, str]:
    return {
        "model": instance._meta.label,
        "id": "" if instance.pk is None else str(instance.pk),
    }


def _present(values: dict[str, Any], config: ModelConfig) -> dict[str, Any]:
    return {name: _present_value(name, value, config) for name, value in values.items()}


def _present_value(name: str, value: Any, config: ModelConfig) -> Any:
    serializer = config.serializers.get(name)
    if serializer is not None:
        return to_jsonable(serializer(value))
    rendered = to_jsonable(value)
    if name in config.mask:
        return mask_text(rendered)
    return rendered
