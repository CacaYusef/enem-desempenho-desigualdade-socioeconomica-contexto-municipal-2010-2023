# Desigualdade socioeconômica, contexto municipal e desempenho no ENEM

## Versão de trabalho da tese

**Instituição:** Universidade de São Paulo — Faculdade de Economia,
Administração e Contabilidade  
**Curso:** Ciências Econômicas  
**Autores indicados no documento-base:** Caio Luca da Silva e Nathan Henrique de
Souza Fonseca  
**Período pretendido:** 2010–2023  
**Estado do trabalho:** 2º estado — Relatório Descritivo em elaboração  
**Única etapa concluída:** Proposta  
**Ainda não concluídos:** Relatório Descritivo, Relatório Final e Apresentação

## Aviso sobre o andamento

O trabalho encontra-se atualmente no **2º estado**, correspondente à elaboração
do **Relatório Descritivo**. Até o momento, **somente a Proposta foi concluída**.
Este arquivo é uma estrutura de trabalho construída a partir dessa proposta e
não deve ser apresentado como tese, relatório descritivo ou relatório final já
concluído.

Ainda não foram concluídos:

- a preparação e validação da base analítica;
- a análise descritiva;
- a análise inferencial;
- o Relatório Descritivo;
- o Relatório Final;
- a Apresentação.

> Nota de proveniência: este texto foi estruturado a partir do relatório
> acadêmico fornecido como `Chang (2).pdf`. O relatório funciona como fonte do
> tema, da motivação, dos objetivos e das expectativas. O documento corresponde à
> Proposta, única etapa concluída até agora. Ele não contém resultados estatísticos
> concluídos nem referências bibliográficas completas. Nenhum número ou achado
> empírico foi inventado nesta versão.

## Resumo

Esta pesquisa investiga as associações entre condições socioeconômicas,
características do contexto municipal e desempenho de participantes do Exame
Nacional do Ensino Médio (ENEM) entre 2010 e 2023. O estudo pretende combinar
informações individuais e familiares dos microdados do exame com indicadores
econômicos, sociais, educacionais e institucionais dos municípios. A análise será
estruturada, conforme a instrução atualizada, por município × ano do ENEM,
mantendo inscrição × edição como unidade dos microdados brutos. Serão examinadas
diferenças entre grupos socioeconômicos, municípios, unidades da Federação,
regiões e anos. Dado o caráter observacional do desenho, os resultados serão
interpretados como associações estatísticas, e não como efeitos causais. Nesta
versão, os pacotes ENEM 2010–2023 e fontes municipais estão locais; a
harmonização semântica, o vínculo residencial, o estimando, a amostra e todos os
parâmetros estatísticos permanecem pendentes. A importação técnica não conclui
o Relatório Descritivo.

**Palavras-chave:** ENEM; desigualdade educacional; condição socioeconômica;
contexto municipal; heterogeneidade territorial; cortes transversais repetidos.

## 1. Introdução

A educação ocupa posição central nas discussões sobre desenvolvimento econômico
e social. Na tradição do capital humano, a escolarização é analisada como
investimento capaz de se relacionar à produtividade e aos rendimentos. Essa
perspectiva, embora relevante, não esgota o fenômeno educacional: o acesso à
escola, as condições de aprendizagem e a conversão da escolaridade em
oportunidades dependem também de estruturas familiares, sociais, territoriais e
institucionais.

Outras vertentes enfatizam que sistemas educacionais podem reproduzir
desigualdades preexistentes e que educação deve ser entendida não apenas por seus
retornos produtivos, mas também por sua contribuição à expansão de capacidades e
liberdades. No Brasil, essas questões se articulam à formação histórica do
sistema educacional, às diferenças regionais e às desigualdades de renda, raça,
trajetória escolar e acesso a serviços públicos.

A ampliação da escolarização e do acesso ao Ensino Superior não implica, por si
só, homogeneidade de aprendizagem. Diferenças de desempenho continuam associadas
às condições econômicas e culturais das famílias, ao tipo de escola e às
características dos territórios. O ENEM oferece uma oportunidade de estudar uma
manifestação observável dessas desigualdades por reunir notas, informações
cadastrais e respostas contextuais de participantes distribuídos pelo país.

