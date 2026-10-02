import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpResponse
from django.test import RequestFactory
from django.utils.module_loading import import_string

from audivra import audit
from audivra.middleware import RequestContextMiddleware
from audivra.models import AuditLog
from tests.tracking.models import Note


def _save_note(_request):
    Note.objects.create(name="Ada")
    return HttpResponse("ok")


@pytest.mark.django_db
def test_should_store_the_request_actor() -> None:
    audit.register(Note)
    user = User.objects.create(username="ada")
    request = RequestFactory().patch(
        "/api/notes/1/",
        REMOTE_ADDR="192.168.0.10",
        HTTP_USER_AGENT="TestAgent",
        HTTP_X_REQUEST_ID="abc-123",
    )
    request.user = user
    RequestContextMiddleware(_save_note)(request)

    entry = AuditLog.objects.get()
    assert entry.user_id == str(user.pk)
    assert entry.user_type == "auth.User"
    assert entry.ip_address == "192.168.0.10"
    assert entry.user_agent == "TestAgent"
    assert entry.request_id == "abc-123"
    assert entry.meta_info["request"] == {
        "method": "PATCH",
        "path": "/api/notes/1/",
        "ip": "192.168.0.10",
        "request_id": "abc-123",
    }


@pytest.mark.django_db
def test_should_leave_the_actor_empty_without_a_request() -> None:
    audit.register(Note)
    request = RequestFactory().get("/api/notes/")
    request.user = AnonymousUser()
    RequestContextMiddleware(_save_note)(request)
    inside = AuditLog.objects.get()
    assert inside.user_id is None
    assert inside.meta_info["request"]["method"] == "GET"

    Note.objects.create(name="job")
    outside = AuditLog.objects.exclude(pk=inside.pk).get()
    assert outside.user_id is None
    assert outside.ip_address is None
    assert "request" not in outside.meta_info


@pytest.mark.django_db
def test_should_skip_context_when_disabled(settings) -> None:
    settings.AUDIVRA = {"BACKEND": "sync", "TRACK_REQUEST_CONTEXT": False}
    audit.register(Note)
    user = User.objects.create(username="ada")
    request = RequestFactory().post("/api/notes/", REMOTE_ADDR="192.168.0.10")
    request.user = user
    RequestContextMiddleware(_save_note)(request)
    entry = AuditLog.objects.get()
    assert entry.user_id is None
    assert "request" not in entry.meta_info


def test_should_import_the_middleware_path() -> None:
    middleware = import_string("audivra.middleware.RequestContextMiddleware")
    assert middleware is RequestContextMiddleware
