# Reconstrução socioeconômica e territorial — ENEM 2023

Data: 2026-09-21. Plano A–J aprovado pelo usuário. Executar a análise descritiva;
a etapa econométrica será executada somente depois dela. Esta decisão substitui
o escopo principal das decisões 004/005, preservadas como histórico. Não apagar
amostras, relatórios, dados ou códigos anteriores; não usá-los como modelo de foco.

## Pergunta, população e desfecho

Até que ponto características socioeconômicas individuais e diferenças
econômicas, sociais e educacionais entre municípios e regiões brasileiras se
associam às diferenças de desempenho dos candidatos no ENEM 2023?

População substantiva: concluintes do ensino médio regular brasileiro em 2023.
População observada: inscritos nos microdados de 2023. Elegibilidade primária:
TP_ST_CONCLUSAO=2, TP_ENSINO=1, IN_TREINEIRO=0, TP_PRESENCA_MT=1 e NU_NOTA_MT
numérica finita não negativa. Conferir códigos no dicionário de 2023 antes da
execução. Não impor teto universal de 1000 à TRI. Zeros observados permanecem.
Não exigir outras provas nem redação regular. Quantificar exclusões em ordem.
Conclusão é declarada, não diploma observado. TP_ENSINO não permite presumir
que todas as modalidades externas estão corretamente identificadas.

Desfecho principal aprovado: matemática, na escala original. Demais notas são
somente robustez em domínios com presença/nota disponíveis, com denominadores
explícitos; não são explicativas. Não criar indicador composto. As inferências
nacionais para todos os concluintes continuam não identificadas pela seleção
voluntária e pela presença no ENEM.

## Base integral e pesos

Usar todos os elegíveis, lendo colunas necessárias do Parquet integral. Sem
novo sorteio ou uso da amostra antiga. Probabilidade de inclusão no processamento
condicional à elegibilidade=1 e peso=1. Isso não é probabilidade de participar
no ENEM. Proporções externas somente se universo/conceito forem compatíveis.
PNAD séries 3/4 é proxy, não conclusão observada; renda domiciliar e região de
residência não substituem renda familiar e região da escola. Na tabela exigida
de alvo/base/amostra/ponderação, ausências de alvos compatíveis serão explícitas.

## Unidades, contexto e cobertura

Individual: inscrição de 2023. Contexto: município da escola; nunca residência
ou município de prova. Junção à esquerda muitos-para-um por código IBGE e ano
de referência declarado. Região deriva do município/UF escolar validado.
Ausência de município não exclui da descrição individual; ausência de indicador
restringe somente seu domínio específico. Comparar localização conhecida e
ausente em nota, renda, raça, sexo, escola, parentalidade e região observável.

Núcleo contemporâneo: IDEB/Saeb ensino médio 2023, rendimento escolar 2023,
distorção idade-série 2023, PIB per capita 2023. Renda, população e urbanização
censitárias de 2022 podem entrar com defasagem explícita de um ano, sem
renomeá-las como medições de 2023. Atlas/IDHM/Gini 2010 ficam fora do núcleo.
Auditar rede/etapa/cobertura das novas fontes antes de usar. Não construir IDEB
municipal por média de escolas. IDEB público é contexto da rede pública local,
não indicador da escola privada do candidato; analisar rede pública separadamente.

Agregar por município: contagem, média, mediana, variância descritiva (ddof=0),
desvio-padrão, quartis e composições socioeconômicas. Referência para comparações
municipais: n>=30, sensibilidades n>=20 e n>=50. Não aplicar esses cortes à
base individual. Distribuições municipais e correlações principais têm igual
peso municipal; média/correlação ponderada por n é sensibilidade de outro
estimando. Tamanho do ponto pode mostrar n, nunca alegar precisão uniforme.

## Análise descritiva, sem econometria nesta entrega

Ordem: composição individual -> gradientes socioeconômicos -> heterogeneidade
municipal -> diferenças nas cinco regiões. Regiões sempre explícitas: Norte,
Nordeste, Centro-Oeste, Sudeste, Sul. Não substituir por ranking de médias.

Renda, escolaridade, raça, sexo, faixa etária e dependência são categorias.
Manter rótulos oficiais e não declaração; Q005 é contagem. Não imputar renda
pontual nem escolaridade em anos. Faixas originais de renda nos CSV; quatro
grupos para legibilidade A/B, C/D, E–H, I–Q, limites do questionário explicitados.
Esse agrupamento é apresentação, não transformação em escala contínua.

Medidas de distribuição e associação sem testes, p-valores, intervalos ou modelos
ajustados. Pearson e Spearman (postos médios nos empates) em pares completos.
Quintis nacionais calculados entre municípios n>=30 com indicador observado;
cortes idênticos nas regiões, empates no mesmo grupo, informar grupos vazios.
Dispersões e LOESS são descritivas. Por adiamento explícito da econometria,
reta OLS e quaisquer regressões/ICC não serão estimadas nesta etapa; LOESS
somente como guia visual sem interpretação de coeficientes ou inferência.
Não mostrar matriz extensa entre provas nem comparar suas escalas como achado.

Ausentes, inconsistências e extremos quantificados, sem correção silenciosa.
Verificar chaves, cobertura por fonte/rede, códigos, limites e discrepâncias
pública/privada versus dependência. Extremos conservados. Todos os resultados
restritos ao universo/denominador informado. Aprovação/reprovação/abandono e
IDEB/componentes não serão empilhados irrefletidamente em modelos futuros.

## Produtos e rastreabilidade

Novos derivados em data/processed/territorial_2023; novo relatório sem substituir
o anterior. Fontes novas em raw com manifesto, hashes, URL e data; reproduzir
por src/enem_analysis. Registrar ano, unidade, rede, conceitos, limites e
denominadores por indicador. Testes de filtros, junções, grupos, quintis,
ausências, medidas e conservação de contagens. Estado acadêmico permanece no
2º estado, versão descritiva para revisão; somente a Proposta previamente concluída.

## Implementação e validação

Execução em 21/09/2026: 1.027.924 elegíveis, todos incluídos; 709.066 com
município da escola identificado em 5.475 municípios. A referência municipal
n≥30 contém 2.341 municípios e 672.090 candidatos. O rótulo observado
`Centro-oeste` foi padronizado para `Centro-Oeste` e validado contra as cinco
regiões; nenhuma unidade mudou de região.

IDEB/Saeb foram extraídos das colunas de referência 2023 da planilha municipal
de divulgação vintage 2025, rede pública, sem média de escolas. O núcleo inclui
fluxo, distorção e infraestrutura de 2023, PIB per capita 2023 e Censo 2022 com
defasagem explícita. Foram aprovadas 22 verificações independentes em
`data/processed/territorial_2023/validacao.json`. O relatório vigente é
`reports/report/relatorio_descritivo_territorial_enem_2023.pdf`; contém zero
modelos econométricos.
