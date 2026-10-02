import pytest
from django.db import transaction

from audivra import audit
from audivra.backends.outbox import OutboxWorker
from audivra.models import AuditLog, AuditOutbox, OutboxStatus
from tests.tracking.models import Note


@pytest.mark.django_db
def test_should_enqueue_in_the_same_transaction(settings) -> None:
    settings.AUDIVRA = {"BACKEND": "outbox"}
    audit.register(Note)
    note = Note.objects.create(name="Ada")
    assert AuditLog.objects.count() == 0
    event = AuditOutbox.objects.get()
    assert event.status == OutboxStatus.PENDING
    assert event.payload["object_id"] == str(note.pk)
    assert event.event_type == "create"

    try:
        with transaction.atomic():
            Note.objects.create(name="rolled-back")
            raise RuntimeError("rollback")
    except RuntimeError:
        pass
    assert AuditOutbox.objects.count() == 1


@pytest.mark.django_db
def test_should_deliver_once(settings) -> None:
    settings.AUDIVRA = {"BACKEND": "outbox"}
    audit.register(Note)
    Note.objects.create(name="Ada")
    assert OutboxWorker().run() == 1
    assert AuditLog.objects.count() == 1
    event = AuditOutbox.objects.get()
    assert event.status == OutboxStatus.PROCESSED
    assert event.processed_at is not None
    log = AuditLog.objects.get()
    assert log.event_id == event.event_id
    assert log.meta_info["snapshot"]["name"] == "Ada"

    event.status = OutboxStatus.PENDING
    event.save(update_fields=["status"])
    assert OutboxWorker().run() == 1
    assert AuditLog.objects.count() == 1


@pytest.mark.django_db
def test_should_retry_and_reprocess(settings, monkeypatch: pytest.MonkeyPatch) -> None:
    settings.AUDIVRA = {"BACKEND": "outbox"}
    audit.register(Note)
    Note.objects.create(name="Ada")

    def fail(*args: object, **kwargs: object) -> None:
        raise RuntimeError("db down")

    monkeypatch.setattr(AuditLog.objects, "get_or_create", fail)
    assert OutboxWorker(max_attempts=1).run() == 0
    event = AuditOutbox.objects.get()
    assert event.status == OutboxStatus.FAILED
    assert event.attempts == 1
    assert "db down" in event.last_error

    monkeypatch.undo()
    assert OutboxWorker().reprocess() == 1
    event.refresh_from_db()
    assert event.status == OutboxStatus.PENDING
    assert event.attempts == 0
    assert OutboxWorker().run() == 1
    assert AuditLog.objects.count() == 1


@pytest.mark.django_db
def test_should_cleanup_processed_events(settings) -> None:
    settings.AUDIVRA = {"BACKEND": "outbox", "RETENTION_DAYS": None}
    audit.register(Note)
    Note.objects.create(name="Ada")
    OutboxWorker().run()
    assert OutboxWorker().cleanup() == 1
    assert AuditOutbox.objects.count() == 0
    assert AuditLog.objects.count() == 1
