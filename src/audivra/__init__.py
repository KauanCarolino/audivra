from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from audivra.audit import audit as audit

__all__ = ["audit"]


def __getattr__(name: str) -> Any:
    if name == "audit":
        from audivra.audit import audit as value

        globals()["audit"] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
