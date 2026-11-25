# Política de Segurança

> [English](SECURITY.md) | **Português (Brasil)**

O `pgscope` leva a segurança a sério. Este documento descreve nosso processo de relato de vulnerabilidades, os padrões de segurança da cadeia de suprimentos e as políticas de exceção.

---

## 1. Relatando Vulnerabilidades de Segurança

Se você descobrir uma vulnerabilidade de segurança ou um defeito sensível no `pgscope`, **não abra uma issue pública no GitHub**.

Em vez disso, use o Private Vulnerability Reporting do GitHub, na aba Security do repositório, caso esteja habilitado. Sua disponibilidade atual não foi verificada. Se ele não estiver disponível, entre em contato com o mantenedor pelo perfil do GitHub vinculado ao repositório. Inclua uma forma de reproduzir o problema e uma versão afetada; o mantenedor responderá o mais rápido possível.

---

## 2. Segurança da Cadeia de Suprimentos e Atestações de Artefatos

Os workflows de release estão configurados para as seguintes verificações de cadeia de suprimentos. Nenhum artefato de release publicado nem atestação de registry foi verificado durante a revisão de prontidão de 2026-11-03:

- **Registry de Pacotes**: O workflow tem como alvo o GitHub Container Registry (`ghcr.io/diaszano/pgscope`); a visibilidade do pacote e os manifestos publicados continuam não verificados.
- **Software Bill of Materials (SBOM)**: O Buildx está configurado para gerar um SBOM para cada imagem publicada.
- **Procedência do Build**: O Buildx está configurado para gerar uma procedência que vincula a imagem às suas entradas de build.
- **Dependências Fixadas**: Todas as dependências estão travadas em `uv.lock`. Os workflows fixam todas as GitHub Actions de terceiros em SHAs de commit imutáveis de 40 caracteres.

---

## 3. Política de Isenção de Vulnerabilidades

Em circunstâncias raras, em que uma dependência upstream contém uma vulnerabilidade reportada sem correção disponível, e a vulnerabilidade é verificada como não explorável no contexto do `pgscope`, uma isenção temporária pode ser documentada:

Toda isenção de segurança **deve** documentar explicitamente:
1. **Identificador**: CVE ou GHSA ID específico.
2. **Pacote Afetado**: Nome e versão exata.
3. **Análise de Explorabilidade**: Justificativa técnica detalhada explicando por que o problema não é explorável no `pgscope`.
4. **Revisão do Mantenedor**: Registre a revisão por um mantenedor (veja [`.github/CODEOWNERS`](.github/CODEOWNERS)); atualmente há um único mantenedor observado, portanto isto não é um requisito de aprovação independente.
5. **Data de Expiração**: Inclua uma data de revisão, de preferência dentro de 30 dias. Reavalie a isenção quando uma correção estiver disponível.

---

## 4. Governança do Repositório e Segurança de Acesso

As regras detalhadas de proteção do repositório, a segurança de branches na `main`, as proteções de tags de release e as políticas de governança de proprietários estão documentadas em [`docs/github-settings.md`](docs/github-settings.md).
