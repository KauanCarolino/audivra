"""Per-request actor and HTTP metadata for audit events."""

from collections.abc import Callable
from contextvars import ContextVar
from dataclasses import dataclass
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.validators import validate_ipv46_address
from django.http import HttpRequest, HttpResponse

from audivra.conf import get_config

_current: ContextVar["RequestContext | None"] = ContextVar("audivra_request_context", default=None)


@dataclass(frozen=True)
class RequestContext:
    """Data captured for one HTTP request. Jobs leave this unset."""

    user_id: str | None
    user_type: str | None
    ip_address: str | None
    user_agent: str
    request_id: str
    method: str
    path: str


def get_request_context() -> RequestContext | None:
    return _current.get()


class RequestContextMiddleware:
    """Store the current request until the response is finished.

    Install after ``AuthenticationMiddleware``:

    ``audivra.middleware.RequestContextMiddleware``
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not get_config()["TRACK_REQUEST_CONTEXT"]:
            return self.get_response(request)
        token = _current.set(_from_request(request))
        try:
            return self.get_response(request)
        finally:
            _current.reset(token)


def _from_request(request: HttpRequest) -> RequestContext:
    user = getattr(request, "user", None)
    user_id = None
    user_type = None
    if user is not None and getattr(user, "is_authenticated", False):
        user_id = "" if user.pk is None else str(user.pk)
        user_type = user._meta.label
    request_id = request.META.get("HTTP_X_REQUEST_ID") or str(uuid4())
    return RequestContext(
        user_id=user_id or None,
        user_type=user_type,
        ip_address=_client_ip(request.META.get("REMOTE_ADDR", "")),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        request_id=request_id[:255],
        method=request.method or "",
        path=request.path,
    )


def _client_ip(value: str) -> str | None:
    try:
        validate_ipv46_address(value)
    except ValidationError:
        return None
    return value
