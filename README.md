# audivra

Biblioteca de audit trail para Django. Rastreia CREATE, UPDATE e DELETE em models registrados.

## Instalação

```bash
pip install -e ".[dev]"
```

Django suportado: **5.2** (LTS), **6.0** e **6.1**. Python **3.10+**. Django 6.x exige Python 3.12+.

Adicione `audivra` em `INSTALLED_APPS` e rode `python manage.py migrate`. Guia: [docs/installation.md](docs/installation.md), [docs/django.md](docs/django.md).

## Uso

```python
from audivra import audit

audit.register(User, exclude=["password"])

user.name = "Maria"
user.save()

audit.history(user)
audit.history(user).updated().by_user(actor)
```

`audit.history(instance)` devolve um QuerySet. Também dá para filtrar por `AuditLog.objects.for_object`, `by_user`, `created`, `updated`, `deleted` e `between`.

`audit.record` (eventos manuais) ainda não está implementado.

## Limitações

SQL bruto, bulk update/delete, ManyToMany e alterações fora do ORM não são detectados. Depois de um `delete()`, o Django zera o `pk` — consulte com a instância ainda viva ou com `Model(pk=id)`.

## Desenvolvimento

```bash
ruff check src tests
mypy src
pytest
```
