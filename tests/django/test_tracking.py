from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.db import transaction

from audivra import audit
from audivra.models import AuditAction, AuditLog
from tests.tracking.models import Note


@pytest.mark.django_db
def test_should_record_create_update_and_delete() -> None:
    audit.register(Note)
    author = User.objects.create(username="ada")
    note = Note.objects.create(
        name="João",
        age=20,
        active=True,
        password="secret",
        amount=Decimal("10.50"),
        tags=["a"],
        author=author,
    )

    created = AuditLog.objects.get(action=AuditAction.CREATE)
    assert created.object_id == str(note.pk)
    assert created.meta_info["object"] == {"model": "tracking.Note", "id": str(note.pk)}
    assert created.meta_info["snapshot"]["name"] == "João"
    assert created.meta_info["snapshot"]["amount"] == "10.50"
    assert created.meta_info["snapshot"]["author"] == author.pk
    assert "password" not in created.meta_info["snapshot"]

    note.save()
    assert AuditLog.objects.filter(action=AuditAction.UPDATE).count() == 0

    note.name = "Maria"
    note.age = 21
    note.save(update_fields=["name"])
    updated = AuditLog.objects.get(action=AuditAction.UPDATE)
    assert updated.meta_info["changes"] == {"name": {"old": "João", "new": "Maria"}}
    assert "snapshot" not in updated.meta_info

    note.refresh_from_db()
    note.author = None
    note.save()
    author_change = AuditLog.objects.filter(action=AuditAction.UPDATE).latest("id")
    assert author_change.meta_info["changes"]["author"] == {"old": author.pk, "new": None}

    object_id = str(note.pk)
    note.delete()
    deleted = AuditLog.objects.get(action=AuditAction.DELETE)
    assert deleted.object_id == object_id
    assert deleted.meta_info["snapshot"]["name"] == "Maria"
    assert "password" not in deleted.meta_info["snapshot"]


@pytest.mark.django_db
def test_should_store_optional_update_snapshot() -> None:
    audit.register(Note, snapshot=True)
    note = Note.objects.create(name="João", age=20)
    note.name = "Maria"
    note.save()
    updated = AuditLog.objects.get(action=AuditAction.UPDATE)
    assert updated.meta_info["changes"]["name"]["new"] == "Maria"
    assert updated.meta_info["snapshot"]["name"] == "Maria"
    assert updated.meta_info["snapshot"]["age"] == 20


@pytest.mark.django_db
def test_should_skip_unregistered_models() -> None:
    Note.objects.create(name="João")
    assert AuditLog.objects.count() == 0


@pytest.mark.django_db
def test_should_roll_back_the_audit_log_with_the_change() -> None:
    audit.register(Note)
    note = Note.objects.create(name="João")
    try:
        with transaction.atomic():
            note.name = "Maria"
            note.save()
            raise RuntimeError("rollback")
    except RuntimeError:
        pass
    note.refresh_from_db()
    assert note.name == "João"
    assert AuditLog.objects.filter(action=AuditAction.UPDATE).count() == 0
