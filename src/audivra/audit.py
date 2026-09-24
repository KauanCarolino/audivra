"""Public audit API. Tracking is implemented in later phases."""

from collections.abc import Sequence
from typing import Any


class Audit:
    """Stable entry point: register, unregister, record, history."""

    def register(
        self,
        model: type,
        *,
        exclude: Sequence[str] | None = None,
        include: Sequence[str] | None = None,
        mask: Sequence[str] | None = None,
    ) -> None:
        raise NotImplementedError

    def unregister(self, model: type) -> None:
        raise NotImplementedError

    def record(self, action: str, instance: Any, user: Any = None) -> None:
        raise NotImplementedError

    def history(self, instance: Any) -> list[Any]:
        raise NotImplementedError


audit = Audit()
