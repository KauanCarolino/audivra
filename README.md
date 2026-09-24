# audivra

Biblioteca de audit trail para Django. Versão `0.1.0` entrega a fundação do pacote; o rastreamento CREATE/UPDATE/DELETE chega nas fases seguintes do `project-plan.md`.

## Instalação

```bash
pip install -e ".[dev]"
```

Django suportado: **5.2** (LTS), **6.0** e **6.1**. Python **3.10+**. Django 6.x exige Python 3.12+.

## API prevista

```python
from audivra import audit

audit.register(User, exclude=["password"])
audit.unregister(User)
audit.record("approve", obj, user=user)
audit.history(obj)
```

Nesta versão os métodos levantam `NotImplementedError`.

## Limitações

SQL bruto, bulk update/delete e alterações fora do ORM não são detectados.

## Desenvolvimento

```bash
ruff check src tests
mypy src
pytest
```
