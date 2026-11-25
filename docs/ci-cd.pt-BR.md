# Guia de Arquitetura de CI/CD e Release Automatizado

> [English](ci-cd.md) | **Português (Brasil)**

Este documento descreve a arquitetura de integração e entrega contínuas automatizadas do servidor **pgscope**.

## 1. Visão Geral do Pipeline

O projeto usa workflows do GitHub Actions para validação contínua e releases sem nenhuma intervenção manual:

```
[Developer Branch]
       │
       ▼ (Pull Request)
[.github/workflows/ci.yml]
       ├── Lint & Formatting (Ruff)
       ├── Type Checking (Pyright)
       ├── Unit & Release Tests (pytest tests/unit tests/release)
       ├── Package Build (uv build)
       ├── HypoPG Integration Gate (PG16 & PG17)
       └── PR Metadata & Conventional Commits Validation
       │
       ▼ (Merge to main)
[Release Handoff]
       │
       ▼ (Trigger reusable .github/workflows/release.yml)
[Release Please Job]
       ├── Open/update the release PR "chore(release): X.Y.Z" (pyproject.toml, uv.lock, CHANGELOG.md)
       ├── Enable auto-merge (squash); the PR must pass the required CI checks
       └── When the release PR merges: create tag vX.Y.Z & GitHub Release
       │
       ▼ (On New Release)
[Attach Distributions]
       └── Build wheel/sdist and upload them to the GitHub Release
       │
       ▼ (On New Release)
[Standalone Binaries & Homebrew] (.github/workflows/binaries.yml, triggered by the published release)
       ├── Build darwin/linux amd64/arm64 tarballs + sha256 and upload to the GitHub Release
       └── Update Casks/pgscope.rb in Diaszano/homebrew-tap
       │
       ▼ (On New Release)
[Multiarch GHCR Staging & Delivery]
       ├── Docker Buildx & QEMU (linux/amd64, linux/arm64)
       ├── Generate SLSA Provenance & SBOM (SPDX)
       ├── Stage immutable image: ghcr.io/diaszano/pgscope:sha-<commit-sha>
       ├── Fail-closed vulnerability scan (Trivy HIGH/CRITICAL exit 1)
       └── Promote immutable digest to stable SemVer aliases:
           - ghcr.io/diaszano/pgscope:vX.Y.Z
           - ghcr.io/diaszano/pgscope:X.Y.Z
           - ghcr.io/diaszano/pgscope:X.Y
           - ghcr.io/diaszano/pgscope:X
           - ghcr.io/diaszano/pgscope:latest
```

## 2. Gerenciamento de Dependências e Invariantes de Versionamento

- **Verificação do Lock de Dependências**: `uv lock --check` garante que as dependências em `uv.lock` correspondam estritamente ao `pyproject.toml`.
- **Especificação das Tags de Release**: Releases estáveis seguem estritamente o formato `vX.Y.Z`, em que X, Y e Z são inteiros não negativos. Tags de pré-release (`-rc`, `-alpha`, `-beta`) são proibidas na entrega estável.
- **Origem da Versão**: o Release Please deriva a próxima versão dos Conventional Commits (`feat` incrementa a minor, `fix` incrementa a patch) e a registra em `.release-please-manifest.json`, `pyproject.toml` e `uv.lock` no PR de release.
- **Política de Versão Zero**: Enquanto estiver na `0.x.y`, mudanças incompatíveis incrementam a minor (`0.3.0` -> `0.4.0`) em vez de saltar para `1.0.0`.

## 3. Download e Verificação de Imagens

Usuários e orquestradores devem fazer o deploy de imagens usando digests de conteúdo imutáveis:

```bash
# Replace the placeholder with the digest verified for your deployment:
docker pull ghcr.io/diaszano/pgscope@sha256:<verified-digest>

# Run container
docker run -it --rm \
  ghcr.io/diaszano/pgscope@sha256:<verified-digest> \
  postgres://mcp_agent:password@localhost:5432/mydb
```

## 4. Procedimento de Recuperação de Release Parcial

Em cenários raros em que o Release Please cria a tag de um release e o publica no GitHub Releases, mas timeouts de rede ou do registry de contêineres interrompem o build ou a promoção da imagem:

