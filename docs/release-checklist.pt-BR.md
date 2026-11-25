# Checklist de Release e Procedimento de Rollback do pgscope

> [English](release-checklist.md) | **Português (Brasil)**

Versão Base: (avaliada dinamicamente a partir do `pyproject.toml`)
Registry de Imagens Principal: `ghcr.io/diaszano/pgscope`
Automação de Release: Release Please (googleapis/release-please-action v5.0.0) via GitHub Actions

## Checklist de Verificação Pré-Release

Execute os seguintes gates de verificação antes de criar a tag e publicar qualquer release:

- [ ] **Lock de Dependências**: Execute `uv lock --check` para garantir que o `uv.lock` seja consistente com o `pyproject.toml`.
- [ ] **Lint e Formatação**: Execute `just lint` (`uv run ruff check .` e `uv run ruff format --check .`).
- [ ] **Análise Estática de Tipos**: Execute `just typecheck` (`uv run pyright`).
- [ ] **Testes Unitários e de Release**: Execute `uv run pytest -q tests/unit tests/release` (o job de CI executa as duas suítes).
- [ ] **Suíte de Testes de Integração**: Execute `just test-integration` em PostgreSQL 16 e 17 com contêineres com a extensão HypoPG.
- [ ] **Suíte de Release**: Execute `uv run pytest -q tests/release`, cobrindo regras de SemVer, convenções, varreduras de segurança e gates de workflow.
- [ ] **Benchmarks de Desempenho**: Execute `uv run --group dev pytest -q tests/performance --run-performance`.
- [ ] **Smoke Tests**: Execute `uv run pytest -q tests/release/test_smoke.py` ao alterar o empacotamento de runtime ou a inicialização do contêiner.
- [ ] **Build do Pacote**: Execute `uv build` e inspecione o conteúdo do wheel em `dist/`.
- [ ] **Build do Contêiner**: Verifique o build de contêiner multiarquitetura para `linux/amd64` e `linux/arm64`.

## Gates Automatizados de CI/CD e Entrega

1. **Pull Requests**:
   - Todos os PRs executam checks somente leitura de lint, verificação de tipos, testes, build do pacote e integração com HypoPG.
   - Os metadados do PR são validados conforme o Conventional Commits.
   - Segredos privilegiados e permissões de publicação são bloqueados em eventos de PR.

2. **Branch Main e Release Please**:
   - Pushes na `main` avaliam o histórico de commits usando Conventional Commits.
   - O Release Please abre ou atualiza um PR de release (`chore(release): X.Y.Z`, branch `release-please--branches--main`) que atualiza `pyproject.toml`, `uv.lock` e `CHANGELOG.md` (política de versão zero pré-1.0: mudanças incompatíveis incrementam a minor).
   - O auto-merge (squash) fica habilitado nesse PR e conclui assim que os checks obrigatórios passam. Nada faz push direto na `main`.
   - Ao fazer o merge do PR de release, o Release Please cria a tag `vX.Y.Z` e o GitHub Release, e o workflow então anexa a ele os pacotes wheel e sdist. O novo fluxo ainda não produziu um release, então os artefatos de release remotos não foram verificados para ele.

3. **Entrega Multiarquitetura no GHCR**:
   - Imagens multiarquitetura (`linux/amd64,linux/arm64`) são construídas com o Docker Buildx e preparadas (staged) usando SHAs de commit imutáveis.
   - Varreduras de vulnerabilidades de contêiner rodam com o Trivy (fail-closed em CVEs HIGH/CRITICAL).
   - O Buildx está configurado para gerar provenance e SBOM a cada build de imagem; a publicação no registry não foi verificada.
   - Os digests de staging verificados são promovidos para as tags `vX.Y.Z`, `X.Y`, `X` e `latest` em `ghcr.io/diaszano/pgscope`.

4. **Binários Standalone e Homebrew**:
   - A publicação do release dispara `.github/workflows/binaries.yml`, que constrói os tarballs `darwin`/`linux` `amd64`/`arm64` com arquivos `sha256`, envia-os ao release e atualiza `Casks/pgscope.rb` em `Diaszano/homebrew-tap`.
   - O workflow falha se `HOMEBREW_TAP_TOKEN` estiver ausente, se faltar algum checksum ou se o push no tap falhar.

## Procedimento de Rollback em Produção e Backout de Emergência

Se surgirem regressões, rejeições inesperadas de consultas ou incompatibilidades de clientes em produção:

1. **Desabilitar os Query Guardrails**:
   Defina `DATABASE_QUERY_GUARDRAILS_ENABLED=false` no ambiente do servidor. Isso restaura imediatamente o comportamento legado das instruções, sem quebrar pools de conexão nem descartar avisos de segurança.
2. **Desabilitar a Paginação por Cursor**:
   Defina `DATABASE_PAGINATION_ENABLED=false` se os clientes tiverem problemas ao consumir tokens de continuação.
3. **Isolamento do Armazenamento em Memória**:
   O cache de cursores é estritamente em processo e limitado em memória, sem dependências de armazenamento externo (sem serviços de cache externos nem daemons de broker). Reiniciar o contêiner ou o processo descarta o estado ativo dos cursores de forma limpa, sem corrupção persistente.
4. **Rollback de Binário / Contêiner**:
   Faça o redeploy de uma imagem previamente verificada por digest (`ghcr.io/diaszano/pgscope@sha256:<verified-release-digest>`; apenas placeholder) ou de um wheel de um GitHub Release verificado. Não presuma que uma tag mutável ou um artefato de release exista até que seja verificado.
5. **Recuperação Somente de Publicação**:
   Se a publicação do release falhar no meio do caminho (por exemplo, o GitHub Release existe, mas a promoção do contêiner sofreu timeout), dispare o `.github/workflows/retry-publish.yml` com a tag de release validada para republicar com segurança sem incrementar versões. Se apenas os binários standalone ou o cask do Homebrew falharam, execute `.github/workflows/binaries.yml` manualmente (`workflow_dispatch`) com a mesma tag.
