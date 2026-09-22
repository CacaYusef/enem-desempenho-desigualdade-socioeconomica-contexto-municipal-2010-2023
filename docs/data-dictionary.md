# Dicionário de dados

Status: inventário multianual de importação e dicionário analítico do recorte
territorial 2023. A harmonização multianual permanece incompleta.
A fonte normativa para 2023 é
`data/raw/microdados_enem_2023/microdados_enem_2023/DICIONÁRIO/Dicionário_Microdados_Enem_2023.xlsx`.
Mapeamentos de códigos devem ser transcritos e validados contra esse arquivo;
categorias não serão deduzidas pelo nome da variável.

## Inventário de fontes

| Conjunto | Arquivo | Formato | Unidade/nível | Estado |
|---|---|---|---|---|
| Participantes ENEM 2023 | `DADOS/MICRODADOS_ENEM_2023.csv` | CSV, `;`, Windows-1252, 76 colunas | Uma linha por inscrição, a confirmar no documento técnico | Disponível |
| Itens de prova 2023 | `DADOS/ITENS_PROVA_2023.csv` | CSV | Item/prova, a confirmar | Disponível |
| Dicionário oficial 2023 | `DICIONÁRIO/Dicionário_Microdados_Enem_2023.xlsx` | XLSX | Metadados | Disponível |
| ENEM 2010–2022 | `data/raw/enem/ANO/microdados_enem_ANO.zip` | CSV e documentação no ZIP | Inscrição × edição | Baixados do INEP |
| Contexto municipal | `data/raw/municipal/` | JSON, TXT, XLS/XLSX em ZIP | Município × ano, conforme fonte | Importado |

Os caminhos dos três primeiros itens são relativos a
`data/raw/microdados_enem_2023/microdados_enem_2023/`.

## Dicionários e rastreabilidade multianuais

- [Dicionário municipal CSV](sources/municipal/dicionario_variaveis.csv) e
  [JSON](sources/municipal/dicionario_variaveis.json): descrição, fonte e URL,
  ano, unidade, geografia, cálculo, categorias e limitações por indicador–ano.
- `docs/sources/enem/dictionary_ANO.json`: transcrição das planilhas oficiais de
  cada edição, incluindo categorias e linhas originais. Questões com nomes
  iguais não são consideradas semanticamente equivalentes entre anos.
- [Inventário anual](sources/enem/inventario_anual.csv),
  [ausências por coluna](sources/enem/disponibilidade_variaveis.csv) e
  [matriz de disponibilidade](sources/enem/matriz_disponibilidade.csv).
- [Cobertura municipal](sources/municipal/cobertura_variaveis.csv): contagens,
  ausências, mínimo e máximo. Indicadores importados são candidatos, não
  covariáveis selecionadas para um modelo.

Na ingestão ENEM, todos os campos são strings; somente campos originalmente
vazios tornam-se nulos. Nenhum código de categoria é convertido ou imputado.
Nos indicadores municipais, conserva-se `valor_original` junto a `valor` e
`status_valor`. Os símbolos SIDRA `...`, `..` e `X` não viram zero; `-` significa
zero absoluto **apenas no SIDRA**, conforme documentação oficial. Em outras
fontes, marcadores de ausência permanecem distintos de zero observado.

O painel usa `codigo_ibge` de sete dígitos como string e `ano_enem` como inteiro.
Os indicadores numéricos são nullable; PIB/VAB estão em mil reais correntes,
PIB per capita em reais, percentuais em 0–100 e IDHM/Gini em 0–1. A renda Atlas
em reais de 2010 não deve ser confundida com renda censitária corrente de 2022.
As unidades exatas e os universos de cada coluna constam no dicionário municipal.

As correspondências registram código/nome original ENEM, município, UF, ano,
tipo de localização e validação por código. Validar um código de escola ou
prova **não** valida residência. As colunas de notas e contagens ENEM no painel
contextual são placeholders nulos, não resultados calculados nem zeros.

## Grupos observados no cabeçalho de participantes de 2023

