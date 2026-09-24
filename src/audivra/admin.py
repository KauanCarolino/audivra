from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from audivra.exceptions import ImmutabilityError
from audivra.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Read-only audit history."""

    list_display = ("id", "action", "user_id", "object_label", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("object_id", "user_id", "request_id")
    ordering = ("-created_at",)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: AuditLog | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: AuditLog | None = None) -> bool:
        return False

    def get_readonly_fields(self, request: HttpRequest, obj: AuditLog | None = None) -> list[str]:
        return [field.name for field in self.model._meta.fields]

    def save_model(self, request: HttpRequest, obj: AuditLog, form: Any, change: bool) -> None:
        raise ImmutabilityError("AuditLog is immutable.")

    def delete_model(self, request: HttpRequest, obj: AuditLog) -> None:
        raise ImmutabilityError("AuditLog is immutable.")

    @admin.display(description="Object")
    def object_label(self, obj: AuditLog) -> str:
        content_type = obj.content_type
        if content_type is None:
            return obj.object_id
        return f"{content_type.app_label}.{content_type.model} #{obj.object_id}"
