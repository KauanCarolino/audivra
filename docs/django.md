# Django

Adicione `audivra` em `INSTALLED_APPS` e aplique as migrations:

```bash
python manage.py migrate
```

Configuração: [configuration.md](configuration.md). Middleware de request context entra depois de `AuthenticationMiddleware`.

## Registrar models

```python
from audivra import audit

audit.register(User, exclude=["password", "last_login"])
audit.register(Customer, mask=["cpf", "phone"], snapshot=True)
audit.unregister(User)
```

`include` restringe os campos; `exclude` tem prioridade. Campos com `password`, `token`, `secret` e similares saem por padrão.

`save()` e `delete()` passam a gerar `AuditLog`. UPDATE só grava campos alterados; sem mudança auditável, não há evento. DELETE captura o snapshot antes da remoção.

## Consultar histórico

```python
from audivra import audit
from audivra.models import AuditLog

audit.history(user)
audit.history(user).updated()
audit.history(user).updated().by_user(request.user)
audit.history(user).between(start, end)

AuditLog.objects.for_object(user)
AuditLog.objects.by_user(request.user)
AuditLog.objects.created()
AuditLog.objects.updated()
AuditLog.objects.deleted()
```

`history` e `for_object` exigem `instance.pk`. Depois de `delete()`, use a instância ainda viva ou um stub `User(pk=saved_id)`.

O Admin de `AuditLog` é somente leitura.

## Limitações

Não entram no rastreamento automático:

- SQL bruto
- `QuerySet.update`, `bulk_update`, `bulk_delete`
- ManyToMany (`add` / `remove` / `clear`)
- alterações feitas direto no banco

`audit.record` (eventos manuais) ainda não está disponível.
