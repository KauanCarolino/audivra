# Arquitetura

```text
Model.save/delete → Collector → Event Builder → Outbox → COMMIT → Worker → AuditLog
```

O core fica em `src/audivra`. A primeira integração é Django (`integrations/django`). FastAPI e Flask ficam fora do MVP.

UPDATE registra só campos alterados. `AuditLog` é imutável. Campos sensíveis saem por padrão (`exclude` e `mask`).