| Variáveis | Papel aparente a validar | Tipo inicial | Unidade/valores | Ausências | Origem |
|---|---|---|---|---|---|
| `NU_INSCRICAO` | Identificador de inscrição; não usar como medida | Identificador/string | Sem unidade | Não inferido | ENEM 2023 |
| `NU_ANO` | Ano da edição | Inteiro | Ano-calendário | Não inferido | ENEM 2023 |
| `TP_FAIXA_ETARIA`, `TP_SEXO`, `TP_ESTADO_CIVIL`, `TP_COR_RACA`, `TP_NACIONALIDADE` | Códigos cadastrais/demográficos | Categórico codificado | Consultar dicionário oficial | Avaliar antes do uso | ENEM 2023 |
| `TP_ST_CONCLUSAO`, `TP_ANO_CONCLUIU`, `TP_ESCOLA`, `TP_ENSINO`, `IN_TREINEIRO` | Situação educacional declarada/cadastral | Categórico codificado/binário | Consultar dicionário oficial | Avaliar antes do uso | ENEM 2023 |
| `CO_MUNICIPIO_ESC`, `NO_MUNICIPIO_ESC`, `CO_UF_ESC`, `SG_UF_ESC` | Localização da escola | Código/texto | Código e nome geográfico | Avaliar ausência estrutural | ENEM 2023 |
| `TP_DEPENDENCIA_ADM_ESC`, `TP_LOCALIZACAO_ESC`, `TP_SIT_FUNC_ESC` | Características da escola | Categórico codificado | Consultar dicionário oficial | Avaliar ausência estrutural | ENEM 2023 |
| `CO_MUNICIPIO_PROVA`, `NO_MUNICIPIO_PROVA`, `CO_UF_PROVA`, `SG_UF_PROVA` | Local de aplicação | Código/texto | Código e nome geográfico | Avaliar antes do uso | ENEM 2023 |
| `TP_PRESENCA_CN`, `TP_PRESENCA_CH`, `TP_PRESENCA_LC`, `TP_PRESENCA_MT` | Situação de presença por área | Categórico codificado | Consultar dicionário oficial | Não recodificar como zero | ENEM 2023 |
| `CO_PROVA_CN`, `CO_PROVA_CH`, `CO_PROVA_LC`, `CO_PROVA_MT` | Código de prova por área | Categórico codificado | Consultar dicionário oficial | Avaliar antes do uso | ENEM 2023 |
| `NU_NOTA_CN`, `NU_NOTA_CH`, `NU_NOTA_LC`, `NU_NOTA_MT` | Nota por área | Numérico | Escala a confirmar na documentação técnica | Manter ausente distinto de zero | ENEM 2023 |
| `TX_RESPOSTAS_CN`, `TX_RESPOSTAS_CH`, `TX_RESPOSTAS_LC`, `TX_RESPOSTAS_MT` | Sequência de respostas | String | Formato a confirmar | Avaliar antes do uso | ENEM 2023 |
| `TP_LINGUA` | Opção de língua | Categórico codificado | Consultar dicionário oficial | Avaliar antes do uso | ENEM 2023 |
| `TX_GABARITO_CN`, `TX_GABARITO_CH`, `TX_GABARITO_LC`, `TX_GABARITO_MT` | Sequência de gabarito | String | Formato a confirmar | Avaliar antes do uso | ENEM 2023 |
| `TP_STATUS_REDACAO` | Situação da redação | Categórico codificado | Consultar dicionário oficial | Não recodificar como nota zero sem regra | ENEM 2023 |
| `NU_NOTA_COMP1`–`NU_NOTA_COMP5`, `NU_NOTA_REDACAO` | Notas de competências e redação | Numérico | Pontuação/escala a confirmar | Manter ausente distinto de zero | ENEM 2023 |
| `Q001`–`Q025` | Questionário contextual/socioeconômico | Categórico codificado | Consultar dicionário oficial por item | Avaliar códigos de não resposta | ENEM 2023 |

## Campos obrigatórios para a próxima revisão

Para cada variável efetivamente selecionada, completar: significado oficial,
tipo de armazenamento, escala estatística, unidade, categorias válidas, códigos
de ausência/não resposta, universo de aplicação, origem, compatibilidade por ano
e transformação analítica. Nenhuma categoria deve ser inventada.

## Derivados da análise descritiva — decisão 005

Em `data/processed/descriptive/amostra_contexto_escola.parquet`, a unidade é
inscrição × edição, não município. Os pesos, identificadores e campos originais
da amostra são preservados. A tabela tem 280.000 linhas e 66 colunas.

