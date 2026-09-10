# Dados

## Convenção

- `raw/`: cópia imutável do material recebido da fonte.
- `processed/`: produtos derivados exclusivamente por código versionado.

Não edite nem sobrescreva arquivos em `raw/`. Uma correção deve virar uma nova
etapa de transformação, com entrada, saída, regra e impacto documentados. Dados
brutos e processados estão fora do Git; somente seus metadados são versionados.

## Cobertura disponível

Na inicialização havia apenas o pacote ENEM 2023. Agora também estão locais os
13 pacotes oficiais de 2010–2022, além de fontes municipais IBGE, INEP e Ipeadata.
A aquisição do pacote 2023 precedeu a inicialização; sua data e URL exatas
continuam desconhecidas. Os demais downloads têm URL, data, tamanho e SHA-256
em `../docs/sources/manifests/`.

Os ZIPs ENEM ficam em `raw/enem/ANO/`; a pasta 2023 original não foi movida ou
substituída. As fontes municipais ficam em `raw/municipal/`. Cada edição ENEM
gera `processed/enem/year=ANO/participantes.parquet`, com todas as colunas e
linhas, sem definir uma amostra. Indicadores contextuais e correspondências
geográficas ficam em `processed/municipal/`.

`processed/municipal/base_municipio_ano.parquet` e sua cópia CSV contêm o contexto
municipal, **não uma base analítica concluída de participantes residentes**.
As colunas ENEM dessa tabela permanecem ausentes, pois escola/prova não validam
residência. `indicadores_longos.parquet` preserva o valor original, a fonte,
`ano_dado`, `ano_enem` e `defasagem_anos`; só há associação temporal exata.
Consulte `../docs/importacao.md` para executar novamente a importação.

Consulte `raw/README.md` para inventário técnico e hashes e
`../docs/data-dictionary.md` para o dicionário em construção.
