# Guia de Migração de Query Guardrails e Paginação por Cursor

> [English](migration-query-guardrails.md) | **Português (Brasil)**

Este guia descreve como migrar para orçamentos de consulta limitados e paginação por cursor no **pgscope**, mantendo a compatibilidade com clientes MCP legados.

## 1. Rollout e Compatibilidade com Versões Anteriores

Por padrão, os query guardrails são opt-in para não quebrar instalações legadas:

```bash
# Keep legacy behavior (unbounded row counts and default timeouts)
DATABASE_QUERY_GUARDRAILS_ENABLED=false

# Enforce production guardrails
DATABASE_QUERY_GUARDRAILS_ENABLED=true
```

Quando os guardrails estão habilitados, consultas que excedem o teto de linhas são truncadas automaticamente, com um envelope estruturado de metadados de aviso, em vez de descartar linhas silenciosamente ou esgotar a memória do cliente.

## 2. Contratos de Ferramentas Versionados

### `execute_sql` e `read_query`
Os clientes podem informar controles de orçamento opcionais a cada chamada de ferramenta:
- `max_rows` (inteiro): Limite de linhas solicitado para esta execução (deve ser <= `DATABASE_QUERY_HARD_MAX_ROWS`).
- `timeout_seconds` (inteiro): Timeout de execução em segundos (deve ser <= `DATABASE_QUERY_HARD_TIMEOUT_SECONDS`).

### `fetch_query_page`
Quando as consultas produzem conjuntos de resultados grandes, a resposta inclui um token de continuação opaco, `cursor`:

```json
{
  "rows": [...],
  "page": 1,
  "has_more": true,
  "cursor": "c3ViamVjdF9pZDoxMDA=",
  "truncated": false
}
```

Para buscar as linhas seguintes:
```json
{
  "name": "fetch_query_page",
  "arguments": {
    "cursor": "c3ViamVjdF9pZDoxMDA="
  }
}
```

### Tempo de Vida do Cursor e Semântica de Melhor Esforço
- **TTL**: Os cursores expiram após 300 segundos (`DATABASE_PAGINATION_CURSOR_TTL_SECONDS`). Tokens de cursor expirados ou desconhecidos retornam um erro estruturado `INVALID_CURSOR`.
- **Consumo único**: Cada token de cursor é de uso único; recuperar uma página invalida o token anterior e retorna um novo se ainda restarem linhas.
- **Consistência de Melhor Esforço (Sem Promessas de Snapshot)**: o pgscope não mantém transações de snapshot de longa duração abertas entre requisições HTTP ou stdio, para evitar inchaço de tabelas de transação e contenção de locks. Se linhas forem inseridas, excluídas ou modificadas entre as requisições de página, a paginação opera em regime de melhor esforço, sem garantias de isolamento de snapshot entre as páginas.
