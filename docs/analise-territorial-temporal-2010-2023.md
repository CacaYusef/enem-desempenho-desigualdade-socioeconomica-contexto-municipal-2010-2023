# Correlações municipais temporais — ENEM 2010–2023

Extensão descritiva registrada na
[decisão 007](decisions/007-correlacoes-municipais-temporais.md). O trabalho
permanece no 2º estado; somente a Proposta foi concluída. Não há econometria,
testes, intervalos ou afirmações causais.

## Reprodução

```powershell
python -m enem_analysis.data.temporal_municipal_correlations
python -m enem_analysis.data.validate_temporal_municipal
python -m enem_analysis.visualization.temporal_municipal_correlations
python -m pytest
python -m ruff check .
```

Saídas: `data/processed/territorial_series_2010_2023/`. O manifesto registra
hashes de todos os cadastros elegíveis, da base municipal e dos derivados;
`validacao.json` registra oito verificações aprovadas. As figuras usam estilo
`ggplot` e duas famílias cromáticas: azul e amarelo, com variação apenas de
tonalidade.

## Limites de leitura

As correlações descrevem médias dos candidatos elegíveis ligados ao município
da escola. Mudanças anuais podem refletir cobertura municipal, composição de
participantes, mudanças do exame e mensuração, além de mudanças substantivas.
PIB está em reais correntes, mas correlação dentro de cada ano não muda sob
reescala linear positiva. Indicadores censitários não foram interpolados.
