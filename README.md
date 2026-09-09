# Desempenho no ENEM, desigualdade socioeconômica e contexto municipal (2010–2023)

Projeto de análise estatística reprodutível sobre o tema indicado no título. O
relatório acadêmico fornecido estabeleceu uma pergunta associativa preliminar e
um desenho de cortes transversais repetidos; o estimando e a estratégia de
identificação ainda precisam ser formalizados antes da análise inferencial.

## Estado atual

- **Estado do trabalho: 2º estado — Relatório Descritivo em elaboração.**
- **Única etapa concluída: Proposta.**
- Ainda não concluídos: Relatório Descritivo, Relatório Final e Apresentação.
- Disponível localmente: pacote oficial de microdados do ENEM 2023.
- Ainda ausentes: microdados de 2010–2022 e dados de contexto municipal.
- Análise estatística: ainda não iniciada.
- Pergunta e população preliminares: documentadas em `docs/methodology.md`.
- Estimando, critérios operacionais de inclusão, vínculo municipal e método:
  pendentes.
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
