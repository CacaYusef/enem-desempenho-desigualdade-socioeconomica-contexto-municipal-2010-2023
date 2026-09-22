# Correlações municipais temporais, 2010–2023

Data: 2026-09-21. Pedido: estender a análise de correlações municipais de 2023
para 2010–2022, observar a direção e a evolução das associações e anexar somente
os gráficos ao final do Relatório Descritivo no Google Docs.

## Decisão

- A unidade desta extensão é **município da escola × ano**. Município da escola
  não é residência.
- Para reproduzir a precisão da análise territorial de 2023, são usados os
  **cadastros elegíveis integrais** já gerados na decisão 004, não a subamostra
  operacional de 20 mil. Isso não substitui nem refaz a amostra da decisão 004;
  cria um derivado municipal separado para estabilizar as médias dentro de
  município.
- A elegibilidade temporal é a regra comparável da decisão 004: conclusão
  declarada no ano, ensino regular, não treineiro quando observável, presença
  nas quatro provas, cinco notas numéricas e redação regular. O ponto de 2023 é
  reestimado nesse mesmo universo e, portanto, não deve ser confundido com o
  recorte de matemática da decisão 006.
- Cada uma das cinco notas é analisada separadamente. Não se cria média geral
  das provas nem se interpreta diferença entre escalas como evolução de nível.
- O corte principal preserva municípios com pelo menos 30 candidatos elegíveis;
  20 e 50 são sensibilidades. Pearson e Spearman dão igual peso aos municípios.
  Pearson ponderado pelo número de candidatos é uma sensibilidade com outro
  estimando.
- PIB per capita, salário médio formal do CEMPRE, aprovação e abandono no ensino
  médio formam as trajetórias repetidas. A série salarial termina em 2021 por
  quebra de fonte em 2022. IDEB/Saeb é mostrado apenas em 2017, 2019, 2021 e
  2023, anos presentes na divulgação local. Não há interpolação.
- Renda, Gini, pobreza, alfabetização e IDHM são mostrados somente como âncoras
  de 2010 ou 2022. Conceitos de Atlas 2010 e Censo 2022 não são ligados como se
  fossem a mesma série.
- Linhas conectam pontos apenas para leitura. Não são tendências estimadas,
  testes, intervalos, regressões ou efeitos causais.

## Produtos

Os derivados ficam em `data/processed/territorial_series_2010_2023/`, incluindo
agregados município–ano, correlações, cobertura, manifesto, validação e seis
figuras. O Google Docs recebe apenas as figuras, conforme pedido; dados e
escolhas ficam auditáveis no repositório.
