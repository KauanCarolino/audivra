"""Public audit API."""

from collections.abc import Sequence
from typing import Any

from django.db.models import Model

from audivra.integrations.django.registry import registry


class Audit:
    """Stable entry point: register, unregister, record, history."""

    def register(
        self,
        model: type[Model],
        *,
        exclude: Sequence[str] | None = None,
        include: Sequence[str] | None = None,
        mask: Sequence[str] | None = None,
        snapshot: bool = False,
    ) -> None:
        registry.register(
            model,
            exclude=exclude,
            include=include,
            mask=mask,
            snapshot=snapshot,
        )

    def unregister(self, model: type[Model]) -> None:
        registry.unregister(model)

    def record(self, action: str, instance: Any, user: Any = None) -> None:
        raise NotImplementedError

    def history(self, instance: Any) -> list[Any]:
        raise NotImplementedError


audit = Audit()
