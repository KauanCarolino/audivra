from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from audivra import audit
from audivra.exceptions import ImmutabilityError
from audivra.models import AuditAction, AuditLog
from tests.tracking.models import Note


def _log(instance: Note, **overrides: object) -> AuditLog:
    payload: dict[str, object] = {
        "action": AuditAction.CREATE,
        "object_id": str(instance.pk),
        "content_type": ContentType.objects.get_for_model(instance.__class__),
        "meta_info": {},
    }
    payload.update(overrides)
    return AuditLog.objects.create(**payload)


@pytest.mark.django_db
def test_should_return_events_for_one_object() -> None:
    note = Note.objects.create(name="Ada")
    other = Note.objects.create(name="Grace")
    mine = _log(note)
    _log(other)

    result = list(AuditLog.objects.for_object(note))
    assert result == [mine]


@pytest.mark.django_db
def test_should_filter_by_user_instance_or_id() -> None:
    note = Note.objects.create(name="Ada")
    user = User.objects.create(username="ada")
    mine = _log(note, user_id=str(user.pk))
    _log(note, user_id="999")

    assert list(AuditLog.objects.by_user(user)) == [mine]
    assert list(AuditLog.objects.by_user(str(user.pk))) == [mine]
    assert list(AuditLog.objects.by_user(user.pk)) == [mine]


@pytest.mark.django_db
def test_should_filter_by_action() -> None:
    note = Note.objects.create(name="Ada")
    created = _log(note, action=AuditAction.CREATE)
    updated = _log(note, action=AuditAction.UPDATE)
    deleted = _log(note, action=AuditAction.DELETE)

    assert list(AuditLog.objects.created()) == [created]
    assert list(AuditLog.objects.updated()) == [updated]
    assert list(AuditLog.objects.deleted()) == [deleted]


@pytest.mark.django_db
def test_should_include_endpoints_in_between() -> None:
    note = Note.objects.create(name="Ada")
    entry = _log(note)
    moment = entry.created_at
    assert moment is not None

    assert list(AuditLog.objects.between(moment, moment)) == [entry]
    later = moment + timedelta(seconds=1)
    assert list(AuditLog.objects.between(later, later + timedelta(hours=1))) == []


@pytest.mark.django_db
def test_should_expose_history_as_for_object() -> None:
    audit.register(Note)
    note = Note.objects.create(name="João")
    note.name = "Maria"
    note.save()

    history = audit.history(note)
    assert list(history) == list(AuditLog.objects.for_object(note))
    assert history.created().get().action == AuditAction.CREATE
    assert history.updated().get().meta_info["changes"]["name"] == {"old": "João", "new": "Maria"}


@pytest.mark.django_db
def test_should_chain_history_filters() -> None:
    user = User.objects.create(username="ada")
    note = Note.objects.create(name="Ada")
    other = Note.objects.create(name="Grace")
    match = _log(note, action=AuditAction.UPDATE, user_id=str(user.pk))
    _log(note, action=AuditAction.CREATE, user_id=str(user.pk))
    _log(other, action=AuditAction.UPDATE, user_id=str(user.pk))
    _log(note, action=AuditAction.UPDATE, user_id="999")

    assert list(audit.history(note).updated().by_user(user)) == [match]


@pytest.mark.django_db
def test_should_reject_history_for_unsaved_instance() -> None:
    note = Note(name="ghost")
    with pytest.raises(ValueError, match="unsaved instance"):
        AuditLog.objects.for_object(note)
    with pytest.raises(ValueError, match="unsaved instance"):
        audit.history(note)


@pytest.mark.django_db
def test_should_keep_filtered_queryset_immutable() -> None:
    note = Note.objects.create(name="Ada")
    _log(note)
    queryset = AuditLog.objects.for_object(note)
    with pytest.raises(ImmutabilityError):
        queryset.delete()
    with pytest.raises(ImmutabilityError):
        queryset.update(object_id="1")
