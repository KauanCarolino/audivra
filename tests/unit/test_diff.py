from datetime import date, datetime, time, timezone
from decimal import Decimal
from uuid import UUID

from audivra.services.diff import diff_values
from audivra.services.serialize import to_jsonable


def test_should_keep_only_changed_fields() -> None:
    changes = diff_values(
        {"name": "João", "age": 20, "active": True},
        {"name": "Maria", "age": 20, "active": True},
    )
    assert changes == {"name": {"old": "João", "new": "Maria"}}


def test_should_compare_none_and_nested_json() -> None:
    assert diff_values({"name": None}, {"name": None}) == {}
    assert diff_values({"tags": ["a"]}, {"tags": ["a", "b"]}) == {"tags": {"old": ["a"], "new": ["a", "b"]}}
    assert diff_values({"payload": {"a": 1}}, {"payload": {"a": 1}}) == {}


def test_should_compare_numbers_bools_dates_uuid_and_decimal() -> None:
    day = date(2026, 9, 30)
    moment = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
    clock = time(12, 0)
    uid = UUID("12345678-1234-5678-1234-567812345678")
    old = {
        "age": 1,
        "active": True,
        "when": moment,
        "day": day,
        "clock": clock,
        "uid": uid,
        "amount": Decimal("1.50"),
    }
    assert diff_values(old, dict(old)) == {}
    changed = dict(old)
    changed["amount"] = Decimal("2.00")
    changed["active"] = False
    assert set(diff_values(old, changed)) == {"amount", "active"}


def test_should_serialize_json_safe_values() -> None:
    moment = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
    uid = UUID("12345678-1234-5678-1234-567812345678")
    assert to_jsonable(None) is None
    assert to_jsonable(True) is True
    assert to_jsonable("ada") == "ada"
    assert to_jsonable(3) == 3
    assert to_jsonable(1.5) == 1.5
    assert to_jsonable(Decimal("10.50")) == "10.50"
    assert to_jsonable(moment) == "2026-09-30T12:00:00+00:00"
    assert to_jsonable(date(2026, 9, 30)) == "2026-09-30"
    assert to_jsonable(time(8, 30)) == "08:30:00"
    assert to_jsonable(uid) == "12345678-1234-5678-1234-567812345678"
    assert to_jsonable({"n": Decimal("1")}) == {"n": "1"}
    assert to_jsonable([uid]) == ["12345678-1234-5678-1234-567812345678"]
    assert to_jsonable(b"token") == "token"
