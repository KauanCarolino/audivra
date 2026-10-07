"""Immutable audit event stored by audivra."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.db import models

from audivra.exceptions import ImmutabilityError


class AuditAction(models.TextChoices):
    CREATE = "create", "Create"
    UPDATE = "update", "Update"
    DELETE = "delete", "Delete"
    RESTORE = "restore", "Restore"
    APPROVE = "approve", "Approve"
    REJECT = "reject", "Reject"
    CUSTOM = "custom", "Custom"


class AuditLogQuerySet(models.QuerySet):
    def for_object(self, instance: models.Model) -> AuditLogQuerySet:
        if instance.pk is None:
            raise ValueError("Cannot query audit history for an unsaved instance.")
        content_type = ContentType.objects.get_for_model(instance.__class__)
        return self.filter(content_type=content_type, object_id=str(instance.pk))

    def by_user(self, user: models.Model | str | int) -> AuditLogQuerySet:
        if isinstance(user, models.Model):
            if user.pk is None:
                raise ValueError("Cannot filter audit history by an unsaved user.")
            user_id = str(user.pk)
        else:
            user_id = str(user)
        return self.filter(user_id=user_id)

    def created(self) -> AuditLogQuerySet:
        return self.filter(action=AuditAction.CREATE)

    def updated(self) -> AuditLogQuerySet:
        return self.filter(action=AuditAction.UPDATE)

    def deleted(self) -> AuditLogQuerySet:
        return self.filter(action=AuditAction.DELETE)

    def between(self, start: datetime, end: datetime) -> AuditLogQuerySet:
        return self.filter(created_at__gte=start, created_at__lte=end)

    def update(self, **kwargs: Any) -> int:
        raise ImmutabilityError("AuditLog is immutable.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ImmutabilityError("AuditLog is immutable.")

    def bulk_update(self, objs: Any, fields: Any, batch_size: int | None = None) -> int:
        raise ImmutabilityError("AuditLog is immutable.")


class AuditLog(models.Model):
    """Historical audit event. Inserts are allowed; updates and deletes are not."""

    action = models.CharField(max_length=16, choices=AuditAction.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    user_type = models.CharField(max_length=255, null=True, blank=True)
    content_type = models.ForeignKey(
        "contenttypes.ContentType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    object_id = models.CharField(max_length=255)
    meta_info = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    request_id = models.CharField(max_length=255, null=True, blank=True)
    event_id = models.UUIDField(null=True, blank=True, unique=True)

    objects = AuditLogQuerySet.as_manager()

    class Meta:
        db_table = "audivra_audit_log"
        ordering = ["-created_at"]
        default_permissions = ("view",)
        indexes = [
            models.Index(
                fields=["content_type", "object_id", "created_at"],
                name="audivra_obj_history_idx",
            ),
            models.Index(fields=["user_id"], name="audivra_user_idx"),
            models.Index(fields=["created_at"], name="audivra_created_idx"),
            models.Index(fields=["action"], name="audivra_action_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.action} {self.object_id}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            raise ImmutabilityError("AuditLog is immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ImmutabilityError("AuditLog is immutable.")
