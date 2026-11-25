# Baseline de prontidão do projeto

> [English](project-readiness.md) | **Português (Brasil)**

Baseline capturado em 2026-11-03 a partir do commit local `cdb81019c61a2cb1f1590e4b42af79b0ff8b95ee` na branch `docs/project-readiness-implementation`. Esta é uma verificação pontual; a `main` remota do repositório estava em `764c0a4e59639e43c1a502e287d227631d131bdc` quando foi inspecionada.

## Matriz de evidências

| Área | Estado | Evidência | Próxima ação |
|---|---|---|---|
| Lockfile | Verificado | `uv lock --check` — exit 0; 83 pacotes resolvidos. | Manter esta verificação na validação local e no CI. |
| Lint e formatação | Verificado fora do sync do projeto | `uvx --from ruff==0.14.13 ruff check .` — exit 0; `ruff format --check .` — exit 0, 147 arquivos. | Restaurar as verificações com `uv run` após resolver a falha de build de dependência de runtime abaixo. |
| Tipos e testes unitários/de release | Bloqueado | `uv run pyright` e `uv run pytest -q tests/unit tests/release` — exit 1 antes da execução: o código-fonte travado do `pglast` falha ao compilar porque `postgres_deparse.h` está ausente. A mesma falha de instalação impede o início dos comandos `uv run ruff` planejados. | Inspecionar o artefato de código-fonte fixado e a distribuição suportada na Task 3; não tratar verificações bloqueadas como aprovadas. |
| Build do pacote | Verificado | `uv build` — exit 0; gerou sdist e wheel da versão 0.3.0. Isso não instala as dependências de runtime. | A Task 2 deve instalar o wheel construído em um ambiente limpo e verificar o caminho do módulo instalado. |
| Ferramentas locais | Parcial | Padrão do host: Python 3.15.2; `uv` 0.13.7 instalado pelo instalador da Astral após nenhum executável ser encontrado no PATH nem nos caminhos de instalação locais padrão. O `uv` selecionou o CPython 3.12.3 para este projeto. O cliente e o daemon do Docker 29.1.3 respondem. `gh auth status` confirmou uma conta ativa; os valores dos tokens não foram registrados. | Executar os fluxos descartáveis de PostgreSQL e contêiner na Task 2. |
| Configurações de repositório e merge | Verificado remotamente | Metadados do GitHub: público, ativo, branch padrão `main`; squash, merge e rebase estão habilitados; auto-merge está habilitado. Apenas `Diaszano` aparece na lista de colaboradores e tem permissão de admin. | Alinhar a proposta do repositório a um único colaborador ativo na Task 7. |
| Proteção de branch | Verificada como ausente na `main` | O endpoint de rulesets do GitHub retornou `[]`; `gh api .../branches/main/protection` retornou 404 `Branch not protected`. | Propor configurações concretas na Task 7; não aplicá-las durante este trabalho. |
| Checks e execuções recentes | Misto | O commit mais recente da `main` tinha sete checks do Dependabot concluídos (seis `Dependabot`, um `.github/dependabot.yml`), todos bem-sucedidos. As 10 execuções de Actions mais recentes eram pushes de CI de branches do Dependabot e todas foram concluídas com falha; exemplo: [run 41661206742](https://github.com/Diaszano/pgscope/actions/runs/41661206742). | Inspecionar as causas das falhas ao tratar as tarefas de CI/release; não inferir que todas as execuções de CI falham apenas a partir desta amostra. |
| Releases e GHCR | Pendente | A API de releases retornou uma lista vazia. A listagem de pacotes do GHCR falhou com 403 porque a credencial ativa não tem `read:packages`; a existência, a visibilidade e os manifests do pacote continuam desconhecidos. | Verificar o GHCR por um caminho de leitura autorizado nas Tasks 7/8; não presumir uma imagem publicada. |

## Achados priorizados

1. **Bloqueio de instalação (resolvido na Task 2):** o `pyproject.toml` agora usa `pglast==7.22` do PyPI; o arquivo de código-fonte anteriormente fixado falhava ao compilar porque `postgres_deparse.h` estava ausente. As verificações que dependem de dependências agora rodam.
2. **Lacuna de confiança na entrega:** a amostra recente de Actions contém execuções de CI do Dependabot que falharam repetidamente, e nenhum release está listado. A causa dessas execuções e qualquer publicação de imagem precisam ser confirmadas antes de afirmar que a entrega está saudável.
3. **Lacuna de governança:** a `main` não tem proteção de branch nem rulesets. O repositório tem um único colaborador listado, então qualquer exigência de revisão deve considerar um mantenedor solo.
4. **Lacuna de visibilidade remota:** a credencial do GitHub disponível não consegue ler pacotes do GHCR. O estado da imagem permanece desconhecido, não ausente.

## Evidências remotas

- Metadados do repositório, rulesets, proteção de branch, releases, execuções de workflows, checks e permissão de colaborador foram lidos do GitHub em 2026-11-03. A lista de colaboradores foi lida com o `gh` porque o plugin do GitHub não expôs essa coleção.
- A proteção de branch pôde ser lida com o `gh`, embora o plugin do GitHub tenha retornado 403 para esse endpoint. A CLI autenticada reportou `Branch not protected` (404).
- A inspeção do GHCR foi tentada com o `gh`; o GitHub negou por falta do escopo `read:packages`. Nenhuma credencial foi alterada.
- Nenhuma string de conexão de banco de dados, token ou log bruto de comandos está incluída aqui.

## Verificação da Task 2

- O bloqueio de instalação era um arquivo de código-fonte do `pglast` 7.11 sem o `postgres_deparse.h`. Este repositório agora usa `pglast==7.22` do PyPI e não fixa mais a URL direta de código-fonte quebrada. O changelog do upstream documenta a correção do header ausente na 7.17; a linha v7 do `pglast` do projeto tem como alvo o PostgreSQL 17. Veja [mudanças do pglast](https://github.com/lelit/pglast/blob/v8/CHANGES.rst) e [projeto pglast](https://github.com/lelit/pglast).
- `uv run ruff check .` e `uv run ruff format --check .` agora rodam com o ambiente do projeto. `uvx --from . pgscope --help` funciona.
- `uv run pyright` roda, mas termina com exit 1 e 292 diagnósticos em 34 arquivos: 35 em quatro arquivos de código-fonte e 257 em 30 arquivos de teste. A maioria repete poucas categorias (tipagem de união de conteúdo do MCP, mocks de teste, campos opcionais da AST e acesso protegido em testes). Nenhum defeito de runtime foi demonstrado a partir desses diagnósticos, e as suítes comportamentais existentes exercitam os caminhos afetados; uma limpeza ampla de anotações ou supressões está fora do escopo baseado em evidências da Task 3. O Pyright continua sendo uma verificação sabidamente com falha para a Task 8.
- Smoke test do wheel, executado a partir da raiz do repositório:

  ```bash
  uv build
  wheel_test=$(mktemp -d /tmp/pgscope-wheel.XXXXXX)
  uv venv --python 3.12 "$wheel_test/venv"
  uv pip install --python "$wheel_test/venv/bin/python" "$PWD/dist/pgscope-0.3.0-py3-none-any.whl"
  (cd "$wheel_test" && "$wheel_test/venv/bin/pgscope" --help && "$wheel_test/venv/bin/python" -c 'import importlib.metadata, pathlib, pgscope; print(importlib.metadata.version("pgscope")); print(pathlib.Path(pgscope.__file__).resolve())')
  ```

  Resultado: o help termina com exit 0, a versão é `0.3.0` e o caminho do módulo está dentro do `site-packages` do venv temporário.
- O primeiro build local do Docker falhou porque o `.dockerignore` excluía o `README.md` exigido pelos metadados do pacote. A lista de ignorados agora reinclui o `README.md`; `docker build --tag pgscope:readiness --build-arg REVISION=local-readiness .` e `docker run --rm pgscope:readiness --help` terminam ambos com exit 0. Nenhuma imagem foi enviada (push).
- `bash scripts/ci/build_hypopg_image.sh 16` construiu e verificou a imagem descartável do PostgreSQL 16. `uv run pytest -q tests/integration/test_mcp_result_wire.py tests/integration/test_restricted_security.py` passou 15 testes; isso inclui uma sessão real de cliente MCP contra o banco descartável, descoberta de ferramentas, um SELECT permitido, um INSERT bloqueado e uma resposta de erro sem a senha.
- `uv run pytest -q tests/unit/test_documentation_contract.py tests/release/test_smoke.py` passou 8 testes. `uv run pytest -q tests/unit/test_query_service.py tests/unit/sql/test_safe_sql.py tests/unit/security/test_sql_policy.py tests/unit/test_mcp_response.py tests/unit/test_error_contract.py` passou 143 testes.
- O teste de wire inicialmente revelou que o FastMCP rejeitava o erro estruturado do servidor contra o schema de saída de lista inferido. `format_error_response` agora inclui o conteúdo `result` esperado junto com o erro estruturado; a saída de sucesso e as assinaturas das ferramentas permanecem inalteradas. A regressão passou após esta correção.

## Verificação da Task 3

- O teste existente de comandos de desenvolvedor ainda afirmava `pglast==7.11` após a correção de dependência exigida pela Task 2. Agora ele compara a versão travada do pglast com a dependência exata declarada no `pyproject.toml`.
- O `justfile` agora tem `lock-check`, e `test-unit` executa `tests/unit` e `tests/release`, igual ao CI. O CONTRIBUTING lista os comandos de lock, lint, formatação, tipos, unit/release, metadados de versão e build do CI. O `just` não está instalado neste ambiente, então `just --list` não pôde ser executado.
- `uv run pytest -q tests/unit tests/release`: 804 passaram, 1 xfailed, com uma falha de teste de governança obsoleto que exigia uma imagem do GHCR nos dois READMEs. Essa asserção foi atualizada para verificar as instruções de build local do Docker já verificadas e a ausência de uma referência não verificada ao GHCR; seus testes de governança focados passam.
- `uv run pyright --outputjson`: exit 1, 292 diagnósticos (35 de código-fonte, 257 de testes). Os problemas de código-fonte reportados são incompatibilidades de contrato de tipos e análise de valores opcionais; nenhuma correção adicional de runtime foi justificada por um teste de owner. Isso continua sendo uma lacuna de prontidão explícita, e não uma verificação aprovada.

## Verificação da Task 4

- O CI de `pull_request` agora roda em `opened`, `synchronize`, `reopened` e `edited`, de modo que alterar o título de um PR reexecuta a validação. A validação de branches de bot recebe `github.event.pull_request.user.login`; um humano editando ou reexecutando um PR do Dependabot não substitui a identidade do autor.
- O chamador de release concede `contents: write` e `packages: write` somente ao seu job condicionado a um push na `main`. As permissões dos workflows reutilizáveis permanecem somente leitura por padrão; o semantic release recebe contents write, enquanto o build/promoção de imagem recebe packages write. Nenhuma permissão `id-token: write` é solicitada porque esses jobs não usam OIDC.
- O CI e o release usam o uv 0.13.7. Esta versão exata executou com sucesso `uv lock --check` contra o lockfile atual. A Astral documenta a compatibilidade do schema do lockfile por versão e que as revisões permanecem retrocompatíveis; veja [compatibilidade do lockfile do uv](https://docs.astral.sh/uv/concepts/resolution/) e [versionamento do uv](https://docs.astral.sh/uv/reference/policies/versioning/).
- O CONTRIBUTING agora lista `revert/` como uma categoria de branch suportada, documenta a validação de título de squash e a semântica de autor do Dependabot, e mantém os comandos de teste locais verificados.
- `uv run pytest -q tests/release/test_pr_metadata.py tests/release/test_ci_workflow.py tests/release/test_ci_release_gate.py tests/release/test_dependabot_config.py tests/release/test_action_security.py`: 28 passaram. As verificações de lint/formatação do Ruff nos arquivos Python alterados e `uv lock --check` passaram. O comportamento dos workflows foi validado a partir do YAML; nenhum workflow do GitHub foi disparado.

## Verificação da Task 5

- O passo de release anterior executava `version --print || true` e depois comparava a versão inalterada do projeto consigo mesma. O workflow agora verifica a versão proposta sem suprimir erros, trata uma versão inalterada como um não-release bem-sucedido e, caso contrário, executa o comando mutante `version` antes de verificar a versão carimbada no projeto e publicar os assets da tag exata. O Python Semantic Release 10.7.0 documenta que `--print` termina com a versão atual quando nenhum release está planejado, enquanto `version` cria/envia mudanças de versão por padrão e `publish --tag` envia os assets do release. Veja [comandos da CLI](https://python-semantic-release.readthedocs.io/en/latest/api/commands.html).
- A varredura agendada do repositório com o Trivy agora define `exit-code: "1"` para achados HIGH/CRITICAL; nenhum `continue-on-error` suprime falhas da ferramenta.
- `uv run pytest -q tests/release/test_release_workflow.py tests/release/test_release_bootstrap.py tests/release/test_release_build.py tests/release/test_release_metadata.py tests/release/test_security_failures.py`: 23 passaram. Os testes executam o bloco de shell real do workflow com ferramentas falsas para falha de versão, nenhuma mudança de versão e sequenciamento bem-sucedido da saída de version/publish.
- `uvx --from python-semantic-release==10.7.0 semantic-release --noop version --print` terminou com exit 0 sem modificar a worktree; nesta branch de implementação a ferramenta reportou corretamente que a branch está fora dos grupos de release configurados. Nenhum token de escrita foi usado. Um release real na `main` não foi disparado.

## Verificação da Task 6

- `promote_image.sh` e `scan_image.sh` são exercitados como subprocessos reais com executáveis falsos de Docker e Trivy. Refs inválidas, Trivy ausente, qualquer uma das arquiteturas falhando, tags imutáveis alteradas, erros de inspeção do registry e metadados de versão de alias desconhecidos interrompem tudo antes da promoção. Uma promoção bem-sucedida registra o digest exato e as tags passadas ao `docker buildx imagetools create`.
- A recuperação inspeciona os aliases flutuantes e lê `org.opencontainers.image.version` de cada plataforma da imagem. Ela atualiza um alias somente quando sua versão atual não é mais nova que o release solicitado; metadados de versão desconhecidos ou inconsistentes falham em modo fail-closed. Tags de versão podem ser reparadas quando ausentes ou já no mesmo digest, e não podem ser redirecionadas para outro digest. O mesmo grupo de concorrência serializa a promoção de release e a de recuperação.
- A imagem Docker agora carrega o label de versão do release. Tanto o build de release quanto o de retry passam a versão associada ao commit exato obtido no checkout, e o script de promoção é executado a partir desse commit. As entradas do retry são passadas por variáveis de ambiente e validadas antes do uso; o commit obtido no checkout deve ser igual ao commit da tag solicitada.
- O Trivy é instalado nos dois jobs de promoção a partir do commit fixado do `aquasecurity/setup-trivy` `81e514348e19b6112ce2a7e3ecbafe19c1e1f567` e da versão fixa do binário `v0.76.1`. A varredura agendada do repositório usa o commit fixado do `trivy-action` `57a97c7e7821a5776cebc9bb87c984fa69cba8f1` e a mesma versão do scanner. Estes são posteriores ao [aviso oficial de cadeia de suprimentos do Trivy](https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23); o setup-trivy documenta a instalação fixada por SHA e as entradas de versão fixa no seu [README oficial](https://github.com/aquasecurity/setup-trivy/blob/main/README.md).
- O Dockerfile alterado foi construído localmente com `VERSION=0.3.0`; `docker image inspect` retornou o label `0.3.0`. Nenhuma imagem foi enviada (push).
- Suíte exigida da Task 6: 37 passaram; `bash -n` passou nos dois scripts de shell editados; lint/formatação do Ruff e `git diff --check` passaram. O estado do GHCR continua não verificado por falta de `read:packages`, então nenhuma recuperação ou promoção remota foi executada.

## Verificação da Task 7

- Foram relidas as execuções de Actions e os check-runs remotos em 2026-11-03. A última execução de CI na `main` foi a [41660883533](https://github.com/Diaszano/pgscope/actions/runs/41660883533); ela falhou antes de emitir qualquer entrada de job. Os checks visíveis do seu commit eram seis checks do Dependabot e `.github/dependabot.yml`, todos bem-sucedidos. Portanto, nenhum contexto de status de CI bem-sucedido estava disponível para confirmar os nomes de exibição exatos dos check-runs. O `docs/github-settings.md` dá os nomes de jobs declarados no workflow como contextos propostos e exige confirmá-los em uma execução bem-sucedida antes de aplicá-los.
- A documentação de rulesets do GitHub lista GitHub Apps entre os atores de bypass elegíveis. A disponibilidade, neste repositório, do app interno do GitHub Actions não foi verificada, então o ruleset de PR é explicitamente mantido em Evaluate até que esse bypass exato seja verificado ou o fluxo de release mude. Nenhum bypass por mensagem de commit nem nova credencial é proposto.
- Os documentos de governança agora levam em conta o único admin observado, distinguem o roteamento por CODEOWNERS da aprovação independente imposta, e marcam o acesso ao pacote GHCR/publicação como não verificados. Os digests de rollback de release são explicitamente rotulados como placeholders. `SECURITY.md`, o template de PR, o guia de CI/CD, o checklist de release e o índice de planos foram reconciliados com as mudanças das Tasks 2–6.
- Comando exigido da Task 7: `uv run pytest -q tests/release/test_github_settings.py tests/release/test_release_docs.py tests/release/test_repository_governance.py tests/release/test_repository_conventions.py tests/unit/test_documentation_contract.py` — 26 passaram.

## Verificação final da Task 8

A verificação da implementação foi executada a partir do código commitado em `b6ba76eca4251a19f1dae27bafdd675787cd064f` em 2026-11-03. Esta evidência é local, salvo quando indicada como remota.

| Verificação | Comando ou evidência | Resultado |
|---|---|---|
| Lock de dependências | `uv lock --check` | Passou; 83 pacotes resolvidos. |
| Ruff | `uv run ruff check .`; `uv run ruff format --check .` | Passou; todas as verificações passaram, 147 arquivos formatados. |
| Análise estática | `uv run pyright --outputjson` | Falhou com 292 erros, 0 avisos, em 147 arquivos analisados. Esta é a lacuna conhecida registrada na Task 2. |
| Suítes unitárias e de release | `uv run pytest -q tests/unit tests/release` | 833 passaram, 1 xfailed. |
| Build do pacote | `uv build` | Passou; construiu sdist e wheel da 0.3.0. |
| Integração com PostgreSQL 16 | `bash scripts/ci/build_hypopg_image.sh 16`; `MULTIDB_PG_IMAGE=postgres-hypopg:16 uv run pytest -q tests/integration` | Imagem e ativação do HypoPG passaram; 86 passaram, 18 ignorados, 1 xfailed. |
| Integração com PostgreSQL 17 | `bash scripts/ci/build_hypopg_image.sh 17`; `MULTIDB_PG_IMAGE=postgres-hypopg:17 uv run pytest -q -rs tests/integration` | Imagem e ativação do HypoPG passaram; 86 passaram, 18 ignorados, 1 xfailed. Todos os ignorados eram casos de DTA sem recomendações geradas ou cenários explicitamente adiados. |
| Smoke test do wheel | Instalar o wheel construído em um venv Python 3.12 limpo; executar `pgscope --help`; inspecionar o caminho do módulo e os metadados do pacote | Passou; versão 0.3.0, módulo carregado a partir do `site-packages` do venv temporário. |
| Smoke test do contêiner | `docker build --tag pgscope:readiness-final --build-arg REVISION=readiness-final --build-arg VERSION=0.3.0 .`; `docker run --rm pgscope:readiness-final --help`; inspecionar o label de versão OCI | Passou; o help retornou com sucesso e o label é 0.3.0. Nenhuma imagem foi enviada (push). |
| Higiene do diff | `git diff --check` | Passou. |


A revisão final independente confirmou um bloqueio de prontidão: o `.github/workflows/ci.yml` exige o job `typecheck` antes do handoff de release, e o Pyright atualmente termina com 292 erros. Mantenha esse gate de CI intacto; não aplique o conjunto de checks de branch proposto nem trate a entrega como pronta até que os diagnósticos do Pyright sejam resolvidos e o gate passe.

### Estado remoto e trabalho pendente

- **Validado no GitHub:** Metadados do repositório, proteção de branch/rulesets, permissão de colaborador, check runs, releases e execuções recentes de Actions foram inspecionados em 2026-11-03. A `main` não está protegida; o único colaborador observado tem acesso de admin. A última execução de CI falhou antes de criar jobs, então os nomes de contexto de check de CI bem-sucedidos continuam não confirmados. A [última execução de CI da `main`](https://github.com/Diaszano/pgscope/actions/runs/41660883533) está registrada acima. A API de releases do GitHub retornou uma lista vazia.
- **Acesso/verificação remota pendentes:** Existência, visibilidade, permissão de escrita de Actions, manifests, digests e atestações do pacote no GHCR; disponibilidade de relato privado de vulnerabilidades; se o app interno do GitHub Actions pode ser selecionado como ator de bypass de ruleset; e os nomes de exibição exatos dos status checks de uma execução bem-sucedida.
- **Não aplicado:** Nenhuma regra de branch/tag, configuração de merge, configuração do GHCR, release, promoção de imagem ou publicação foi alterada. O guia de configurações é uma proposta para revisão do owner. Não declare o CD de ponta a ponta como validado até que o caminho de release e registry tenha sido bem-sucedido remotamente.
