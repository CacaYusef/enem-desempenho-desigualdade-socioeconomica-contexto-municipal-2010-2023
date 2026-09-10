# Importação das fontes — 2010–2023

Estado acadêmico: **2º estado — Relatório Descritivo em elaboração**.
**Somente a Proposta foi concluída.** Esta entrega é preparação técnica dos
dados, não resultado da pesquisa. Amostra, critérios de inclusão, parâmetros,
modelo, percentis, cortes e covariáveis finais continuam indefinidos.

## O que está local

- ENEM: 13 ZIPs oficiais de 2010–2022 baixados do INEP e pacote 2023 preexistente,
  mantido intacto. Os CSVs principais das 14 edições foram convertidos para
  Parquet, preservando todas as linhas e colunas. São 81.962.210 registros de
  inscrição–edição, **não pessoas únicas nem tamanho de amostra definido**.
- Contexto municipal: 77.965 linhas município–ano, 114 colunas, das quais 101
  são indicadores candidatos. Há cinco campos de identificação e oito campos
  reservados à futura integração ENEM/status. Não há seleção de variáveis para
  modelo nem garantia de disponibilidade de cada indicador em todos os anos.
- Proveniência: 113 manifestos de arquivos adquiridos, com URL, data, tamanho e
  SHA-256; ZIPs também foram verificados por CRC na aquisição. A data e URL
  exatas da aquisição preexistente de 2023 continuam desconhecidas.

O armazenamento observado ao concluir a importação é aproximadamente 12,33 GB
em `data/raw/` e 7,33 GB em `data/processed/` (GB decimais). Os ZIPs ENEM novos
somam 9,71 GB. Não é preciso baixar novamente o que já está local. A conversão
lê os ZIPs diretamente, sem extrair cópias completas dos CSVs anuais. A pasta
continua no OneDrive; sua configuração de sincronização não foi alterada.

## De onde vieram os dados

