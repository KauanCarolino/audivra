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

Para gravar usuário, IP e a requisição, coloque o middleware depois da autenticação:

```python
MIDDLEWARE = [
    ...
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "audivra.middleware.RequestContextMiddleware",
]
```

`TRACK_REQUEST_CONTEXT` desliga essa captura. Fora de uma requisição HTTP, `user_id` fica vazio.

Com `BACKEND` `outbox`, o `AuditLog` nasce no worker:

```python
from audivra.backends.outbox import OutboxWorker

OutboxWorker().run()
```
