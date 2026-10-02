"""Drain AuditOutbox into AuditLog. One event id produces one log row."""

from datetime import timedelta
from typing import Any
from uuid import uuid4

from django.db import transaction
from django.utils import timezone

from audivra.conf import get_config
from audivra.models import AuditLog, AuditOutbox, OutboxStatus


class OutboxWorker:
    """Process, retry and clean outbox events."""

    def __init__(self, *, limit: int = 100, max_attempts: int = 5) -> None:
        self.limit = limit
        self.max_attempts = max_attempts

    def run(self) -> int:
        return process_outbox(limit=self.limit, max_attempts=self.max_attempts)

    def reprocess(self) -> int:
        return reprocess_failed()

    def cleanup(self) -> int:
        return cleanup_processed()


def enqueue(event_type: str, payload: dict[str, Any]) -> AuditOutbox:
    """Insert an event in the caller's transaction."""
    return AuditOutbox.objects.create(
        event_id=uuid4(),
        event_type=event_type,
        payload=payload,
        status=OutboxStatus.PENDING,
    )


def process_outbox(*, limit: int = 100, max_attempts: int = 5) -> int:
    """Turn pending events into AuditLog rows. A second pass does not duplicate logs."""
    event_ids = list(
        AuditOutbox.objects.filter(status__in=[OutboxStatus.PENDING, OutboxStatus.FAILED], attempts__lt=max_attempts)
        .order_by("id")
        .values_list("pk", flat=True)[:limit]
    )
    delivered = 0
    for event_pk in event_ids:
        if _deliver(event_pk, max_attempts):
            delivered += 1
    return delivered


def reprocess_failed() -> int:
    """Put failed and stuck events back in the queue."""
    return AuditOutbox.objects.filter(status__in=[OutboxStatus.FAILED, OutboxStatus.PROCESSING]).update(
        status=OutboxStatus.PENDING,
        attempts=0,
        last_error="",
    )


def cleanup_processed() -> int:
    """Delete processed events. RETENTION_DAYS keeps rows newer than that window."""
    queryset = AuditOutbox.objects.filter(status=OutboxStatus.PROCESSED)
    retention_days = get_config()["RETENTION_DAYS"]
    if isinstance(retention_days, int):
        cutoff = timezone.now() - timedelta(days=retention_days)
        queryset = queryset.filter(processed_at__lt=cutoff)
    deleted, _ = queryset.delete()
    return deleted


def _deliver(event_pk: int, max_attempts: int) -> bool:
    try:
        with transaction.atomic():
            event = AuditOutbox.objects.select_for_update().get(pk=event_pk)
            if event.status == OutboxStatus.PROCESSED:
                return False
            if event.attempts >= max_attempts:
                return False
            event.status = OutboxStatus.PROCESSING
            event.save(update_fields=["status"])
            _create_log(event)
            event.status = OutboxStatus.PROCESSED
            event.processed_at = timezone.now()
            event.last_error = ""
            event.save(update_fields=["status", "processed_at", "last_error"])
        return True
    except Exception as exc:
        _mark_failure(event_pk, max_attempts, exc)
        return False


def _create_log(event: AuditOutbox) -> None:
    payload = event.payload
    AuditLog.objects.get_or_create(
        event_id=event.event_id,
        defaults={
            "action": payload["action"],
            "content_type_id": payload["content_type_id"],
            "object_id": payload["object_id"],
            "meta_info": payload["meta_info"],
            "user_id": payload.get("user_id"),
            "user_type": payload.get("user_type"),
            "ip_address": payload.get("ip_address"),
            "user_agent": payload.get("user_agent") or "",
            "request_id": payload.get("request_id"),
        },
    )


def _mark_failure(event_pk: int, max_attempts: int, exc: Exception) -> None:
    event = AuditOutbox.objects.filter(pk=event_pk).first()
    if event is None:
        return
    attempts = event.attempts + 1
    status = OutboxStatus.FAILED if attempts >= max_attempts else OutboxStatus.PENDING
    AuditOutbox.objects.filter(pk=event_pk).update(
        attempts=attempts,
        status=status,
        last_error=str(exc)[:2000],
    )
