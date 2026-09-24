import pytest
from django.contrib.contenttypes.models import ContentType
from django.db import connection

from audivra.exceptions import ImmutabilityError
from audivra.models import AuditAction, AuditLog


def _log(**overrides: object) -> AuditLog:
    content_type = ContentType.objects.get_for_model(ContentType)
    payload = {
        "action": AuditAction.CREATE,
        "object_id": "123",
        "content_type": content_type,
        "meta_info": {"snapshot": {"name": "Ada"}},
    }
    payload.update(overrides)
    return AuditLog.objects.create(**payload)


@pytest.mark.django_db
def test_should_store_audit_log() -> None:
    entry = _log(user_id=None, user_type="auth.user")
    assert entry.pk is not None
    assert entry.action == AuditAction.CREATE
    assert entry.created_at is not None
    assert entry.meta_info["snapshot"]["name"] == "Ada"
    assert entry.user_id is None


@pytest.mark.django_db
def test_should_reject_update() -> None:
    entry = _log()
    entry.object_id = "999"
    with pytest.raises(ImmutabilityError):
        entry.save()


@pytest.mark.django_db
def test_should_reject_delete() -> None:
    entry = _log()
    with pytest.raises(ImmutabilityError):
        entry.delete()
    with pytest.raises(ImmutabilityError):
        AuditLog.objects.all().delete()
    with pytest.raises(ImmutabilityError):
        AuditLog.objects.all().update(object_id="1")


@pytest.mark.django_db
def test_should_index_object_history() -> None:
    _log()
    table = AuditLog._meta.db_table
    with connection.cursor() as cursor:
        constraints = connection.introspection.get_constraints(cursor, table)
    indexed = {tuple(info["columns"]) for info in constraints.values() if info["index"]}
    assert ("content_type_id", "object_id", "created_at") in indexed
    assert ("user_id",) in indexed
    assert ("created_at",) in indexed
    assert ("action",) in indexed
