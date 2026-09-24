import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import RequestFactory

from audivra.admin import AuditLogAdmin
from audivra.exceptions import ImmutabilityError
from audivra.models import AuditLog


@pytest.mark.django_db
def test_should_keep_admin_readonly() -> None:
    admin = AuditLogAdmin(AuditLog, AdminSite())
    request = RequestFactory().get("/admin/audivra/auditlog/")
    request.user = User.objects.create_superuser("ada", "ada@example.com", "secret-pass")

    assert admin.has_add_permission(request) is False
    assert admin.has_change_permission(request) is False
    assert admin.has_delete_permission(request) is False
    assert admin.has_view_permission(request) is True
    assert "action" in admin.get_readonly_fields(request)


@pytest.mark.django_db
def test_should_block_admin_writes() -> None:
    admin = AuditLogAdmin(AuditLog, AdminSite())
    request = RequestFactory().post("/admin/audivra/auditlog/")
    request.user = User.objects.create_superuser("ada2", "ada2@example.com", "secret-pass")
    with pytest.raises(ImmutabilityError):
        admin.save_model(request, AuditLog(), None, False)
    with pytest.raises(ImmutabilityError):
        admin.delete_model(request, AuditLog())
