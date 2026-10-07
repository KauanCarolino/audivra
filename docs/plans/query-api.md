# Plano — Fase 10: Query API

## Summary

Fases 0–8 estão implementadas (fundação, AuditLog, registry, tracking CRUD, serialização, segurança, request context, outbox). A Fase 9 (Celery) é a próxima no número, mas o MVP e o `AGENTS.md` pedem para **não** adicionar Celery/Redis antes do core estável.

O critério de aceite “AuditLog puder ser consultado” e o exemplo final `audit.history(user)` ainda falham: `audit.history` e `audit.record` levantam `NotImplementedError`. Este plano implementa a **Query API** (`AuditLogQuerySet` + `audit.history`). `audit.record` fica para a Fase 11.

**Alternativa rejeitada:** implementar Celery agora. O extra `audivra[celery]` já existe no `pyproject.toml`, mas o backend ainda recusa a opção de propósito. Query API fecha o MVP de consulta sem expandir o escopo assíncrono.

## Estado atual (explore)

| Peça | Onde | Situação |
|------|------|----------|
| `audit.register` / `unregister` | `src/audivra/audit.py:14-34` | Pronto |
| `audit.history` / `audit.record` | `src/audivra/audit.py:36-40` | `NotImplementedError` |
| `AuditLogQuerySet` | `src/audivra/models/audit_log.py:22-30` | Só bloqueia update/delete |
| Índices de consulta | `src/audivra/models/audit_log.py:60-67` | Já existem (`obj_history`, `user`, `created_at`, `action`) |
| `user_id` | string, nullable | `request_context.py:60` grava `str(user.pk)` |
| README | `README.md:23-24` | Desatualizado (“nesta versão NotImplementedError”) |

Padrão a copiar: `tests/django/test_audit_log.py` (criação de logs) e `tests/django/test_tracking.py` (fluxo real com `Note`).

## Steps

### 1. QuerySet: `for_object`, `by_user`, `created`, `updated`, `deleted`, `between`

- **Arquivos:** `src/audivra/models/audit_log.py`
- **Mudança:** métodos no `AuditLogQuerySet` existente. Manter `update`/`delete`/`bulk_update` imutáveis.
  - `for_object(instance)` → `content_type` + `object_id=str(pk)`
  - `by_user(user)` → `user_id=str(user.pk)` se for Model; senão `str(user)`
  - `created()` / `updated()` / `deleted()` → `action` correspondente
  - `between(start, end)` → `created_at__gte=start`, `created_at__lte=end`
- **Verificação:** `pytest tests/django/test_query_api.py` (arquivo do passo 3; neste passo o teste ainda não existe — escrever os testes no passo 3 em paralelo se o implementador fizer 1+3 juntos, senão TDD no 3 primeiro)

Preferência: **passo 3 antes do 1** (teste que falha, depois implementação). Na prática, um turno pode fazer 3→1→2.

### 2. `audit.history(instance)`

- **Arquivos:** `src/audivra/audit.py`
- **Mudança:** `history` retorna `AuditLog.objects.for_object(instance)`. Não materializar em `list` — o caller encadeia filtros (`history(obj).updated()`).
- **Assinatura:** `def history(self, instance: Model) -> AuditLogQuerySet` (quebra o stub `list[Any]`; permitido antes de `1.0.0`).
- **Verificação:** testes do passo 3 cobrindo `audit.history`.

`audit.record` continua `NotImplementedError` até a Fase 11.

### 3. Testes Django

- **Arquivos:** `tests/django/test_query_api.py` (novo)
- **Casos:**
  - `for_object` devolve só eventos daquela instância
  - `by_user` filtra por `user_id` (User autenticado e `user_id` string)
  - `created` / `updated` / `deleted` isolam a ação
  - `between` respeita o intervalo (timezone-aware)
  - `audit.history(note)` coincide com `for_object`
  - encadeamento: `history(note).updated().by_user(user)`
  - imutabilidade do queryset filtrado ainda levanta `ImmutabilityError`
  - instância sem `pk` levanta erro claro (não retorna lixo com `object_id=""`)
- **Verificação:** `pytest tests/django/test_query_api.py tests/django/test_audit_log.py`

### 4. README + docs de consulta

- **Arquivos:** `README.md`, `docs/django.md` (criar — o plano pede `docs/django.md` e ainda não existe)
- **Mudança:** exemplo de `audit.history` e QuerySet; remover a frase de que `history` levanta `NotImplementedError`. Manter limitações (SQL bruto, bulk, M2M).
- **Verificação:** leitura humana; sem teste.

## Non-goals

- Celery / extra wiring (Fase 9)
- `audit.record()` e eventos manuais (Fase 11)
- Management commands (`audivra_cleanup`, stats)
- Retenção de `AuditLog` (hoje `RETENTION_DAYS` só limpa outbox processado)
- Benchmarks / performance (Fase 12)
- M2M, bulk, hash chain
- Mudar retorno de `history` para lista
- Migration (índices já cobrem as consultas)

## Risks & rollback

| Risco | Mitigação | Rollback |
|-------|-----------|----------|
| Após `delete()`, Django zera `instance.pk` — `history(obj)` não acha o log | Exigir `pk`; documentar consulta por `Note(pk=id)` ou `for_object` com instância ainda viva | Reverter `audit.py` + QuerySet |
| `by_user(None)` vs jobs sem usuário | `by_user` não aceita `None`; histórico anônimo continua `filter(user_id__isnull=True)` direto no ORM (não expor helper agora) | — |
| Métodos `created()` vs campo `created_at` | Nomes vêm do project-plan; não há colisão de API | — |

## Acceptance criteria

- [ ] `AuditLog.objects.for_object(instance)` retorna só eventos daquele model+pk, ordenados por `-created_at` (Meta já define `ordering`)
- [ ] `by_user(user)` e `by_user("1")` filtram o mesmo `user_id`
- [ ] `created()` / `updated()` / `deleted()` filtram `AuditAction`
- [ ] `between(start, end)` inclui extremos
- [ ] `audit.history(instance)` é o atalho público para `for_object`
- [ ] Encadear filtros funciona
- [ ] `history` de instância sem pk falha de forma explícita
- [ ] `update`/`delete` no queryset filtrado ainda são bloqueados
- [ ] `ruff check src tests`, `mypy src/audivra`, `pytest` passam
- [ ] README não afirma mais que `history` está stubado

## Open questions

1. **`history` após DELETE:** confirmar que exigir `pk` (e o padrão `Model(pk=saved_id)`) basta, sem um `for_pk(model, object_id)` extra no MVP.
2. **`by_user` com User anônimo:** não implementar `by_anonymous()` agora — ok?
3. **Docs `docs/django.md`:** criar neste ciclo ou só atualizar o README?

## Próxima fase (fora deste plano)

Fase 11 — `audit.record(action, instance, user=..., metadata=...)`. Celery só depois do core estável (Fase 9 adiada).