| Fonte oficial | Aquisição e cobertura | Limitação principal |
|---|---|---|
| [INEP — Microdados ENEM](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem) | Pacotes anuais, dicionários e documentação; 2010–2023 | Nos arquivos adquiridos há município de escola e prova, não residência |
| [IBGE — PIB municipal, base TXT 2010–2023](https://ftp.ibge.gov.br/Pib_Municipios/2022_2023/base/base_de_dados_2010_2023_txt.zip) | PIB, PIB per capita, VAB e referência geográfica anual | VAB setorial ausente em 2022–2023; unidades monetárias diferentes |
| [IBGE/SIDRA — População](https://sidra.ibge.gov.br/tabela/6579) | Estimativas 2011–2021; Censos 2010/2022 em tabelas próprias | Não foi criada estimativa anual de 2023 a partir do Censo 2022 |
| [IBGE/SIDRA — Censo 2010](https://sidra.ibge.gov.br/tabela/1552) e [Censo 2022](https://sidra.ibge.gov.br/tabela/4714) | População, área, densidade e tabelas temáticas de renda, instrução, alfabetização, saneamento, internet e urbanização | Indicadores censitários, não séries anuais interpoladas |
| [IBGE — CEMPRE até 2021](https://sidra.ibge.gov.br/tabela/1685) e [desde 2022](https://sidra.ibge.gov.br/tabela/9528) | Unidades locais, pessoal ocupado/assalariado e remunerações | Quebra metodológica; emprego nas organizações não é taxa de desemprego |
| [Ipeadata — Metadados oficiais](http://www.ipeadata.gov.br/api/odata4/Metadados) | 19 séries documentadas: IDHM, Gini, renda, pobreza, escolaridade, trabalho e condições domiciliares | Predominantemente 2010; analfabetismo também traz 2022, com fonte atualizada |
| [INEP — Taxas de rendimento escolar](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/taxas-de-rendimento-escolar) | Planilhas municipais 2010–2023; aprovação, reprovação e abandono | Referem-se às escolas no município, não à residência dos alunos |

As tabelas SIDRA adquiridas são **1552, 1301, 6579, 4714, 9923, 9543, 10295,
3540, 6803, 6805, 10201, 1685 e 9528**. Cada URL completa de consulta, variável,
categoria e ano está no [catálogo municipal](sources/municipal_catalog.json).
As séries Ipeadata e URLs anuais de rendimento escolar estão no
[catálogo complementar](sources/supplement_catalog.json). O
[dicionário municipal](sources/municipal/dicionario_variaveis.csv) contém 435
registros indicador–ano com descrição, fonte/URL, unidade, cálculo e limitações.

Não foram importados DATASUS, SICONFI, IDEB ou IQM/IQIM. Saúde/finanças eram
condicionais na instrução; outras expansões dependem da pergunta e justificativa.

## Produtos e regras

| Produto local | Uso |
|---|---|
| `data/processed/enem/year=ANO/participantes.parquet` | Inscrições com esquema original, strings e vazios como nulos |
| `data/processed/municipal/base_municipio_ano.parquet` e `.csv` | Painel contextual; contagens/notas ENEM ainda nulas |
| `data/processed/municipal/indicadores_longos.parquet` | Valor original, valor numérico, status, fonte e temporalidade por indicador |
| `data/processed/municipal/correspondencia_enem_municipios.parquet` e `.csv` | Código/nome original ENEM, código IBGE, município, UF, ano e tipo de localização |
| `data/processed/municipal/indicadores_sem_correspondencia.csv` | Registros municipais externos à referência anual preservados |
| `data/processed/municipal/municipios_enem_nao_correspondidos.csv` | Localizações ENEM sem código correspondente, inclusive código ausente |
| `data/processed/municipal/possiveis_correspondencias_para_revisao.csv` | Sugestões por nome normalizado exato; nenhuma foi aplicada |
| `data/processed/municipal/education/year=ANO/linhas_fonte.parquet` | Todas as linhas publicadas por município, rede e localização escolar |

A referência de códigos por ano vem da base PIB, não do cadastro corrente:
5.565 unidades em 2010–2012 e 5.570 em 2013–2023. Isso define o suporte técnico
do painel, não a amostra. O cadastro IBGE corrente foi preservado apenas como
referência auxiliar, sem retroagir municípios novos.

Nas planilhas escolares, os indicadores do painel são os totais **publicados**
para rede=Total e localização=Total, sem fazer média entre redes. As outras
linhas permanecem no derivado completo e no original. No Ipeadata, a resposta
integral fica em raw; o recorte técnico município/2010–2023 é contabilizado na
auditoria. Nenhuma linha original é apagada.

Só há coincidência temporal exata: `ano_dado`, `ano_enem` e `defasagem_anos`
estão na base longa. Ausências censitárias não foram imputadas. Defasagens,
deflação e escolhas de ano-base para análise continuam pendentes. Valores
monetários são mantidos na unidade e referência de preços de cada fonte.

## Limitação que impede a junção residencial

Nenhuma das 14 edições adquiridas disponibiliza campo municipal identificado
como residência no CSV principal e respectivo dicionário. Existem campos de
escola e aplicação de prova. Todos os códigos não vazios desses dois tipos
encontraram correspondência por código IBGE no respectivo ano; isso **não**
valida vínculo residencial.

Portanto, não foram calculadas médias, medianas, desvios-padrão, percentis,
proporções ou agregados socioeconômicos ENEM por suposta residência. A tabela
contextual é utilizável para inspeção, mas não deve ser apresentada como base
analítica concluída de residentes. Resolver a localização ou alterar a pergunta
exige decisão metodológica explícita, não uma troca silenciosa de campo.

## Reprodução no PowerShell

Execute na raiz, com `.venv` ativo e dependências do lock instaladas:

```powershell
python -m enem_analysis.data.acquire enem
python -m enem_analysis.data.municipal_catalog
python -m enem_analysis.data.supplement_catalog
python -m enem_analysis.data.enem_import
python -m enem_analysis.data.education_import
python -m enem_analysis.data.municipal_import
python -m enem_analysis.data.integration_audit
python -m enem_analysis.data.verify_imports
python -m pytest
python -m ruff check .
```

Os três primeiros comandos requerem internet quando faltarem arquivos; os
demais usam fontes locais. Arquivos raw existentes são verificados, não
sobrescritos. Falha de checksum exige investigação; não se corrige baixando
por cima. `curl.exe` é usado no Windows para retomar downloads parciais.
2023 é lido da pasta original documentada em `data/raw/README.md`.

Os derivados são regeneráveis. Código e documentação podem ser versionados;
microdados, arquivos municipais e grandes derivados ficam fora do Git.
Consulte o [relatório de qualidade](../reports/data-quality.md), a
[metodologia](methodology.md) e a
[decisão 003](decisions/003-importacao-sem-definir-amostra.md).
