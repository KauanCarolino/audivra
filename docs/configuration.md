# Configuração

Namespace único `AUDIVRA`:

```python
AUDIVRA = {
    "BACKEND": "outbox",  # sync | outbox | celery
    "RETENTION_DAYS": None,
    "TRACK_REQUEST_CONTEXT": True,
    "DEFAULT_EXCLUDE_FIELDS": [
        "access_token",
        "api_key",
        "password",
        "password_hash",
        "private_key",
        "refresh_token",
        "secret",
        "token",
    ],
}
```

`celery` exige o extra `audivra[celery]`. O padrão de `BACKEND` é `outbox`.
