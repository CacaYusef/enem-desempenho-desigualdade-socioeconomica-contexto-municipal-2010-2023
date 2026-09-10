# Metodologia

Status acadêmico: **2º estado — Relatório Descritivo em elaboração**. Somente a
**Proposta** foi concluída. O Relatório Descritivo, o Relatório Final e a
Apresentação ainda não foram concluídos.

Este rascunho metodológico foi baseado na proposta fornecida em `Chang (2).pdf`
e atualizado à luz do cronograma descrito em
`Orientação sobre o trabalho de estatística-2026.pdf` (2026-09-09).

## Pergunta de pesquisa

O relatório pergunta quais mecanismos socioeconômicos ajudam a explicar as
diferenças de desempenho entre participantes do ENEM. Para manter a linguagem
proporcional ao desenho observacional proposto, a pergunta operacional
preliminar será:

> Quais características econômicas, sociais, demográficas e educacionais dos
> municípios estão associadas às características e ao desempenho dos
> participantes do ENEM residentes nesses municípios, no escopo 2010–2023?

Essa é a intenção substantiva indicada na instrução municipal mais recente,
não uma pergunta já viabilizada pelos dados. A disponibilidade de residência
precisa ser resolvida antes da operacionalização. A unidade principal pretendida
é **município × ano do ENEM**, conforme a decisão 003.

A pergunta é associativa, não causal. Antes da inferência ainda é obrigatório
definir o estimando: desfecho exato, exposição, contraste, população, escala e
horizonte temporal. “Mecanismo” será usado apenas como hipótese teórica, não como
efeito causal identificado.

## População, amostra e desenho

**Tamanho da amostra, parâmetros estatísticos e critérios de inclusão não estão
definidos.** O escopo de aquisição é 2010–2023 e não equivale à seleção final
dos anos, municípios ou participantes para análise.

Os arquivos ENEM têm registros de inscrição × edição. Foram preservados todos
os registros e campos, sem filtro de treineiro, conclusão, presença ou nota.
As sugestões da proposta original sobre concluintes e exclusões são apenas
histórico (decisão 002); não foram adotadas como critérios. A decisão 003
atualiza a unidade principal pretendida para município × ano. Não se presume
acompanhamento longitudinal dos mesmos indivíduos.

Permanecem pendentes:

- definição precisa das populações-alvo e observada;
- áreas/notas incluídas e exigência de presença por prova;
- códigos anuais de conclusão, modalidade de ensino e treineiro;
- obtenção de vínculo residencial seguro ou revisão expressa da pergunta;
- tratamento de inscrições sem localização adequada à pergunta;
- estrutura hierárquica, temporal e espacial relevante;
- alcance e limites de generalização.

## Dados disponíveis

Na inicialização havia somente o pacote ENEM 2023. Foram acrescentados os ZIPs
oficiais INEP 2010–2022 e as fontes municipais IBGE, INEP e Ipeadata. A aquisição
2023 é preexistente, sem data/URL exatas conhecidas; não foi substituída.
Inventários anuais, hashes, URLs e dicionários estão em `docs/sources/`.

O CSV de participantes de 2023 usa `;`, tem 76 colunas e está em Windows-1252.
Essas propriedades devem ser declaradas explicitamente na ingestão.

## Variáveis

Os desfechos candidatos do relatório são as notas nas áreas do ENEM e na
redação. Ainda não foi decidido se serão analisadas separadamente ou por alguma
medida composta; nenhuma média será criada sem justificativa de comparabilidade.

As características individuais candidatas incluem renda familiar, escolaridade
dos pais — com atenção à escolaridade materna —, sexo, raça/cor, idade e tipo de
escola. Os códigos e a comparabilidade anual devem ser validados nos dicionários
oficiais antes de qualquer harmonização.

Foram importados candidatos de população, PIB, renda, escolaridade,
alfabetização, emprego, pobreza, desigualdade, saneamento, internet, urbanização,
IDHM e rendimento escolar. O dicionário municipal registra fonte, URL, ano,
unidade, universo e limitações. Sua presença no catálogo não os seleciona para
modelo. IDEB e IQM/IQIM, citados na proposta, não foram importados nesta etapa.

O painel contextual usa a referência município–ano do PIB oficial: 5.565
unidades em 2010–2012 e 5.570 em 2013–2023. Essa referência operacional não é a
amostra; observações de outras fontes sem correspondência ficam preservadas em
arquivo separado e na base longa. O cadastro territorial corrente não é
retroagido para preencher anos anteriores.

No painel de importação, `ano_dado = ano_enem` e `defasagem_anos = 0`; isso
registra coincidência exata, não escolhe uma defasagem para modelo. Dados
censitários não são repetidos em anos sem observação. Valores monetários mantêm
os preços/unidades da fonte; deflator e ano-base continuam pendentes. A série
CEMPRE anterior a 2022 permanece separada da nova série.

## Plano analítico

O relatório organiza a investigação em três eixos:

1. condições individuais, familiares, econômicas e sociais;
2. fatores demográficos, territoriais e institucionais dos municípios;
3. persistência temporal e heterogeneidade territorial das desigualdades.

Antes de selecionar um modelo, o trabalho deverá:

1. revisar os inventários e auditorias das fontes importadas;
2. complementar a matriz de disponibilidade com equivalência semântica por ano;
3. validar regras de ingestão e a unidade de observação;
4. formalizar o estimando e congelar critérios da amostra;
5. documentar o fluxograma de inclusões e exclusões;
6. avaliar ausências, extremos, distribuição, seleção e qualidade;
7. produzir descrições somente após definir universo e agregação territorial;
8. avaliar modelos compatíveis com a dependência município–ano e comparar
   especificações individuais e contextuais;
9. verificar premissas, intervalos, tamanhos de efeito e multiplicidade;
10. realizar sensibilidades a população, vínculo municipal, desfecho e
    especificação.

Não há método estatístico final selecionado nesta etapa. A escolha entre modelos
multinível, efeitos fixos, erros agrupados ou outras alternativas dependerá do
estimando e da estrutura efetivamente observada.

## Premissas e limitações atuais

- A disponibilidade temporal dos indicadores municipais não é uniforme; o
  intervalo 2010–2023 não significa que cada indicador existe em cada ano.
- A junção residencial e as estatísticas ENEM municipais permanecem pendentes.
  Código de escola/prova válido não identifica residência. Nenhuma média,
  mediana, desvio-padrão, percentil ou corte municipal do ENEM foi calculado.
- Participantes do ENEM não constituem automaticamente uma amostra
  representativa de todos os estudantes ou jovens brasileiros.
- Relações observacionais não sustentam causalidade sem desenho e premissas
  adicionais explícitos.
- Comparabilidade de variáveis, questionários e provas ao longo dos anos ainda
  precisa ser avaliada na documentação de cada edição.
- Município de escola ou prova não será tratado como residência. Uma mudança
  de pergunta territorial exige decisão explícita, não uma substituição técnica.
- Estatísticas agregadas municipais não descrevem cada candidato individualmente
  e não sustentam inferências individuais por si sós (risco de falácia ecológica).
- A participação no ENEM e as regras de elegibilidade mudam ao longo do tempo,
  podendo alterar a composição dos cortes transversais.

Atualize este documento e registre decisões materiais em `docs/decisions/`
antes de produzir resultados inferenciais.
