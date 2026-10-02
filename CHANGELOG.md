# Changelog

## 0.1.0

- Pacote inicial: layout `src/audivra`, namespace `AUDIVRA` e API pública em esqueleto.
- `AuditLog` imutável, `AuditAction`, índices e Admin somente leitura.
- `audit.register` / `unregister` com include, exclude e campos sensíveis de fora por padrão.
- CREATE, UPDATE e DELETE no backend `sync`, com diff e snapshot opcional.
- Máscara padrão e `serializers` por campo; senha, token e secret não entram no log.
- Middleware grava usuário, IP, user-agent, método, path e request id.
- Outbox grava o evento na mesma transação; o worker cria um `AuditLog` por `event_id`.
- Tooling: Ruff, Mypy, Pytest, coverage e pre-commit.
