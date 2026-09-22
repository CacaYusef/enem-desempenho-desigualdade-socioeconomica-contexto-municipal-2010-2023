# Desempenho no ENEM, desigualdade socioeconômica e contexto municipal (2010–2023)

Projeto de análise estatística reprodutível sobre o tema indicado no título. O
relatório acadêmico fornecido estabeleceu uma pergunta associativa preliminar.
A entrega vigente analisa a base elegível integral do ENEM 2023, com matemática
como desfecho principal e município da escola como contexto. A decisão 006
registra o desenho; inferência e modelos econométricos ainda não foram executados.

## Estado atual

- **Estado do trabalho: 2º estado — Relatório Descritivo em elaboração.**
- **Única etapa concluída: Proposta.**
- Ainda não concluídos: Relatório Descritivo, Relatório Final e Apresentação.
- Disponíveis localmente: pacotes oficiais ENEM 2010–2022 e pacote 2023 preexistente.
- Contexto municipal: fontes IBGE, INEP e Ipeadata importadas; cobertura varia por
  indicador e ano. Não foram interpolados indicadores censitários.
- Importação, fontes e reprodução: [docs/importacao.md](docs/importacao.md).
- Auditoria técnica: [reports/data-quality.md](reports/data-quality.md).
- Desenho vigente: **1.027.924 elegíveis de 2023**, todos incluídos, sem sorteio;
  probabilidade condicional de processamento e peso iguais a 1.
- [Relatório PDF vigente: análise socioeconômica e territorial](reports/report/relatorio_descritivo_territorial_enem_2023.pdf).
- [Resultados, fontes, limites e reprodução](docs/analise-territorial-2023.md).
- A análise descritiva foi executada; modelos econométricos, testes e inferência
  ainda não foram executados. A revisão acadêmica da etapa está pendente.
- O plano de 20 mil por edição, a calibração PNAD e o relatório multianual
  permanecem preservados como histórico das decisões 004/005, não como desenho
  vigente.
- Pergunta pretendida, unidade principal e pendências: documentadas em
  `docs/methodology.md`; referência substantiva: concluintes do ensino médio.
- O vínculo territorial usa somente o município da escola; local de prova não é
  residência. Estimandos e métodos econométricos continuam pendentes.
- Texto-base da tese: `reports/report/tese.md`.

## Estrutura

```text
data/raw/          dados originais imutáveis (não versionados)
data/processed/    produtos derivados reproduzíveis (não versionados)
analysis/          análises exploratórias, descritivas, inferenciais e modelos
src/enem_analysis/ código reutilizável de dados, estatística e visualização
tests/             testes automatizados
reports/           figuras, tabelas e relatório
docs/              metodologia, dicionário, glossário e decisões
notebooks/         exploração e comunicação; lógica permanente fica em src/
```

## Ambiente de desenvolvimento

O projeto usa Python 3.13. No PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Para reproduzir exatamente o ambiente instalado na inicialização:

```powershell
python -m pip install -r requirements-dev.lock
python -m pip install -e . --no-deps
```

Validações previstas:

```powershell
python -m pytest
python -m ruff check .
```

Não inclua `.env`, credenciais nem microdados no Git. Consulte `AGENTS.md`
antes de modificar análises e `data/README.md` antes de manipular dados.
