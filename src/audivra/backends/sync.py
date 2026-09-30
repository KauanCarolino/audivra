"""Write an AuditLog in the same database transaction as the model change."""

from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model

from audivra.conf import get_config
from audivra.exceptions import ConfigurationError
from audivra.models import AuditLog


def write_audit_log(*, action: str, instance: Model, meta_info: dict[str, Any]) -> AuditLog:
    if get_config()["BACKEND"] != "sync":
        raise ConfigurationError("AUDIVRA BACKEND must be 'sync' until the outbox backend is available.")
    return AuditLog.objects.create(
        action=action,
        content_type=ContentType.objects.get_for_model(instance.__class__),
        object_id="" if instance.pk is None else str(instance.pk),
        meta_info=meta_info,
    )
