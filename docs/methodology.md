# Metodologia

## Extensão descritiva temporal — 21/09/2026, decisão 007

O pedido mais recente estende as correlações municipais de 2023 a 2010–2022.
Para manter médias municipais estáveis e o corte n≥30, a extensão usa os
cadastros elegíveis integrais da decisão 004, mantendo suas cinco notas e regras
comparáveis. Esse derivado município da escola × ano não substitui a amostra
operacional de 20 mil por edição. Pearson, Spearman e Pearson ponderado por n
são descrições; não há teste, regressão ou causalidade. Séries anuais, IDEB
bienal e âncoras censitárias permanecem separados, sem interpolação. Detalhes:
[decisão 007](decisions/007-correlacoes-municipais-temporais.md).

## Desenho vigente — 21/09/2026, decisão 006

O usuário aprovou a reconstrução com foco socioeconômico e territorial no
**ENEM 2023**, usando **todos os elegíveis** e **matemática como desfecho
principal**. Não utilizar automaticamente o recorte de 20 mil, a calibração
ou o foco nas cinco provas das versões anteriores. Critérios, pergunta,
estimandos descritivos, fontes e limites estão na
[decisão 006](decisions/006-reconstrucao-enem-2023.md).

A econometria fica para depois da análise descritiva. Não executar modelos,
testes ou inferência nesta entrega. As seções seguintes são histórico; suas
escolhas substituídas não prevalecem sobre esta atualização.

### Execução do desenho vigente

O filtro aprovado resultou em **1.027.924 inscrições elegíveis**, todas incluídas
sem sorteio (π condicional=1; peso=1). O município da escola foi identificado
para 709.066 candidatos, em 5.475 municípios. A análise municipal principal usa
n≥30 e conserva 2.341 municípios e 672.090 candidatos vinculados; n≥20 e n≥50
são sensibilidades.

Foram incorporados IDEB/Saeb municipal público de referência 2023, fluxo,
distorção e infraestrutura escolar de 2023, PIB per capita de 2023 e renda,
população e urbanização do Censo 2022 com defasagem declarada. A junção usa o
município da escola. IDEB não foi reconstruído por média de escolas e IDHM 2010
não integra o núcleo contemporâneo. Resultados e comandos estão em
[analise-territorial-2023.md](analise-territorial-2023.md); o PDF vigente é
[relatorio_descritivo_territorial_enem_2023.pdf](../reports/report/relatorio_descritivo_territorial_enem_2023.pdf).

## Execução descritiva — 20/09/2026, decisão 005

A [decisão 005](decisions/005-relatorio-descritivo.md) registra as regras da
análise já calculada sobre a amostra da decisão 004, sem novo sorteio, exclusão
ou imputação. São 280.000 inscrições (20.000 por edição); as séries cobrem
2010–2023 e o detalhamento gráfico concentra-se em 2023, último ano do escopo.
As cinco notas são analisadas separadamente. Médias, variâncias descritivas,
quantis, proporções e correlações usam pesos de desenho; a calibração externa
é uma sensibilidade no mesmo domínio de raça/sexo conhecidos.

O vínculo municipal usa a escola e o ano exato, preservando todos os casos
na junção à esquerda. PIB per capita e abandono no ensino médio compõem o
núcleo anual; renda censitária, Gini e IDHM-E são examinados somente nos anos
observados. Não há substituição de residência nem transporte entre censos.
Ausências, desconhecimento, códigos inválidos e extremos foram quantificados.
Valores extremos e zeros observados não foram removidos automaticamente.

[Relatório, resultados e reprodução](relatorio-descritivo.md). O Google Docs
recebeu uma aba específica, preservando a proposta original. Esta é uma versão
descritiva para revisão dos autores: o trabalho continua no 2º estado, não
equivale a Relatório Final, nem inclui testes, intervalos inferenciais ou modelos.

## Atualização vigente — 20/09/2026, decisão 004

O pedido de identificar variáveis e construir amostra estratificada substitui
o adiamento de amostragem da decisão 003. O usuário escolheu **concluintes do
ensino médio em cada ano** como população de referência. A operação atual
restringe-se ao ensino regular; EJA não está coberta. A unidade é inscrição ×
edição; município × ano é contexto auxiliar. [Plano completo](amostragem.md) e
[PDF com cálculos e anexos](../reports/report/variaveis_plano_amostral_chang.pdf).

Pergunta operacional: quais características familiares, demográficas e escolares
estão associadas às diferenças de notas entre concluintes declarados elegíveis
do ENEM, e que informação adicional oferece o município da escola quando
identificado? Município da escola não é residência. A pergunta residencial
anterior continua sem identificação, não foi resolvida por uma troca de chave.

Estimando descritivo primário: distribuição e média de cada uma das cinco notas,
separadamente, no cadastro elegível de cada edição. Estimando secundário:
padronização demográfica à proxy PNAD, no domínio de raça/sexo conhecidos;
não é média nacional identificada de todos os concluintes. Contrastes e modelos
associativos específicos precisam de pré-especificação antes de testes.

Hipóteses substantivas: renda e escolaridade parental estão associadas ao
desempenho; diferenças escolares refletem também composição familiar; contexto
territorial pode acrescentar informação. Não são conclusões nem efeitos causais.
Hipóteses estatísticas, nível de significância, poder e correções de multiplicidade
serão definidos para os contrastes concretos; não houve teste nesta entrega.

Elegibilidade: conclusão declarada no ano, ensino regular, não treineiro quando
observável, presença nas quatro áreas, cinco notas numéricas e redação regular
conforme dicionário anual. Ausência de raça/renda/escola não elimina inscrição.
Exclusões estão quantificadas em `data/processed/sampling/fluxo_elegibilidade.csv`.
O filtro de redação/presença seleciona o universo; análise por área menos
restritiva é uma sensibilidade futura, não resultado já produzido.

Amostra operacional executada: 20 mil/ano em 2010–2023, sem reposição, estratos
de região da escola × raça × sexo × renda original; piso 2 ou inclusão certa
se N_h=1. Semente 20260920 + ano. Probabilidade n_h/N_h condicional ao ENEM.
Cenários de proporções: confiança 95%, erros de 1 e 2 pontos percentuais, DEFF
planejado 1; 1,5; 2; 3 e correção finita. DEFF=2 não foi provado; 30 mil/ano é
alternativa mais conservadora para o cenário DEFF=3, não a amostra sorteada.

PNADC anual 2012–2023: ensino médio regular, séries 3/4, peso V1032. Essa proxy
não confirma conclusão; sensibilidade série 3 versus 3/4 calculada. Calibração
externa parcial: raça × sexo e idade; margem interna: região da escola × renda
ENEM. Não calibrar renda familiar por renda domiciliar nem escola por residência.
2010/2011 têm somente pesos de desenho. Não declarados conservam peso de desenho
e não recebem peso externo. A participação voluntária no ENEM impede concluir
representatividade nacional apenas por raking. Os alvos PNAD têm erro amostral.

O trabalho permanece no **2º estado**; **somente a Proposta foi concluída**.

## Histórico preservado — etapa de importação, anterior à decisão 004

O restante deste documento registra o planejamento da importação. Afirmações
abaixo de amostra/população ainda indefinidas descrevem aquele momento e são
substituídas, apenas nesses pontos, pela atualização acima. As limitações de
residência, comparabilidade e inferência continuam aplicáveis.

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
