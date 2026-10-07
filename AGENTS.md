# AGENTS.md

Instruções para agentes de IA trabalhando neste repositório.

## Overview

**audivra** é uma biblioteca Python publicável (`pip install audivra`) de Audit Trail / Audit Log para Django.
Stack: Python >= 3.10, Django, PostgreSQL (JSONB), pytest, ruff, mypy.

Fonte de verdade detalhada: `@project-plan.md`, `@.cursor/cursor-instructions.md`, `@.cursor/rules/audivra-core.mdc`.

## Layout

```text
src/audivra/
├── audit.py              # API pública (register, record, history)
├── models/               # AuditLog, AuditOutbox
├── services/             # collector, diff, serialize, recorder
├── middleware/           # request_context
├── integrations/django/  # registry, signals
├── backends/             # sync, outbox, celery (extra)
└── utils/                # masking, serialization
tests/{unit,integration,django,performance}/
docs/
.cursor/                  # regras, agentes, skills, CI
```

## Commands

```bash
pip install -e ".[dev]"           # setup
pytest                            # todos os testes
pytest tests/unit/test_foo.py     # um arquivo
ruff check src tests              # lint
mypy src/audivra                  # typecheck
python -m build                   # build do pacote
```

## Conventions

- Código em inglês; type hints em APIs públicas.
- API pública estável: `audit.register`, `unregister`, `record`, `history`.
- Commits: Conventional Commits. Sem secrets no repo.
- Diffs focados na tarefa; sem refactors não relacionados.
- Não usar `json.dumps(model.__dict__)` para serialização.
- Copiar padrões existentes: `@src/audivra/audit.py`, `@src/audivra/integrations/django/registry.py`, `@tests/unit/test_registry.py`.
- Fora do MVP (não adicionar antes do core estável): Celery, Redis, M2M, bulk tracking, hash chain.

## Workflow (Explore → Plan → Implement → Verify)

1. **Explore** — read-only: mapear arquivos, padrões, testes, riscos; parar e reportar.
2. **Plan** — passos em diffs pequenos, critérios de aceite, non-goals; aguardar aprovação.
3. **Implement** — um passo por turno; diff mínimo; rodar testes após cada passo.
4. **Verify** — lint + mypy + pytest; checklist de aceite com evidência; decisão de ship.

Para tarefas simples (1–2 arquivos), pule direto para Implement.
Para tarefas amplas (>3 arquivos), Explore e Plan são obrigatórios.

Mencione `@explore-plan` em `.cursor/rules/explore-plan.mdc` para forçar o fluxo completo.
Salvar planos aprovados em `docs/plans/<nome-curto>.md`.

## Gotchas

- Outbox deve estar na mesma transação da alteração principal — rollback = sem auditoria falsa.
- UPDATE registra somente campos alterados; sem evento se não houver mudança auditável.
- DELETE captura snapshot **antes** da remoção.
- Campos com `password`, `token`, `secret`, `api_key` são excluídos por padrão.
- `AuditLog` é imutável — Admin somente leitura.
- SQL bruto, bulk update/delete e alterações fora do ORM não são detectados no MVP.
- CI canônico: `.github/workflows/ci.yml` (espelhado em `.cursor/workflows/ci.yml`).

## Boundaries

- **Git**: agentes não executam add/commit/push/PR (ver `git-no-write.mdc`).
- Não editar `dist/`, `build/`, `*.egg-info/`.
- Perguntar antes de: nova dependência, mudança de API pública, migration de schema.

## Definition of done

- ruff, mypy e pytest passam.
- Comportamento novo tem teste; bugfix inclui regressão.
- Resumo lista arquivos alterados e o que o humano deve verificar manualmente.