Ao mesmo tempo, o exame impõe limites importantes. Seus participantes não são
automaticamente representativos de todos os estudantes brasileiros; a composição
de quem realiza a prova varia entre anos; e o município de aplicação pode não
corresponder ao município da trajetória escolar. Esses limites precisam fazer
parte do desenho, da análise e da interpretação.

## 2. Problema e pergunta de pesquisa

O problema substantivo é compreender como desigualdades individuais, familiares
e territoriais se manifestam nas diferenças de desempenho no ENEM. O relatório
de origem formula essa preocupação em termos dos mecanismos socioeconômicos que
ajudariam a explicar essas diferenças.

Como o desenho proposto é observacional, a pergunta operacional desta tese é:

> Quais características econômicas, sociais, demográficas e educacionais dos
> municípios estão associadas às características e ao desempenho dos
> participantes do ENEM residentes nesses municípios, no escopo 2010–2023?

A pergunta foi atualizada pela instrução municipal do usuário (decisão 003).
Sua operacionalização depende de identificar residência com segurança; escola
e aplicação de prova não serão tratadas como residência.

Essa formulação não identifica causalidade. O termo “mecanismo” será reservado à
discussão teórica ou a hipóteses que exigiriam desenhos adicionais para serem
testadas causalmente.

## 3. Objetivos

### 3.1 Objetivo geral

Analisar a relação entre condições socioeconômicas individuais e familiares,
características dos municípios e diferenças de desempenho entre participantes do
ENEM no período de 2010 a 2023.

### 3.2 Objetivos específicos

1. Descrever a distribuição do desempenho por edição, região e grupos
   socioeconômicos comparáveis.
2. Estimar associações entre renda familiar, escolaridade dos pais, tipo de
   escola e demais características individuais e as notas do exame.
3. Examinar se indicadores municipais de desenvolvimento, renda, educação e
   capacidade institucional acrescentam informação às características
   individuais e familiares.
4. Investigar heterogeneidade das associações entre regiões, unidades da
   Federação, municípios e grupos socioeconômicos.
5. Avaliar a estabilidade ou a mudança dessas desigualdades ao longo das edições.
6. Verificar a sensibilidade dos resultados a critérios de população, ausências,
   vínculo territorial, desfecho e especificação estatística.

## 4. Referencial teórico preliminar

### 4.1 Educação e capital humano

A literatura de capital humano fornece uma primeira justificativa para estudar a
relação entre escolaridade, produtividade e rendimentos. No entanto, resultados
educacionais não decorrem apenas de decisões individuais de investimento. A
disponibilidade de recursos, a qualidade das instituições e as oportunidades
acumuladas ao longo da trajetória escolar condicionam tanto a aprendizagem
quanto seus retornos.

### 4.2 Reprodução das desigualdades e capacidades

A educação também pode refletir e reproduzir diferenças de classe e de capital
cultural. Famílias com maior disponibilidade de recursos financeiros e não
financeiros podem oferecer condições de estudo, informação e acompanhamento
distintas. Em uma perspectiva de capacidades, a educação integra o conjunto de
oportunidades efetivamente acessíveis às pessoas e não deve ser reduzida a seus
retornos monetários.

### 4.3 Desigualdades educacionais no Brasil

No contexto brasileiro, desigualdades familiares se combinam a diferenças na
oferta, no financiamento, na gestão e na qualidade dos sistemas de ensino. A
distribuição territorial dessas condições é historicamente desigual. Por isso,
uma análise exclusivamente individual pode omitir dimensões relevantes do
ambiente em que as trajetórias escolares se desenvolvem.

### 4.4 Contexto municipal e heterogeneidade territorial

Indicadores municipais podem representar dimensões econômicas, educacionais e
institucionais que não aparecem diretamente no questionário do participante. A
comparação entre modelos individuais e contextuais poderá mostrar se essas
dimensões estão associadas ao nível médio de desempenho ou à magnitude das
desigualdades socioeconômicas. Isso não significa, por si só, que o município
cause as diferenças observadas.

## 5. Expectativas empíricas

As proposições abaixo são expectativas do relatório-base, não resultados:

