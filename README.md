# Desempenho no ENEM, desigualdade socioeconômica e contexto municipal (2010–2023)

Projeto de análise estatística reprodutível sobre o tema indicado no título. O
relatório acadêmico fornecido estabeleceu uma pergunta associativa preliminar.
A unidade principal pretendida foi atualizada para município × ano do ENEM;
o estimando e o desenho ainda precisam ser formalizados antes da inferência.

## Estado atual

- **Estado do trabalho: 2º estado — Relatório Descritivo em elaboração.**
- **Única etapa concluída: Proposta.**
- Ainda não concluídos: Relatório Descritivo, Relatório Final e Apresentação.
- Disponíveis localmente: pacotes oficiais ENEM 2010–2022 e pacote 2023 preexistente.
- Contexto municipal: fontes IBGE, INEP e Ipeadata importadas; cobertura varia por
  indicador e ano. Não foram interpolados indicadores censitários.
- Importação, fontes e reprodução: [docs/importacao.md](docs/importacao.md).
- Auditoria técnica: [reports/data-quality.md](reports/data-quality.md).
- Tamanho da amostra e parâmetros estatísticos: **não definidos**.
- Análise estatística: ainda não iniciada.
- Pergunta pretendida, unidade principal e pendências: documentadas em
  `docs/methodology.md`; a população ainda não foi definida.
- Estimando, critérios de inclusão, vínculo residencial e método: pendentes.
  Escola e local de prova não serão usados como residência.
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
