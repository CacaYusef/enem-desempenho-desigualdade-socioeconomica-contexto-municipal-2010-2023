# Decision: Fundação reprodutível e preservação dos dados brutos

## Status

Accepted — 2026-09-09

## Context

O repositório continha somente um README com o nome do projeto e um pacote
extraído de microdados do ENEM 2023 na raiz. O pacote possui 83 arquivos e cerca
de 1,92 GB. Python 3.13.5 está instalado no ambiente; R não foi localizado. A
pergunta de pesquisa e o plano estatístico ainda não foram definidos.

## Decision

1. Usar Python 3.13, projeto instalável via `pyproject.toml` e código reutilizável
   em `src/enem_analysis/`.
2. Manter notebooks apenas para exploração e narrativa.
3. Mover o pacote recebido, sem modificar seu conteúdo, para
   `data/raw/microdados_enem_2023/` e excluí-lo do Git.
4. Gerar futuros derivados em `data/processed/` exclusivamente por código.
5. Não selecionar teste, modelo, desfecho ou variável socioeconômica até que a
   pergunta e o estimando estejam formalizados em `docs/methodology.md`.

## Alternatives

- Manter os microdados na raiz: rejeitado por misturar fontes imutáveis com código
  e documentação.
- Versionar o pacote no Git: rejeitado pelo volume e pelo risco de distribuição
  acidental de registros desagregados.
- Usar somente notebooks: rejeitado por dificultar testes e reutilização.
- Adotar R nesta etapa: defensável e há scripts R no pacote oficial, mas o runtime
  não está instalado no ambiente atual. A decisão pode ser revista por nova ADR.

## Rationale

A estrutura escolhida separa evidência original, transformações e resultados,
permite testes automatizados e reflete as ferramentas efetivamente disponíveis,
sem antecipar escolhas metodológicas não justificadas.

## Consequences

- O ambiente Python precisa ser criado e as dependências instaladas antes da
  análise.
- Códigos de leitura devem declarar `sep=";"` e `encoding="cp1252"` para o CSV
  principal de 2023.
- Outros anos e dados municipais precisam ser adquiridos, inventariados e
  harmonizados antes de afirmar cobertura de 2010–2023.
- Uma mudança de stack ou política de dados exige nova decisão; este registro não
  deve ser apagado.
