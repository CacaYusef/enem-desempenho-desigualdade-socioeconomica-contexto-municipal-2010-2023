# Dados

## Convenção

- `raw/`: cópia imutável do material recebido da fonte.
- `processed/`: produtos derivados exclusivamente por código versionado.

Não edite nem sobrescreva arquivos em `raw/`. Uma correção deve virar uma nova
etapa de transformação, com entrada, saída, regra e impacto documentados. Dados
brutos e processados estão fora do Git; somente seus metadados são versionados.

## Cobertura disponível

Na inicialização, há apenas o pacote do ENEM 2023. O intervalo 2010–2022 e as
bases de contexto municipal ainda não foram fornecidos. A aquisição do pacote de
2023 ocorreu antes desta inicialização e sua data e URL exatas não estão
documentadas.

Consulte `raw/README.md` para inventário técnico e hashes e
`../docs/data-dictionary.md` para o dicionário em construção.