1. Participantes de famílias com maior renda e escolaridade parental tenderão a
   apresentar, em média, notas superiores.
2. Participantes associados a municípios com melhores condições econômicas,
   sociais, educacionais e institucionais tenderão a apresentar maior desempenho,
   mesmo após considerar características individuais observadas.
3. O nível de desempenho e a magnitude das desigualdades socioeconômicas não
   serão homogêneos entre territórios.
4. Especificações que combinem características individuais e municipais poderão
   ter maior capacidade explicativa que especificações apenas individuais.
5. A força e a forma dessas associações poderão mudar entre 2010 e 2023.

Cada expectativa deverá ser convertida em hipótese estatística somente após a
definição do estimando, da escala e da família de modelos. Resultados contrários
às expectativas serão reportados com a mesma transparência.

## 6. Desenho do estudo

### 6.1 População e unidade de observação

A unidade principal pretendida é município × ano do ENEM. Os arquivos brutos
permanecem em inscrição × edição, sem presumir acompanhamento longitudinal das
mesmas pessoas. População, critérios de inclusão, tamanho da amostra e parâmetros
estatísticos serão decididos posteriormente.

A prioridade para concluintes e as exclusões sugeridas na proposta são histórico,
não regras vigentes. Nenhum filtro de conclusão, treineiro, presença, nota ou
covariável ausente foi aplicado na importação. O intervalo adquirido não fixa
os anos nem municípios da futura amostra.

### 6.2 Fontes de dados

As fontes planejadas são:

- microdados e dicionários do ENEM para cada edição de 2010 a 2023;
- indicadores municipais de desenvolvimento humano e educação;
- renda municipal ou domiciliar per capita com referência temporal explícita;
- IDEB e medidas de rendimento/qualidade educacional compatíveis;
- indicadores de gestão ou capacidade institucional, como IQM/IQIM, se sua
  definição e cobertura forem adequadas.

Estão locais os pacotes ENEM 2010–2023 e fontes municipais IBGE, INEP e Ipeadata.
Os indicadores de rendimento escolar foram importados; IDEB e IQM/IQIM não
foram incluídos nesta etapa. Fontes, cobertura e limitações constam em
`docs/importacao.md` e `reports/data-quality.md`. Não há resultados analíticos
concluídos por essa aquisição.

### 6.3 Desfechos

Os desfechos candidatos são as notas de Ciências da Natureza, Ciências Humanas,
Linguagens, Matemática e Redação. A análise separada ou a construção de uma
medida composta permanece em aberto. Comparabilidade entre edições e diferenças
de escala devem ser examinadas antes de qualquer combinação.

### 6.4 Características individuais e familiares

As variáveis candidatas incluem renda familiar, escolaridade dos pais, sexo,
raça/cor, idade, tipo de escola e outras respostas socioeconômicas comparáveis.
As categorias serão obtidas dos dicionários oficiais de cada edição. Nenhum
código será interpretado apenas pelo nome da coluna.

### 6.5 Contexto municipal

O catálogo importado contém candidatos demográficos, econômicos, sociais e
educacionais, com dicionário por indicador–ano. Nenhum foi automaticamente
selecionado para modelo. IDHM é um índice composto; PIB per capita não é renda
domiciliar. Indicadores censitários permanecem nos respectivos anos, sem
interpolação; CEMPRE tem séries separadas antes e a partir de 2022.

O vínculo requerido é residência. O painel contextual e a correspondência por
código de escola/prova não concluem esse vínculo. As estatísticas municipais
do ENEM permanecem ausentes e não serão calculadas com localização substituta.

## 7. Estratégia analítica preliminar

### 7.1 Ingestão e harmonização

Foi construída uma matriz de disponibilidade; a equivalência semântica das
variáveis por ano permanece pendente. Cada transformação deve partir de
`data/raw/`, gerar novo produto em
`data/processed/` e registrar contagens, tipos, filtros e alterações de códigos.

### 7.2 Auditoria e descrição

Antes da inferência serão avaliados volume, duplicidades, ausências, valores
impossíveis, extremos, distribuição das notas, composição da população e
consistência entre presença, situação escolar e notas. Estatísticas e gráficos
serão apresentados por edição e pelos grupos definidos no plano.

