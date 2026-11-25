# Guia de Segurança e Deploy em Produção

> [English](security-deployment.md) | **Português (Brasil)**

Este documento descreve a arquitetura de segurança e os requisitos de deploy do servidor **pgscope**.

## 1. Roles de Banco de Dados com Privilégio Mínimo

Nunca conecte o servidor pgscope usando a conta de superusuário `postgres` ou uma conta com privilégios `CREATEDB` / `CREATEROLE`.

### Permissões de Role Recomendadas:
```sql
-- Create dedicated unprivileged MCP role
CREATE ROLE mcp_agent WITH LOGIN PASSWORD '${DB_PASSWORD}';

-- Grant connection only to specific application databases
GRANT CONNECT ON DATABASE app_production TO mcp_agent;

-- Grant read-only table access where required
GRANT USAGE ON SCHEMA public TO mcp_agent;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_agent;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO mcp_agent;

-- Grant stats inspection for performance diagnostics
GRANT pg_read_all_stats TO mcp_agent;
```

## 2. Isolamento Multi-Database e Controle de Acesso

Quando `DATABASE_AUTO_DISCOVER=true`, o servidor lista e alterna dinamicamente os pools de conexão entre bancos de dados PostgreSQL no mesmo host:

- `DATABASE_ALLOWED_DATABASES`: Lista, separada por vírgulas, de nomes de bancos aos quais o servidor MCP tem permissão de se conectar.
- `DATABASE_EXCLUDED_DATABASES`: Lista, separada por vírgulas, de nomes de bancos proibidos.
- `DATABASE_MAX_POOLS`: Máximo de pools de conexão simultâneos (padrão: 4).
- `DATABASE_POOL_MAX_SIZE`: Conexões por pool de banco (padrão: 2).
- `DATABASE_POOL_IDLE_SECONDS`: Limite de ociosidade para recuperação de pools de conexão (padrão: 600).

## 3. Guardrails de Execução de Consultas

Para evitar negação de serviço acidental, full-table scans descontrolados ou erros de falta de memória causados por consultas SQL geradas por LLMs, habilite os query guardrails:

- `DATABASE_QUERY_GUARDRAILS_ENABLED`: Defina como `true` para impor os limites de execução (padrão: `false` durante o rollout, por compatibilidade com versões anteriores).
- `DATABASE_QUERY_DEFAULT_MAX_ROWS`: Limite padrão de linhas por consulta (padrão: `200`).
- `DATABASE_QUERY_HARD_MAX_ROWS`: Teto máximo de linhas permitido, que os clientes não podem sobrescrever (padrão: `5000`).
- `DATABASE_QUERY_DEFAULT_TIMEOUT_SECONDS`: Timeout de execução em segundos (padrão: `15`).
- `DATABASE_QUERY_HARD_TIMEOUT_SECONDS`: Teto absoluto de timeout de consulta (padrão: `60`).
- `DATABASE_QUERY_MAX_RESULT_BYTES`: Tamanho máximo, em bytes, da codificação JSON do resultado (padrão: `2097152` / 2MB).
- `DATABASE_QUERY_MAX_CONCURRENCY`: Limite de consultas em execução por pool (padrão: `4`).

## 4. Paginação Baseada em Cursor

Para grandes conjuntos de dados, os resultados são entregues em páginas limitadas usando a ferramenta `fetch_query_page`:

- `DATABASE_PAGINATION_ENABLED`: Defina como `true` para habilitar a paginação (padrão: `true`).
- `DATABASE_PAGINATION_DEFAULT_PAGE_SIZE`: Tamanho de página padrão (padrão: `100`).
- `DATABASE_PAGINATION_MAX_PAGE_SIZE`: Tamanho máximo de página (padrão: `1000`).
- `DATABASE_PAGINATION_CURSOR_TTL_SECONDS`: Tempo de vida do cursor antes da expiração (padrão: `300`).
- `DATABASE_PAGINATION_MAX_ACTIVE_CURSORS`: Capacidade de cursores ativos limitada em memória (padrão: `100`).

## 5. Ingress de Rede e Segurança de Transporte

Ao executar com transporte HTTP / SSE (`--transport=sse` ou `--transport=streamable-http`):
- Execute atrás de um reverse proxy que faça a terminação de TLS (por exemplo, Nginx, Envoy, Cloudflare).
- Imponha autenticação em todos os endpoints HTTP remotos. Ingress anônimo é estritamente proibido em produção.
- Mantenha `DATABASE_METRICS_ENABLED=true` vinculado ao loopback ou a redes administrativas protegidas.

## 6. Segurança da Cadeia de Suprimentos e Integridade de Artefatos no GHCR

Todas as imagens de contêiner e artefatos de release publicados no GitHub Container Registry (GHCR) seguem padrões rigorosos de segurança da cadeia de suprimentos:

- **Provenance no GHCR e Atestações SLSA**: Os builds de contêiner geram atestações criptográficas de provenance SLSA vinculadas aos commits de release do GitHub.
- **Geração de SBOM**: Cada release de imagem anexa um Software Bill of Materials (SBOM) no formato SPDX padrão, detalhando as árvores exatas de dependências e as licenças.
- **Promoção por Digest Imutável**: A promoção para produção depende exclusivamente de digests de imagem imutáveis `sha256:[a-f0-9]{64}` de builds de staging, eliminando condições de corrida em tags flutuantes.
- **Pinning de Actions e Privilégio Mínimo**: Os pipelines de CI/CD usam permissões de token explicitamente somente leitura (`contents: read`) e fixam todas as GitHub Actions de terceiros em SHAs de commit de 40 caracteres.
- **Varredura Contínua de Vulnerabilidades**: Varreduras de vulnerabilidades de contêiner em modo fail-closed rodam nas imagens multiarquitetura antes da promoção, bloqueando deploys diante de achados HIGH ou CRITICAL.
