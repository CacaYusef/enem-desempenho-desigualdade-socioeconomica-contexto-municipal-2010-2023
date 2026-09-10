# Qualidade técnica da importação

Escopo: ingestão ENEM e contexto municipal 2010–2023, execução de setembro de
2026. Este documento **não é o Relatório Descritivo acadêmico concluído**.
O trabalho permanece no 2º estado; somente a Proposta foi concluída.

## Inventário e conservação

- **ENEM:** 14 edições, 81.962.210 registros inscrição–edição. São contagens
  integrais dos arquivos, não pessoas únicas nem tamanho da futura amostra.
  Todas as linhas e colunas dos CSVs principais foram preservadas; nenhuma
  exclusão por treineiro, conclusão, presença, nota ou covariável foi aplicada.
- **Painel contextual:** 77.965 linhas, 114 colunas e nenhuma chave
  município–ano duplicada. A referência PIB contém 5.565 municípios em
  2010–2012 e 5.570 em 2013–2023. Os 101 indicadores são candidatos, não
  covariáveis selecionadas; há 435 definições indicador–ano no dicionário.
- **Base longa municipal:** 2.422.447 observações de indicador, incluindo
  marcadores de ausência e registros sem correspondência. Não representa
  2.422.447 municípios ou uma amostra desse tamanho.
- **Integridade:** 113 manifestos de aquisição registram hashes; os ZIPs foram
  validados por CRC. O CSV 2023 preexistente manteve seu hash. Os derivados
  ENEM e escolares também têm hashes registrados.

Detalhes: [inventário ENEM](../docs/sources/enem/inventario_anual.csv),
[auditoria municipal](../docs/sources/municipal/qualidade.json) e
[verificação reproduzível](../docs/sources/verification.json).

## Localização e correspondências

As 14 edições adquiridas contêm município de escola e prova, **não residência**.
Os dicionários foram lidos e os significados inventariados separadamente.
Todos os códigos ENEM não vazios encontraram correspondência exata no ano;
nenhuma correspondência por aproximação de nome foi aplicada. Há 14 grupos
ano–escola de código ausente no arquivo de não correspondidos, não 14
municípios desconhecidos. Nenhum registro ENEM foi descartado por esse motivo.

A [contagem por ano e tipo de localização](../docs/sources/municipal/correspondencia_resumo.csv)
separa municípios integrados, códigos não integrados, códigos ausentes e
registros envolvidos. Há 101.565 grupos de código/nome/ano/tipo no arquivo de
correspondência e zero sugestões por nome para revisão.

**Junção por residência não realizada.** Contagens e notas ENEM na tabela
contextual continuam nulas, nunca zero. Não se pode interpretar o painel como
associação entre contexto residencial e desempenho de seus residentes.

## Cobertura temporal e divergências territoriais

Os indicadores só são associados ao mesmo ano da edição: nenhuma interpolação,
repetição censitária entre anos ou escolha de defasagem analítica foi feita.
População está disponível em 2010–2022 no conjunto adquirido; não foi criada
uma observação de 2023 usando o Censo 2022. IDHM/Gini e a maioria das séries
Atlas são de 2010. A série de analfabetismo do Ipeadata também contém 2022,
com documentação que remete ao Censo 2022; o nome técnico do alias não garante
constância metodológica. CEMPRE antes/depois de 2022 tem colunas separadas.

Há **96 observações municipais sem chave na referência PIB do mesmo ano**;
88 são marcadores de ausência e oito têm valores publicados. As oito estão
em 2012: população para 1504752, 4212650, 4220000, 4314548 e 5006275; unidades
locais CEMPRE para 4220000 e 5006275; pessoal assalariado para 4220000.
Esses códigos aparecem na referência PIB a partir de 2013. A diferença entre
fontes foi preservada na base longa e em
`data/processed/municipal/indicadores_sem_correspondencia.csv`; não houve
retroação territorial, soma a outro município ou exclusão do dado original.

## Ausências, escalas e extremos

