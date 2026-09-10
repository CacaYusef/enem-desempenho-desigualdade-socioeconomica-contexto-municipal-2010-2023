# Dados processados

Produtos derivados devem ser gerados aqui por código versionado. Para cada
produto, documente:

- arquivos brutos de entrada e respectivos anos;
- script/comando e versão do código;
- filtros, exclusões, conversões, chaves e agregações;
- contagens antes e depois de cada transformação relevante;
- esquema, unidade de observação e tratamento de ausências;
- hash ou versão do produto quando usado em um resultado publicado.

Não adicione arquivos derivados manualmente nem versione arquivos de dados.

## Produtos atuais

- `enem/year=ANO/participantes.parquet`: todas as linhas e colunas do CSV ENEM,
  sem amostragem ou critérios de inclusão;
- `municipal/base_municipio_ano.parquet` e `.csv`: contexto por município–ano,
  com campos ENEM ainda nulos porque residência não foi validada;
- `municipal/indicadores_longos.parquet`: valores, status, fonte e referência
  temporal antes da abertura em colunas;
- `municipal/correspondencia_enem_municipios.*`: auditoria por código e ano das
  geografias de escola e prova, sem convertê-las em residência;
- `municipal/education/`: linhas publicadas e totais municipais das taxas de
  rendimento escolar por ano.

Veja `../../docs/importacao.md` para comandos e proveniência e
`../../reports/data-quality.md` para contagens, validações e limitações. Estes
arquivos não constituem uma amostra ou análise estatística concluída.
