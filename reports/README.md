# Relatórios

- `figures/`: visualizações finais geradas por código, separadas por análise.
- `tables/`: CSVs das tabelas exibidas nos relatórios, na ordem em que aparecem
  em cada PDF e separados por análise. O separador é `;` e a codificação é
  UTF-8 com BOM para facilitar a abertura em planilhas.
- `report/`: texto e artefatos finais.

Todo artefato deve apontar para a análise e os dados que o produziram. Não edite
manualmente números já calculados pelo pipeline.
Os CSVs analíticos continuam em `data/processed/`; as tabelas de `reports/tables/`
são cópias de apresentação geradas a partir deles, não substitutos dos dados.
