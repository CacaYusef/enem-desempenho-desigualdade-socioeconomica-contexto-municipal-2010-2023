# Análise descritiva socioeconômica e territorial — ENEM 2023

## Estado e produto principal

O trabalho permanece no **2º estado — Relatório Descritivo em elaboração**;
**somente a Proposta foi concluída**. Esta é uma versão para revisão dos autores,
não Relatório Final. A etapa econométrica foi adiada por decisão explícita.

Produto principal:
[relatorio_descritivo_territorial_enem_2023.pdf](../reports/report/relatorio_descritivo_territorial_enem_2023.pdf).
O desenho está na [decisão 006](decisions/006-reconstrucao-enem-2023.md).

## Universo e resultados de controle

- 3.933.955 inscrições lidas no Parquet integral de 2023;
- 1.027.924 elegíveis: conclusão declarada em 2023, ensino regular, não
  treineiro, presente em matemática e nota finita não negativa;
- nenhuma subamostragem: π condicional=1 e peso=1;
- 709.066 candidatos com município da escola identificado (68,98%);
- 5.475 municípios observados; referência n≥30: 2.341 municípios e 672.090
  candidatos vinculados;
- 5.183 notas iguais a zero e todos os extremos preservados;
- 22 verificações independentes aprovadas em `validacao.json`;
- zero regressões, testes, p-valores, intervalos inferenciais ou ICC.

## Fontes

Os microdados são do INEP. O contexto contemporâneo combina IDEB/Saeb municipal
público, rendimento, distorção idade-série e Censo Escolar de 2023; PIB per
capita municipal do IBGE de 2023; e renda domiciliar per capita, população e
urbanização do Censo 2022, sempre identificadas com defasagem de um ano. O IDEB
é o agregado municipal publicado, não média calculada das escolas. IDHM/Gini
2010 ficaram fora do núcleo contemporâneo.

Catálogo específico: `docs/sources/territorial_2023_catalog.json`. Manifestos e
hashes: `docs/sources/manifests/territorial_*.json`. O servidor do INEP reiniciou
TLS no ambiente de aquisição; os mesmos caminhos oficiais foram obtidos via HTTP
e verificados por CRC/SHA-256. A limitação está registrada, sem ocultar a rota.

## Produtos derivados

Tudo fica em `data/processed/territorial_2023/`:

- `candidatos_2023.parquet`: base individual elegível com contexto;
- `municipios_2023.parquet/csv`: desempenho e composições municipais;
- `contexto_municipal.parquet/csv`: indicadores para os 5.570 municípios;
- `grupos_individuais.csv`, `regioes.csv`, `robustez_areas.csv`;
- `associacoes_municipais.csv`, `distribuicoes_contextuais.csv`,
  `desempenho_quintis.csv` e `cortes_quintis.json`;
- `comparacao_cobertura.csv`, `cobertura_contextual.csv` e
  `sensibilidade_n_municipal.csv`;
- `representacao_populacoes.csv`: alvo/base/amostra/pesos; alvo externo exato
  declarado indisponível, sem preenchimento por proxy incompatível;
- `referencia_proxy_pnad.csv`: referência contextual, não alvo de calibração;
- `validacao.json`, dicionários e manifestos;
- `figures/`: onze figuras usadas no PDF, com estilo `ggplot` e sistema
  cromático restrito a duas famílias (azul e amarelo), variando apenas suas
  tonalidades; cinzas são reservados à estrutura gráfica e a ausências.

## Reprodução

Com o ambiente ativado e as fontes já adquiridas:

```powershell
python -m enem_analysis.data.territorial_context
python -m enem_analysis.data.territorial_analysis
python -m enem_analysis.data.validate_territorial
python -m enem_analysis.visualization.territorial_figures
python -m enem_analysis.visualization.territorial_report
python -m pytest
python -m ruff check .
```

O Parquet integral de entrada tem SHA-256
`b2c06ec7d7a820f5ca8947d0c77735952b5d4435d88f71e1a3ca66b597cf44c0`.
Hashes dos derivados e das quatro novas fontes constam em `validacao.json` e
`relatorio_manifest.json`.

## Leitura substantiva responsável

A média de matemática foi 532,8 pontos. Entre os quatro grupos de apresentação
da renda, a média passou de 472,4 (até R$ 1.320) a 645,6 (acima de R$ 6.600),
diferença bruta de 173,2 pontos. A correlação ecológica, entre municípios n≥30,
da renda domiciliar per capita de 2022 com a média ENEM foi 0,735 (Pearson) e
0,765 (Spearman). O IDEB mostrou associação muito mais heterogênea: Pearson
nacional 0,337 com igual peso municipal, mas 0,023 quando ponderado pelo número
de candidatos, e diferenças grandes entre regiões.

Esses números não são efeitos causais nem resultados ajustados. A cobertura do
município é seletiva: candidatos vinculados tiveram média 548,9, contra 497,0
entre os não vinculados, e diferiram fortemente em renda e tipo de escola. Toda
interpretação territorial deve permanecer restrita ao domínio observado.
