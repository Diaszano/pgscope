# Contribuindo com o pgscope

> [English](CONTRIBUTING.md) | **Português (Brasil)**

Obrigado pelo seu interesse em contribuir com o `pgscope`! Damos as boas-vindas a contribuições que mantenham altos padrões de engenharia, garantias de segurança e automação reproduzível.

---

## 1. Princípios de Desenvolvimento

- **Desenvolvimento Orientado a Testes (TDD)**: Todo comportamento não trivial ou correção de bug começa com um teste automatizado que falha (RED), seguido da implementação mínima para fazê-lo passar (GREEN) e de uma refatoração disciplinada.
- **Simplicidade e Segurança (Ponytail / YAGNI)**: Prefira código direto e legível e recursos da biblioteca padrão a abstrações desnecessárias ou dependências pesadas.
- **Segurança e Integridade**: Nunca coloque segredos, senhas ou credenciais de produção diretamente no código. Mantenha rigorosas as defesas contra SQL injection e a validação de consultas.

---

## 2. Convenções de Nomenclatura de Branches

Todas as branches de trabalho devem seguir a convenção de nomenclatura estruturada por categoria:

`<category>/<short-description>`

Categorias permitidas:
- `feature/`: Novas funcionalidades ou capacidades (ex.: `feature/query-pagination`)
- `bugfix/`: Correções de bugs não críticos (ex.: `bugfix/pool-connection-leak`)
- `hotfix/`: Correções críticas para defeitos em produção, aplicadas imediatamente
- `docs/`: Adições e melhorias na documentação
- `test/`: Adição ou melhoria de suítes de testes
- `ci/`: Mudanças em workflows de CI/CD, runners ou scripts de automação
- `build/`: Empacotamento, gerenciamento de dependências ou configuração de build
- `perf/`: Otimizações de desempenho
- `refactor/`: Refatoração de código sem alterar o comportamento externo
- `chore/`: Tarefas rotineiras de manutenção
- `revert/`: Reversão de uma mudança anterior

Branches automatizadas de dependências criadas por ferramentas de bot devem usar `dependabot/...`.

---

## 3. Convenções de Mensagens de Commit

As mensagens de commit devem seguir rigorosamente a especificação [Conventional Commits](https://www.conventionalcommits.org/):

`<type>(<optional-scope>): <description>`

Tipos permitidos:
- `feat`: Introduz uma nova funcionalidade para o usuário ou para a API
- `fix`: Corrige um bug
- `docs`: Mudanças apenas na documentação
- `test`: Adição ou modificação de testes
- `ci`: Configuração de CI e scripts de automação
- `build`: Atualizações de dependências, ferramentas de build, empacotamento
- `perf`: Mudança de código que melhora o desempenho
- `refactor`: Mudança de código que não corrige um bug nem adiciona uma funcionalidade
- `chore`: Tarefas de manutenção, arquivos meta
- `revert`: Reverte um commit anterior

Breaking changes devem indicar o impacto de quebra usando `!` imediatamente antes dos dois-pontos (ex.: `feat(api)!: remove deprecated flags`) e documentar a breaking change no rodapé.

Os títulos de pull requests devem seguir o mesmo formato do Conventional Commits, pois o squash merge usa o título como mensagem do commit resultante. O CI valida os títulos quando um PR é aberto, recebe novos commits, é reaberto ou é editado. A autorização de branches do Dependabot é baseada no autor do PR, portanto uma pessoa editando ou reexecutando um PR de bot não altera o autor dele.

---

## 4. Política de Pull Requests e Merge

1. **Template de Pull Request**: Preencha todas as seções do template de pull request.
2. **Verificação Automatizada**: Reproduza localmente as verificações exigidas pelo CI de lock, lint, tipos, testes unitários/de release e pacote:
   ```bash
   uv lock --check
   uv run ruff check .
   uv run ruff format --check .
   uv run pyright
   uv run pytest -q tests/unit tests/release
   uv run python scripts/ci/check_version.py
   uv build
   ```
   As receitas `just lock-check`, `just lint`, `just typecheck`, `just test-unit` e `just build` oferecem os atalhos equivalentes. O CI executa os testes de integração com PostgreSQL separadamente, com sua matriz PG16/17; consulte [CI/CD](docs/ci-cd.md) para o comando que usa Docker.
3. **Estratégia de Squash Merge**: Todos os pull requests são integrados à `main` usando **Squash and Merge**. Isso garante que cada funcionalidade ou correção represente um commit limpo e atômico, com histórico semântico na linha principal.
4. **Propriedade de Código e Revisão**: Caminhos críticos (`.github/workflows/`, `scripts/ci/`, `pyproject.toml`) exigem aprovação dos mantenedores designados em [`.github/CODEOWNERS`](.github/CODEOWNERS).

---

## 5. Atualizações Automatizadas de Dependências (Dependabot)

- O Dependabot é configurado por meio de [`.github/dependabot.yml`](.github/dependabot.yml) para gerar pull requests semanais de atualização para:
  - Dependências Python / uv (`package-ecosystem: uv`)
  - Workflows reutilizáveis e actions do GitHub Actions (`package-ecosystem: github-actions`)
  - Imagens base do Docker (`package-ecosystem: docker`)
- As branches automatizadas de dependências seguem `dependabot/<ecosystem>/<package>-<version>`.
- Todos os pull requests do Dependabot exigem a verificação completa da suíte de testes do CI e a revisão de um mantenedor antes do merge.
