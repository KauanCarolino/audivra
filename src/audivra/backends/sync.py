"""Write an AuditLog in the same database transaction as the model change."""

from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model

from audivra.conf import get_config
from audivra.exceptions import ConfigurationError
from audivra.middleware.request_context import get_request_context
from audivra.models import AuditLog


def write_audit_log(*, action: str, instance: Model, meta_info: dict[str, Any]) -> AuditLog | None:
    fields = _entry_fields(action=action, instance=instance, meta_info=meta_info)
    backend = get_config()["BACKEND"]
    if backend == "sync":
        return AuditLog.objects.create(**fields)
    if backend == "outbox":
        from audivra.backends.outbox import enqueue

        enqueue(action, fields)
        return None
    raise ConfigurationError("AUDIVRA BACKEND must be 'sync' or 'outbox'. Celery is not available yet.")


def _entry_fields(*, action: str, instance: Model, meta_info: dict[str, Any]) -> dict[str, Any]:
    context = get_request_context() if get_config()["TRACK_REQUEST_CONTEXT"] else None
    payload = dict(meta_info)
    user_id = None
    user_type = None
    ip_address = None
    user_agent = ""
    request_id = None
    if context is not None:
        user_id = context.user_id
        user_type = context.user_type
        ip_address = context.ip_address
        user_agent = context.user_agent
        request_id = context.request_id
        payload["request"] = {
            "method": context.method,
            "path": context.path,
            "ip": context.ip_address,
            "request_id": context.request_id,
        }
    return {
        "action": action,
        "content_type_id": ContentType.objects.get_for_model(instance.__class__).pk,
        "object_id": "" if instance.pk is None else str(instance.pk),
        "meta_info": payload,
        "user_id": user_id,
        "user_type": user_type,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "request_id": request_id,
    }
