# Relatório descritivo — versão para revisão

## Entrega e estado acadêmico

[Documento Google Docs, aba Relatório Descritivo](https://docs.google.com/document/d/1Cx9j8C2Y5DFU4UHQxvMO5BwhnWFrDsr10FpCOy9QU6o/edit?tab=t.r484yf39er9r).
A proposta existente foi preservada em sua própria aba. Foram acrescentados
introdução, origem e apresentação dos dados, análise descritiva e conclusões,
com nove tabelas, sete figuras e seis links de fontes oficiais.

[PDF local do relatório](../reports/report/relatorio_descritivo_enem.pdf).
O PDF local é gerado pelo código do projeto; sua paginação não é a do Google
Docs. A etapa continua no **2º estado**, com **Proposta concluída** e relatório
descritivo disponível para revisão dos autores. Não houve análise inferencial.

## Universo e escolhas

Foram preservadas as 280.000 inscrições sorteadas (20.000/ano, 2010–2023) e as
regras da [decisão 004](decisions/004-amostra-estratificada-calibracao.md).
Cada linha representa inscrição × edição, sem acompanhamento longitudinal.
O cadastro elegível de 2023 contém 983.810 inscrições; a amostra de 2023 tem
20.000. Os filtros selecionam concluintes declarados regulares que realizaram
as provas e satisfazem os critérios de nota/redação, não todos os concluintes.

A [decisão 005](decisions/005-relatorio-descritivo.md) detalha as regras de
resumo, pesos, extremos, recortes e junção municipal. Há séries anuais e
detalhamento de 2023. As cinco notas permanecem separadas. Códigos de renda,
raça, sexo e escolaridade não foram usados como números contínuos.

## Principais resultados observados

- Em 2023, a média ponderada de matemática foi 538,8, mediana 531,1 e
  desvio-padrão 127,0 pontos.
- Matemática: 477,6 pontos na faixa familiar até R$ 1.320 e 648,6 acima de
  R$ 6.600; diferença descritiva de 171,1 pontos, sem ajuste por confundimento.
- A diferença privada–pública em matemática foi 122,5 pontos. A presença de
  escola privada variou de 3,73% a 71,31% entre aquelas faixas extremas de renda:
  renda e escola não são explicações independentes identificadas por essas médias.
- Matemática e redação tiveram correlação ponderada de 0,519 em 2023.
- Município da escola faltou em 6.041 casos de 2023 (30,97% ponderados). Nos
  vinculados, matemática teve média 555,4; nos demais, 501,7. A análise contextual
  não pode ser generalizada automaticamente para os casos sem localização.
- Renda municipal e IDHM-E tiveram associações positivas nos respectivos anos
  censitários. Abandono em 2023 teve correlação quase nula (+0,041), frente a
  −0,048 em 2022: não é evidência de benefício do abandono nem efeito causal.

Ausentes não viraram zero. Zeros nas provas objetivas de 2023 foram conferidos
na base anual integral derivada, mas a causa de cada zero não foi determinada.
Extremos permanecem nos cálculos. Não houve exclusão adicional nem imputação.

## Reprodução e arquivos

Com o ambiente do projeto ativado e as importações/amostra já disponíveis:

```powershell
python -m enem_analysis.data.descriptive_analysis
python -m enem_analysis.visualization.descriptive_report
python -m pytest
python -m ruff check .
```

As saídas ficam em `data/processed/descriptive/`:

- `manifest.json`: hashes das entradas, versões, controles e dimensões;
- `qualidade.csv`, `zeros_2023.csv`, `codigos_anuais.csv`: auditoria e semântica;
- `resumos_anuais.csv`, `frequencias.csv`, `resumos_grupos.csv`: medidas por ano/grupo;
- `correlacoes.csv`, `contingencia_renda_escola_2023.csv`: associações;
- `cobertura_contextual.csv`, `selecao_contextual_2023.csv`: cobertura/seleção;
- `sensibilidade_pesos.csv`: desenho versus calibração no mesmo domínio;
- `report_blocks.json`, `relatorio_descritivo.md`: conteúdo do relatório;
- `amostra_contexto_escola.parquet`: derivado individual local, não publicar no Git.

As sete figuras publicadas ficam em `reports/figures/descriptive/`; as nove
tabelas do PDF são exportadas para `reports/tables/descriptive/`. Os CSVs
analíticos listados acima permanecem em `data/processed/descriptive/`.

Os comandos reproduzem cálculos e PDF local, não sobrescrevem o Google Docs.
As atualizações nativas do documento foram verificadas por releitura de tabelas,
conteúdo, imagens e exportação. A inferência futura deverá pré-especificar
contrastes e hipóteses, tratar pesos/estratos/dependência territorial, seleção,
comparabilidade e multiplicidade. A calibração externa continua experimental;
não identifica a média de todos os concluintes brasileiros.
