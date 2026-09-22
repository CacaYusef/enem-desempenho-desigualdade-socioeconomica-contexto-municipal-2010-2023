# Relatório descritivo: execução e escolhas de apresentação

Data: 2026-09-20. Pedido: introdução, coleta/apresentação, análise descritiva e
conclusões, no documento de trabalho Google Docs. Não alterar a amostra da
decisão 004 nem refazer sua seleção. Preservar a proposta e acrescentar uma
aba de relatório. A entrega técnica é uma versão para revisão; não implica
aprovação acadêmica ou conclusão do Relatório Final.

## Universo, medidas e pesos

- Usar as 280 mil inscrições já sorteadas, 20 mil por edição 2010–2023.
  Não são 280 mil pessoas identificadas longitudinalmente. População observada
  é o cadastro elegível definido na decisão 004, não todos os concluintes.
- Descrever cada uma das cinco notas separadamente, por ano. Não produzir média
  geral de provas nem juntar edições em uma distribuição sem significado temporal.
- Principal: peso de desenho. Sensibilidade: desenho e peso calibrado no mesmo
  domínio com calibração disponível, evitando confundir seleção de domínio e peso.
- Média = soma(w*x)/soma(w); variância descritiva = soma(w*(x-média)^2)/soma(w).
  Não é variância do estimador nem estimador não viesado com correção n-1.
  Desvio-padrão é sua raiz. Quantis: inversa da distribuição empírica ponderada,
  menor valor cuja massa acumulada alcança p; nenhum midpoint imputado.
- Correlação de Pearson ponderada em pares quantitativos completos; informar
  n e pesos. Códigos de renda, sexo, raça e escolaridade não são quantitativos.
- Boxplots ponderados usam quartis e cercas Q1−1,5 IQR / Q3+1,5 IQR; extremos
  permanecem. Contagens fora das cercas não implicam erro. Não truncar notas.
- Não executar teste, intervalo de confiança ou regressão nesta etapa; orientar
  a próxima etapa a partir de magnitudes e limitações. Gráficos sem barras de
  erro não são afirmações de precisão inferencial.

## Recortes e qualidade

Séries anuais: cinco notas e comparação por sexo, raça, escola e categorias
originais de questionário, identificadas pelo mapa anual. Detalhamento no texto
e figuras: 2023, última edição do escopo, não escolhida por favorecer resultados.
Tabelas anuais completas ficam disponíveis em CSV. Renda 2023 agrupada, apenas
para apresentação, em A/B até R$1.320; C/D R$1.320,01–2.640; E/F/G/H
R$2.640,01–6.600; I–Q acima de R$6.600. Nunca converter faixas em renda pontual.
São limites do questionário 2023, não salário mínimo constante em todo o ano.

Categorias ausentes/desconhecidas permanecem explícitas. Contar falta bruta,
não declaração e categorias inválidas separadamente. Verificar unicidade
inscrição/ano, somas de pesos, notas finitas/não negativas, redação 0–1000,
domínios categóricos e consistência de localização. Nas provas TRI, não impor
teto de 1000 como impossibilidade universal. Não impute ou exclua extremos.

## Contexto municipal

Junção à esquerda, many-to-one, por CO_MUNICIPIO_ESC × ano e codigo_ibge ×
ano_enem. Nunca residência e nunca local de prova como substituto. Não alterar
os placeholders residenciais da base municipal original. Contabilizar falta de
chave e ausência do indicador separadamente. A análise territorial é do domínio
com escola identificada e sua seleção deve ser comparada com a amostra completa.

Núcleo anual: PIB per capita e abandono no ensino médio. Detalhe censitário:
renda domiciliar e população em 2022; IDHM-E, Gini e renda Atlas em 2010.
Sem transporte censitário, interpolação ou defasagem implícita. Correlações
individuais com contexto repetido por município não provam efeito contextual;
dependência territorial exige tratamento na etapa inferencial. Descrever também
a cobertura e redundância dos indicadores, sem inserir todos num único modelo.

## Rastreabilidade

Derivados em data/processed/descriptive; lógica reutilizável em src; testes de
medidas com resultados conhecidos. Fontes e hashes de entrada em manifesto.
Tabelas de frequência contêm n bruto e proporção ponderada, com denominador.
Nenhum dado individual será publicado no Google Docs, apenas agregados/gráficos.
