# Proposta de Configurações do Repositório no GitHub

> [English](github-settings.md) | **Português (Brasil)**

Esta é uma configuração proposta; ela não foi aplicada. As observações remotas abaixo foram coletadas em 2026-11-03 e estão resumidas em [prontidão do projeto](project-readiness.pt-BR.md).

## Evidências remotas atuais

- `main` é a branch padrão. Nenhuma regra de proteção de branch ou ruleset de repositório está configurada.
- A conta autenticada é o único colaborador observado e tem acesso de admin. Não exija uma aprovação de revisão: o único mantenedor não pode aprovar o próprio pull request.
- A última execução de CI na `main` falhou antes de produzir checks de jobs. Os checks visíveis nesse commit são do Dependabot, portanto o GitHub ainda não forneceu contextos de status de CI bem-sucedidos para seleção.
- O workflow de CI declara estes nomes de jobs: `Validate PR Conventions`, `Lint & Code Style`, `Static Type Analysis`, `Unit & Release Tests`, `Package Build & Version Gate`, `Integration (PG 16)` e `Integration (PG 17)`. Quando existir uma execução de CI bem-sucedida, selecione os contextos exatamente como exibidos na página Checks dela; exija os dois jobs de integração estáveis. Não exija o `Integration (PG 18)`, que é experimental.
- A visibilidade do pacote no GHCR, o acesso de Actions ao pacote e os manifests publicados não puderam ser verificados com as permissões de registry disponíveis. Nenhum artefato de release foi observado; isso não estabelece que não existam.

## Configurações de repositório propostas

### Pull requests e merges

- Permita somente squash merge e defina a mensagem de squash padrão como o título e o corpo do pull request. Desabilite merge commits e rebase merge para que o commit de merge siga a convenção de título validada.
- Exclua as branches de origem após o merge.
- Mantenha o auto-merge habilitado; o GitHub deve fazer o merge somente depois que os checks obrigatórios aplicáveis passarem.
- Mantenha o `.github/CODEOWNERS` como registro de propriedade e de roteamento de revisores. Não exija aprovação enquanto houver um único mantenedor. Reavalie a exigência de aprovação somente depois que outro mantenedor independente tiver acesso de escrita.
- Exija a resolução de conversas e branches atualizadas para o merge. Bloqueie force pushes e a exclusão da `main`.
- Exija os contextos de job de CI listados acima somente depois de confirmar seus nomes de check exatos a partir de uma execução bem-sucedida. As integrações com PostgreSQL 16 e 17 são obrigatórias; o PostgreSQL 18 continua experimental. **Não aplique este conjunto de checks ainda:** o `Static Type Analysis` atualmente falha com 292 erros do Pyright, e o handoff de release depende desse job. Resolva os erros de tipo antes de habilitar este ruleset, para que ele não bloqueie merges e entregas permanentemente.

### Bot de release e compatibilidade com rulesets

O workflow de release usa o `GITHUB_TOKEN` fornecido pelo repositório com `contents: write` para criar o commit/tag do semantic release. A configuração de Actions que permite que workflows criem e aprovem pull requests pode permanecer desabilitada; este workflow faz push direto do commit de release e não abre um PR.

Uma regra na `main` que exija que toda atualização venha por um PR pode bloquear esse push. Os rulesets do GitHub suportam entradas de bypass para GitHub Apps elegíveis, mas o repositório não verificou se o seu app interno do GitHub Actions pode ser selecionado e pode ignorar essa regra específica. Antes de aplicar a regra de PR, verifique essa opção nas configurações do repositório ou execute uma verificação controlada da automação de release. Não use um padrão de mensagem de commit como bypass: `[skip ci]` afeta apenas o disparo de workflows e não concede permissão no ruleset. Não crie uma nova credencial como parte desta proposta.

Se o app interno não puder receber um bypass com escopo restrito, mantenha a exigência de PR em modo Evaluate até que o fluxo de release seja alterado para publicar a partir do merge de um PR, sem push direto. Não habilite um bypass amplo para papéis humanos como substituto do acesso do bot.

### Tags de release e GHCR

- Adicione um ruleset de tags para `v*` que impeça atualizações e exclusões após a criação. A automação de release precisa de permissão para criar tags; confirme que o ruleset escolhido não impede o workflow de semantic release de criá-las.
- Verifique se `ghcr.io/diaszano/pgscope` existe, confirme a visibilidade pretendida e conceda ao repositório o acesso de Actions necessário para as escritas de pacote com o `GITHUB_TOKEN`. Registre as configurações de pacote resultantes; elas continuam não verificadas hoje.
- Mantenha os padrões de Actions em todo o repositório como somente leitura. Os workflows declaram `contents: write` ou `packages: write` restritos por job, apenas onde o trabalho de release exige. Nenhuma permissão `id-token: write` é usada.

## Rollback

Faça o deploy de um digest previamente verificado, substituindo o placeholder explícito abaixo por um digest registrado a partir de um release real e confiável:

```bash
docker pull ghcr.io/diaszano/pgscope@sha256:<verified-release-digest>
```

Não reescreva tags de versão publicadas. Para uma correção, faça o merge de uma mudança `fix:` convencional e deixe o workflow de release publicar uma nova versão patch. Para uma entrega de imagem interrompida, use o [workflow retry-publish](ci-cd.pt-BR.md#4-procedimento-de-recuperação-de-release-parcial) documentado, que verifica as duas arquiteturas e preserva as tags de versão imutáveis.