| Campo ou grupo | Significado e regra |
|---|---|
| `peso_desenho`, `pi_h`, `N_h`, `n_h`, `estrato` | Herdados da amostra: peso inverso da probabilidade condicional de seleção. Não são probabilidade de participar do ENEM. |
| `peso_calibrado_proxy` | Sensibilidade de 2012–2023 à proxy PNAD; nulo fora do domínio coberto. Não se substitui nulo por zero. |
| `codigo_ibge`, `ano_enem`, `vinculo` | Chave municipal vinculada à escola no ano exato e resultado da junção à esquerda. Nunca residência. |
| `*_rotulo` | Rótulos originais dos itens, obtidos do mapa anual; letras idênticas em anos distintos não asseguram equivalência. `codigos_anuais.csv` preserva coluna, código e rótulo. |
| `renda_grupo` | Só 2023: Q006 A/B até R$ 1.320; C/D de R$ 1.320,01 a 2.640; E–H de R$ 2.640,01 a 6.600; I–Q acima de R$ 6.600. Rótulos abreviados nos CSVs não tornam intervalos sobrepostos. |
| `moradores_num` | Q005 numérica somente em 2023; valores observados 1–20. Não se atribuiu renda per capita a partir de pontos médios das faixas. |
| Indicadores municipais | `pib_per_capita_reais`, `educ_abandono_medio_pct`, `populacao`, `renda_domiciliar_per_capita_censo2022_reais`, `renda_per_capita_atlas_reais2010`, `gini_atlas`, `idhm_educacao`. Unidades e anos conforme dicionário municipal, sem interpolação. |

Nas tabelas de saída, `n` é contagem bruta; `peso_total`/`total_estimado` é soma
de pesos; `pct_ponderado` usa essa soma no denominador. Em correlações,
`n_pares`/`peso_pares` indicam o domínio completo do par. `variancia` é dispersão
descritiva com denominador soma dos pesos, não variância da média; `dp` é sua
raiz quadrada. Quantis usam a inversa da distribuição empírica ponderada.
`n_ausente`, `n_nao_declarado` e `n_codigo_ou_valor_invalido` são distintos.
Extremos fora das cercas de 1,5 IQR são marcados, nunca excluídos pelo critério.

## Derivados vigentes — análise territorial 2023, decisão 006

`data/processed/territorial_2023/candidatos_2023.parquet` contém 1.027.924
inscrições elegíveis e preserva os códigos originais. `municipios_2023.parquet`
contém 5.475 agregados de municípios da escola. `contexto_municipal.parquet`
contém o quadro IBGE de 5.570 municípios. Dicionários detalhados e cobertura
estão no mesmo diretório em `dicionario_individual.json`,
`dicionario_contextual.json`, `qualidade_individual.csv` e
`cobertura_contextual.csv`.

| Campo ou grupo | Significado e regra |
|---|---|
| `NU_NOTA_MT` | Desfecho principal. Nota numérica, finita e não negativa de presente em matemática. Zero observado é preservado; não se impõe teto de 1.000 à TRI. |
| `renda`, `renda_grupo` | Rótulo oficial de Q006 e quatro grupos de apresentação A/B, C/D, E–H, I–Q. Não são renda contínua. |
| `pai`, `mae`, `raca`, `sexo`, `idade`, `escola`, `dependencia`, `localizacao`, `computador`, `internet` | Rótulos oficiais de 2023; não declaração e “não sabe” permanecem categorias. |
| `moradores` | Q005 numérica observada, de 1 a 20; não utilizada para imputar renda per capita. |
| `codigo_ibge`, `municipio`, `uf`, `regiao`, `vinculo` | Município/UF/região da escola. Ausência não é substituída pelo município de prova ou residência. `Centro-oeste` da fonte foi padronizado para `Centro-Oeste`. |
| `ideb_2023`, `saeb_mt_2023`, `saeb_lp_2023` | Indicadores municipais publicados da rede pública, referência 2023, extraídos da divulgação vintage 2025 apenas nas colunas 2023. |
| `abandono_2023`, `aprovacao_2023`, `reprovacao_2023`, `distorcao_2023` | Percentuais municipais do ensino médio em 2023; rede/categoria total conforme fonte INEP. |
| `pib_pc_2023` | PIB municipal per capita em reais correntes, IBGE 2023; não é renda domiciliar. |
| `renda_pc_2022`, `populacao_2022`, `urbanizacao_2022` | Indicadores municipais do Censo 2022; defasagem de um ano em relação ao ENEM. |
| `internet_escolas_pct`, `laboratorio_escolas_pct` | Proporção simples de escolas ativas com ensino médio e item observado, todas as redes; não ponderada por matrículas. |
| `quintil_*` | Cortes nacionais entre municípios n≥30, quantis pela EDF inversa; empates não são separados. |

Nos agregados municipais, `n`, `media`, `mediana`, `variancia`, `dp`, `q1` e
`q3` descrevem matemática; a variância usa ddof=0. `prop_*` é composição dentro
do município e soma 1 para cada bloco categórico. `n_publica` e `media_publica`
definem o domínio de candidatos de escola pública usado na sensibilidade do
IDEB. Correlações principais têm igual peso municipal; `pearson_ponderado_n` é
um estimando de sensibilidade distinto. Não há p-valores nem coeficientes de
regressão nesses produtos.
