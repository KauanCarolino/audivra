"""Per-model audit configuration."""

from collections.abc import Sequence
from dataclasses import dataclass

from django.db.models import Model

from audivra.conf import BUILTIN_SENSITIVE_FIELDS, get_config
from audivra.exceptions import ConfigurationError


@dataclass(frozen=True)
class ModelConfig:
    """Fields audited for one model. `include` is None when every concrete field is eligible."""

    model: type[Model]
    include: frozenset[str] | None
    exclude: frozenset[str]
    mask: frozenset[str]

    def audited_field_names(self) -> frozenset[str]:
        selected = _concrete_names(self.model) if self.include is None else self.include
        return frozenset(selected - self.exclude)


class Registry:
    """Models enrolled with `audit.register`."""

    def __init__(self) -> None:
        self._configs: dict[type[Model], ModelConfig] = {}

    def register(
        self,
        model: type[Model],
        *,
        exclude: Sequence[str] | None = None,
        include: Sequence[str] | None = None,
        mask: Sequence[str] | None = None,
    ) -> ModelConfig:
        if not isinstance(model, type) or not issubclass(model, Model):
            raise ConfigurationError("audit.register() expects a Django model class.")
        if model._meta.abstract:
            raise ConfigurationError(f"{model.__name__} is abstract and cannot be registered.")

        aliases = _field_aliases(model)
        explicit_exclude = _canonical_names(exclude, aliases, "exclude")
        explicit_include = None if include is None else _canonical_names(include, aliases, "include")
        explicit_mask = _canonical_names(mask, aliases, "mask")
        excluded = explicit_exclude | (_sensitive_names() & set(aliases.values()))
        overlap = explicit_mask & excluded
        if overlap:
            names = ", ".join(sorted(overlap))
            raise ConfigurationError(f"Masked fields are excluded and will not be stored: {names}.")

        config = ModelConfig(
            model=model,
            include=explicit_include,
            exclude=excluded,
            mask=explicit_mask,
        )
        self._configs[model] = config
        return config

    def unregister(self, model: type[Model]) -> None:
        if model not in self._configs:
            raise ConfigurationError(f"{getattr(model, '__name__', model)} is not registered.")
        del self._configs[model]

    def get(self, model: type[Model]) -> ModelConfig | None:
        return self._configs.get(model)

    def clear(self) -> None:
        self._configs.clear()


def _sensitive_names() -> frozenset[str]:
    configured = get_config()["DEFAULT_EXCLUDE_FIELDS"]
    if isinstance(configured, str) or not isinstance(configured, Sequence):
        raise ConfigurationError("AUDIVRA DEFAULT_EXCLUDE_FIELDS must be a sequence of field names.")
    extra: set[str] = set()
    for name in configured:
        if not isinstance(name, str) or not name.strip():
            raise ConfigurationError("AUDIVRA DEFAULT_EXCLUDE_FIELDS must be a sequence of field names.")
        extra.add(name)
    return BUILTIN_SENSITIVE_FIELDS | frozenset(extra)


def _field_aliases(model: type[Model]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for field in model._meta.concrete_fields:
        aliases[field.name] = field.name
        aliases[field.attname] = field.name
    pk = model._meta.pk
    if pk is not None:
        aliases["pk"] = pk.name
    return aliases


def _concrete_names(model: type[Model]) -> frozenset[str]:
    return frozenset(field.name for field in model._meta.concrete_fields)


def _canonical_names(
    values: Sequence[str] | None,
    aliases: dict[str, str],
    label: str,
) -> frozenset[str]:
    if values is None:
        return frozenset()
    if isinstance(values, (str, bytes)):
        raise ConfigurationError(f"{label} must be a sequence of field names.")
    names: set[str] = set()
    unknown: set[str] = set()
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ConfigurationError(f"{label} entries must be non-empty strings.")
        canonical = aliases.get(value)
        if canonical is None:
            unknown.add(value)
        else:
            names.add(canonical)
    if unknown:
        listed = ", ".join(sorted(unknown))
        raise ConfigurationError(f"Unknown {label} fields: {listed}.")
    return frozenset(names)


registry = Registry()
