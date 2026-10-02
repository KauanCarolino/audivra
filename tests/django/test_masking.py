import json

import pytest

from audivra import audit
from audivra.models import AuditAction, AuditLog
from tests.tracking.models import Note

PASSWORD = "pw-hunter2-unique"
TOKEN = "tok-unique-value"
SECRET = "sec-unique-value"
CPF = "123.456.789-12"
PHONE = "11999998888"


@pytest.mark.django_db
def test_should_not_store_sensitive_values() -> None:
    audit.register(Note, mask=["cpf"])
    note = Note.objects.create(
        name="Ada",
        password=PASSWORD,
        token=TOKEN,
        secret=SECRET,
        cpf=CPF,
        phone=PHONE,
    )
    created = AuditLog.objects.get(action=AuditAction.CREATE, object_id=str(note.pk))
    stored = json.dumps(created.meta_info)
    assert PASSWORD not in stored
    assert TOKEN not in stored
    assert SECRET not in stored
    assert CPF not in stored
    assert created.meta_info["snapshot"]["cpf"] == "***.***.***-12"
    assert created.meta_info["snapshot"]["phone"] == PHONE
    assert "password" not in created.meta_info["snapshot"]
    assert "token" not in created.meta_info["snapshot"]
    assert "secret" not in created.meta_info["snapshot"]

    note.password = "another-secret-password"
    note.save()
    assert AuditLog.objects.filter(action=AuditAction.UPDATE).count() == 0

    note.cpf = "123.456.789-34"
    note.save()
    updated = AuditLog.objects.get(action=AuditAction.UPDATE)
    assert updated.meta_info["changes"]["cpf"] == {
        "old": "***.***.***-12",
        "new": "***.***.***-34",
    }
    assert "123.456.789-34" not in json.dumps(updated.meta_info)


@pytest.mark.django_db
def test_should_use_a_custom_field_serializer() -> None:
    audit.register(Note, serializers={"phone": lambda value: f"***{str(value)[-4:]}"})
    note = Note.objects.create(name="Ada", phone=PHONE)
    created = AuditLog.objects.get(action=AuditAction.CREATE, object_id=str(note.pk))
    assert created.meta_info["snapshot"]["phone"] == "***8888"
    assert PHONE not in json.dumps(created.meta_info)