1. **Não crie uma versão duplicada nem refaça a tag manualmente.**
2. Acesse Actions -> workflow **Retry Publish** (`.github/workflows/retry-publish.yml`).
3. Clique em **Run workflow**, informe a tag existente já verificada (por exemplo, `v0.3.0`) e envie.
4. O workflow verifica o formato da tag, a versão correspondente no `pyproject.toml` e o commit da tag obtido no checkout, constrói a imagem de staging a partir desse commit exato, escaneia as duas arquiteturas com o Trivy e repara os aliases seguros sem incrementar números de versão.
5. A recuperação nunca altera uma tag de versão para um digest diferente. Ela avança aliases flutuantes somente quando a versão de imagem registrada neles não é mais nova que o release solicitado; metadados de versão ausentes ou impossíveis de interpretar interrompem a recuperação. A promoção normal de release e a recuperação compartilham o mesmo grupo de concorrência para evitar corridas entre aliases.
6. Se apenas os binários standalone ou o cask do Homebrew falharam, execute manualmente o workflow **Build and Release Standalone Binaries** (`.github/workflows/binaries.yml`) com a mesma tag.

Para um rollback, faça o redeploy de uma referência `repository@sha256:<verified-digest>` previamente verificada. Isso altera apenas a imagem em execução; não publica um release nem move aliases do registry.

## 5. Verificação de Entrega de Ponta a Ponta e Handoff

A revisão de prontidão do repositório de 2026-11-03 não encontrou nenhuma execução de CI bem-sucedida na `main` a partir da qual confirmar os contextos de job exibidos pelo GitHub. Os nomes propostos e as evidências remotas estão registrados em [Configurações do GitHub](github-settings.pt-BR.md). A publicação no GHCR e o acesso ao pacote também continuam não verificados.

Antes de fazer merge de qualquer mudança na `main` ou de criar tags de versões de produção, todo o conjunto de gates de verificação automatizada deve passar:

- **Higiene e Convenções do Repositório**:
  - `uv run pytest -q tests/release/test_repository_conventions.py`
  - `uv run pytest -q tests/release/test_dependabot_config.py`
  - `uv run pytest -q tests/release/test_pr_metadata.py`
- **Qualidade de Código e Análise Estática**:
  - `uv lock --check`
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `uv run pyright` (atualmente reporta diagnósticos existentes; veja [prontidão do projeto](project-readiness.pt-BR.md))
- **Camadas de Teste**:
  - `uv run pytest -q tests/unit`
  - `uv run pytest -q tests/release`
  - `uv run pytest -q tests/integration` (contêineres PostgreSQL 16 e 17 com HypoPG)
- **Verificação do Build de Artefatos**:
  - `uv build` (gerando wheel e sdist válidos)
  - `docker buildx build --platform linux/amd64,linux/arm64 .`
- **Invariantes de Segurança e Atestação**:
  - SHAs de commit fixados (pinned) nas GitHub Actions em `.github/workflows/*.yml`
  - Scanner de vulnerabilidades de contêiner Trivy em modo fail-closed
  - Promoção de digest SHA256 imutável sem condições de corrida em tags flutuantes

## 6. Secrets de Release e Configurações do Repositório

| Secret | Usado por | Acesso necessário |
|--------|-----------|-------------------|
| `RELEASE_PLEASE_TOKEN` | `release.yml` (Release Please e auto-merge) | Personal access token com permissão de escrita em contents e pull requests deste repositório |
| `HOMEBREW_TAP_TOKEN` | `binaries.yml` (atualização do cask do Homebrew) | Personal access token com permissão de escrita em contents de `Diaszano/homebrew-tap` |

Um personal access token é usado nos releases porque pull requests e releases criados com o `GITHUB_TOKEN` não disparam outros workflows. Com o token padrão, o CI nunca rodaria no PR de release (seus checks obrigatórios ficariam pendentes) e o `binaries.yml` não iniciaria quando o release fosse publicado.

O pipeline depende de **Allow auto-merge** estar habilitado e do ruleset da `main` exigir os checks de CI. Nada faz push direto na `main`, então nenhum bypass do ruleset é necessário. O PR de release usa a branch `release-please--branches--main`, que o `scripts/ci/check_pr_metadata.py` aceita.
