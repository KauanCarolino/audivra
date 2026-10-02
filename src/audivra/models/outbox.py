"""Events waiting to be copied into AuditLog."""

from django.db import models


class OutboxStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    PROCESSED = "processed", "Processed"
    FAILED = "failed", "Failed"


class AuditOutbox(models.Model):
    """Transactional event. The worker turns one row into one AuditLog."""

    event_id = models.UUIDField(unique=True)
    event_type = models.CharField(max_length=16)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=16, choices=OutboxStatus.choices, default=OutboxStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True, default="")

    class Meta:
        db_table = "audivra_audit_outbox"
        ordering = ["id"]
        indexes = [
            models.Index(fields=["status", "created_at"], name="audivra_outbox_status_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} {self.event_id}"
