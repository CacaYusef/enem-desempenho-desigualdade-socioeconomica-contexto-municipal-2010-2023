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

> Quais características socioeconômicas individuais e familiares e quais
> características do contexto municipal estão associadas às diferenças de
> desempenho entre participantes concluintes do Ensino Médio no ENEM de 2010 a
> 2023, e como essas associações variam entre territórios e ao longo do tempo?

A pergunta é associativa, não causal. Antes da inferência ainda é obrigatório
definir o estimando: desfecho exato, exposição, contraste, população, escala e
horizonte temporal. “Mecanismo” será usado apenas como hipótese teórica, não como
efeito causal identificado.

## População, amostra e desenho

O relatório propõe participantes do ENEM entre 2010 e 2023, com prioridade para
quem esteja concluindo o Ensino Médio regular no ano da prova. A unidade de
observação preliminar é a combinação participante–edição. A reunião dos anos
forma cortes transversais repetidos, não um painel de indivíduos.

O relatório também propõe excluir treineiros e pessoas que concluíram o Ensino
Médio anteriormente, além de exigir presença e notas válidas. Essas regras só
serão adotadas após confirmar que as variáveis possuem definições comparáveis em
cada ano. Ausência de covariáveis não implicará exclusão automática: mecanismo,
extensão e alternativas de tratamento serão avaliados primeiro.

Permanecem pendentes:

- definição precisa das populações-alvo e observada;
- áreas/notas incluídas e exigência de presença por prova;
- códigos anuais de conclusão, modalidade de ensino e treineiro;
- município associado ao contexto: escola, residência se disponível, ou prova;
- tratamento de inscrições sem município de escola;
- estrutura hierárquica, temporal e espacial relevante;
- alcance e limites de generalização.

## Dados disponíveis

Na inicialização foi localizado o pacote oficial de microdados do ENEM 2023,
incluindo dados de participantes, itens, dicionário e documentos técnicos. Não
foram localizados microdados de 2010–2022 nem bases de contexto municipal.

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

Os indicadores municipais candidatos incluem IDHM, IDHM-Educação, renda per
capita, IDEB e IQM/IQIM, condicionados à disponibilidade, definição, cobertura e
compatibilidade temporal. Fonte, unidade, ano de referência, deflação, chave e
regra de correspondência com o participante ainda estão pendentes.

## Plano analítico

O relatório organiza a investigação em três eixos:

1. condições individuais, familiares, econômicas e sociais;
2. fatores demográficos, territoriais e institucionais dos municípios;
3. persistência temporal e heterogeneidade territorial das desigualdades.

Antes de selecionar um modelo, o trabalho deverá:

1. obter e inventariar todas as edições e fontes municipais;
2. construir uma matriz de equivalência das variáveis por ano;
3. validar regras de ingestão e a unidade de observação;
4. formalizar o estimando e congelar critérios da amostra;
5. documentar o fluxograma de inclusões e exclusões;
6. avaliar ausências, extremos, distribuição, seleção e qualidade;
7. produzir descrições por ano, região e grupos socioeconômicos;
8. avaliar modelos compatíveis com a dependência município–ano e comparar
   especificações individuais e contextuais;
9. verificar premissas, intervalos, tamanhos de efeito e multiplicidade;
10. realizar sensibilidades a população, vínculo municipal, desfecho e
    especificação.

Não há método estatístico final selecionado nesta etapa. A escolha entre modelos
multinível, efeitos fixos, erros agrupados ou outras alternativas dependerá do
estimando e da estrutura efetivamente observada.

## Premissas e limitações atuais

- A cobertura temporal observada é somente 2023, não 2010–2023.
- Ainda não há dados de contexto municipal no repositório.
- Participantes do ENEM não constituem automaticamente uma amostra
  representativa de todos os estudantes ou jovens brasileiros.
- Relações observacionais não sustentam causalidade sem desenho e premissas
  adicionais explícitos.
- Comparabilidade de variáveis, questionários e provas ao longo dos anos ainda
  precisa ser avaliada na documentação de cada edição.
- O município de prova pode não representar o município da trajetória escolar;
  o vínculo territorial é uma fonte potencial de erro de mensuração.
- A participação no ENEM e as regras de elegibilidade mudam ao longo do tempo,
  podendo alterar a composição dos cortes transversais.

Atualize este documento e registre decisões materiais em `docs/decisions/`
antes de produzir resultados inferenciais.