Na base longa há **67.419 valores ausentes**: 66.840 campos vazios, 486
marcadores INEP sem taxa, 81 indisponíveis SIDRA e 12 sob sigilo. Esses números
não contabilizam todas as células vazias criadas ao abrir o painel em colunas
nem os placeholders ENEM. Há também 5.043 zeros absolutos representados por
`-` no SIDRA, convertidos segundo a
[documentação oficial de valores especiais](https://apisidra.ibge.gov.br/home/ajuda).
Ausências e sigilo não foram convertidos em zero.

Foram encontrados **113 valores negativos**, preservados para revisão, nos
indicadores de PIB/VAB/impostos. Entre eles está PIB de Guamaré/RN em 2012,
publicado como −19.046,434 mil reais. Negativo não foi automaticamente rotulado
como erro nem removido; sua interpretação exige revisão dos conceitos e das
notas da fonte. Veja a
[lista de negativos](../docs/sources/municipal/valores_negativos_para_revisao.csv).

Não foram encontrados valores fora de 0–100 nas variáveis percentuais
importadas nem fora de 0–1 em IDHM/Gini, e todos os códigos municipais na base
longa têm sete dígitos. Esses limites são semânticos, não cortes estatísticos
para seleção ou remoção. Nenhum outlier foi excluído.

PIB/VAB/impostos estão em **mil reais correntes**, PIB per capita em reais;
renda Atlas em reais de 2010 e renda censitária 2022 conforme unidade própria.
PIB per capita não é renda domiciliar. O PDF da base PIB informa o uso de
população censitária na divulgação 2022/2023; não se recalculou esse indicador
com outro denominador ou revisão populacional. VAB setorial não está disponível
em 2022–2023, permanecendo ausente.

A [cobertura por indicador–ano](../docs/sources/municipal/cobertura_variaveis.csv)
registra contagens, ausências, mínimo e máximo. A investigação substantiva de
extremos, distribuições, erros de medição e consistência entre variáveis ainda
deverá integrar a análise descritiva.

## Dicionários e comparabilidade ENEM

Não há inscrições repetidas dentro de uma edição segundo `NU_INSCRICAO` nos
arquivos importados. Os campos com `NOTA` no nome não apresentaram valores
negativos nem textos não numéricos entre seus valores preenchidos. As ausências
por coluna e os extremos foram registrados, sem impor teto arbitrário às notas
TRI e sem filtrar presença ou situação da redação.

Há uma divergência literal no dicionário **2012**: o CSV usa `Q001`–`Q062`,
enquanto a planilha oficial usa `Q1`–`Q62`. As 62 colunas aparecem como sem
correspondência **literal** no inventário; as descrições e categorias da planilha
foram preservadas integralmente. Não se trata de perda de respostas na
importação. A equivalência precisa ser formalizada antes da harmonização e uso
analítico. Nos demais anos, todos os nomes de coluna têm correspondência
literal no dicionário principal.

Os pacotes 2010 e 2016 incluem arquivos temporários Excel `~$...xlsx`, que não
são planilhas válidas. Foram ignorados somente na leitura de metadados; os ZIPs
originais e os dicionários efetivos foram preservados.

As taxas escolares usam o total publicado, não médias de redes. A posição das
colunas em 2010 difere de 2011–2023 e foi tratada pelo código e pelos cabeçalhos
originais salvos. Todas as 61 colunas de dados foram preservadas; colunas extras
de formatação foram verificadas como vazias nas linhas de dados.

## Validação e pendências

`python -m pytest` passou nos 16 testes, cobrindo ausências/zeros, duplicidades,
conservação temporal, limites semânticos, categorias e correspondência
geográfica. `python -m ruff check .` passou. O comando
`python -m enem_analysis.data.verify_imports` verifica os hashes locais,
contagens/esquemas, o primeiro registro completo de cada fonte ENEM contra o
Parquet e a igualdade de todos os valores municipais correspondidos entre base
longa e painel. Esse primeiro registro é uma checagem de engenharia, não uma
amostra de pesquisa.

Não foram definidos tamanho da amostra, critérios de inclusão, covariáveis
finais, deflator, parâmetros, testes ou modelo. Permanecem pendentes a solução
do vínculo residencial, harmonização semântica, pergunta operacional viável,
estimando e análise descritiva. Premissas inferenciais, incerteza e tamanhos de
efeito não foram avaliados porque não houve inferência. A aprovação técnica da
importação não equivale à conclusão da base analítica ou do trabalho acadêmico.