### 7.3 Estimação

O método final ainda não foi escolhido. A estrutura esperada — participantes
agrupados em combinações município–ano e possíveis padrões regionais — exige
avaliar dependência entre observações. Modelos multinível, efeitos fixos, erros
agrupados ou outras especificações são alternativas a comparar somente depois da
definição do estimando e da inspeção da estrutura dos dados.

A análise deverá reportar estimativas, intervalos de confiança, tamanhos de
efeito e diagnósticos. Comparações entre especificações individuais e contextuais
não serão reduzidas ao R² e não serão interpretadas como prova de causalidade.

### 7.4 Robustez e sensibilidade

Serão consideradas, conforme a pergunta final:

- populações alternativas justificadas após a definição da amostra;
- diferentes exigências de presença e notas válidas;
- tratamento de ausências e análise de casos completos;
- notas por área versus eventual medida composta justificada;
- viabilidade do vínculo residencial, sem substituição automática por escola/prova;
- indicadores municipais e defasagens temporais alternativas;
- formas funcionais, interações territoriais e especificações de dependência;
- efeitos da mudança de composição dos participantes entre edições.

## 8. Limitações previstas

1. **Seleção para o exame:** participantes do ENEM não representam
   automaticamente todos os estudantes ou jovens brasileiros.
2. **Mudanças temporais:** regras do exame, adesão, questionários e composição da
   população podem variar entre edições.
3. **Mensuração socioeconômica:** respostas são categóricas e autodeclaradas, e
   sua formulação pode mudar.
4. **Vínculo territorial:** município de prova pode não representar residência ou
   trajetória escolar; município da escola pode estar ausente.
5. **Confundimento:** associações podem refletir características não observadas,
   seleção e causalidade reversa.
6. **Comparabilidade das notas:** diferenças entre edições devem ser avaliadas à
   luz da documentação técnica do exame.
7. **Disponibilidade atual:** há ENEM 2010–2023 e fontes municipais, mas nem todos
   os indicadores têm cobertura anual. A integração residencial segue pendente.
8. **Agregação:** uma média municipal não caracteriza individualmente cada
   candidato; associações municipais não implicam associações individuais.

## 9. Estrutura prevista dos capítulos

1. Introdução, problema e contribuições esperadas.
2. Referencial teórico e evidência empírica anterior.
3. Fontes de dados, população e harmonização temporal.
4. Estratégia empírica, estimando e diagnósticos.
5. Resultados descritivos.
6. Resultados inferenciais e análises de sensibilidade.
7. Discussão, limitações e conclusão.

Os capítulos 5 a 7 não serão preenchidos com números antes que o pipeline seja
executado, validado e documentado.

## 10. Informações pendentes para a próxima versão

- referências bibliográficas completas do relatório-base;
- orientação, modalidade acadêmica e normas formais da instituição;
- revisão substantiva da qualidade e comparabilidade das fontes importadas;
- seleção justificada de indicadores e conferência das condições de uso;
- dicionário harmonizado de variáveis;
- regra de vínculo entre participante e município;
- desfecho, exposição, contraste e estimando;
- critérios finais de população e tratamento de ausências;
- modelo estatístico e plano de múltiplas comparações;
- resultados, tabelas, figuras, discussão e conclusão.

## Referências citadas no documento-base — dados bibliográficos a completar

O PDF menciona as fontes abaixo apenas por autor e ano, sem lista bibliográfica
completa. Para não inventar títulos, periódicos ou editoras, esses dados deverão
ser verificados antes da submissão:

- Barros et al. (2001).
- Becker (1964).
- Bourdieu e Passeron (1977).
- Brasil (2023), relatório relacionado ao PISA 2022.
- Coleman et al. (1966).
- Curi e Menezes-Filho (2009).
- Diaz (2012).
- Ernica, Rodrigues e Soares (2025).
- IBGE (2024).
- Komatsu et al. (2019).
- Menezes-Filho e Amaral (2009).
- Mincer (1974).
- Oliveira, Menezes-Filho e Komatsu (2018).
- Schultz (1961).
- Sen (1999).
- Teixeira (1994).
- Veloso (2011).
