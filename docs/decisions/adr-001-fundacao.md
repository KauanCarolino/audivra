# ADR 001 — Fundação do pacote

## Contexto

A Fase 0 do `project-plan.md` pedia nome, licença, versão, matriz Python/Django e arquitetura antes do código.

## Decisão

- Nome do pacote: `audivra`.
- Licença: MIT.
- Versão inicial: `0.1.0` (SemVer; API estável só após `1.0.0`).
- Python >= 3.10. CI: 3.10, 3.11, 3.12.
- Django >= 5.2, < 6.2 (5.2 LTS, 6.0, 6.1). Django 4.2 está fora de suporte.
- Configuração no namespace `AUDIVRA` (`sync` | `outbox` | `celery`).
- Histórico em `AuditLog`, separado dos models de negócio. Implementação nas fases 2+.

## Consequências

O esqueleto em `src/audivra` e o tooling (Ruff, Mypy, Pytest, pre-commit, GitHub Actions) desbloqueiam a Fase 2.
