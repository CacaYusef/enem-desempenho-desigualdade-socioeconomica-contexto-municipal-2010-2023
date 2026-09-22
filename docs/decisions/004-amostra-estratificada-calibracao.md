# Amostra estratificada e calibração externa: plano operacional

Data: 2026-09-20. Escopo autorizado pelo pedido de amostragem e PDF; o usuário
escolheu explicitamente concluintes do ensino médio em cada ano como referência.

## Atualização das decisões anteriores

A decisão 003 adiava amostra e parâmetros durante a importação. O novo pedido
autoriza seu planejamento e a construção de uma amostra estratificada. Para
esta entrega, a unidade é inscrição × edição, compatível com comparar candidatos
e com Chang (2), p. 5. O painel município–ano continua como contexto auxiliar.
A inferência desejada é associativa; não foi definido estimando causal nem
declarado que qualquer variável é um determinante comprovado.

## Escolhas operacionais deste desenho

- Manter os anos 2010–2023 separados. Adotar confiança de 95% e calcular margens
  de 1 e 2 pontos percentuais para proporções, com DEFF de planejamento 1, 1,5,
  2 e 3. DEFF=2 é uma reserva de planejamento, não um efeito conhecido.
- Construir 20.000 observações por edição, 280.000 no conjunto, se cada
  cadastro elegível comportar esse número. Verificar a dispersão dos pesos e
  distinguir essa meta operacional de poder para interações ou grupos raros.
- Cadastro elegível: conclusão declarada no ano, ensino regular, não treineiro
  quando o campo existir, presença nas quatro provas, cinco notas numéricas e
  redação com situação regular segundo cada dicionário anual. Quantificar cada
  exclusão em fluxo; os brutos e os Parquets integrais permanecem intactos.
- A situação regular da redação é P em 2010–2012, 7 em 2013–2014 e 1 desde
  2015, conforme rótulos oficiais. A restrição pode selecionar desempenho e
  deverá ser contrastada posteriormente com análises por área sem esse filtro.
- Estratos: ano × região da escola × raça/cor × sexo × categoria original de
  renda familiar. Escola ausente e raça não declarada permanecem identificadas.
  Alocação proporcional com piso de duas unidades por célula ocupada, ou censo
  se houver uma; piso serve ao desenho, não garante precisão de cada célula.
- Sorteio sem reposição em cada estrato, usando numpy default_rng e seed
  20260920 + ano. Probabilidade condicional pi_h=n_h/N_h; peso de desenho=1/pi_h.
- O tipo de escola é harmonizado pelo rótulo anual, não por código fixo.
  Sua inclusão como explicativa é justificada; não se impõe margem PNAD onde
  cobertura ou definição divergem. A renda original não é recodificada como
  valor pontual nem equiparada automaticamente à renda domiciliar.

## Referência externa e limites de identificação

A PNAD Contínua começa em 2012. Para 2012–2023, adquirir microdados anuais de
primeira visita, usando quinta visita em 2020–2022 conforme orientação da série
de rendimentos do IBGE. Usar pesos oficiais anuais V1032. Estimar proporções e
cruzamentos sobre alunos de ensino médio regular nas séries 3/4. Esse grupo é
**proxy de potenciais concluintes**, não observação de diplomas ou previsão
individual de conclusão. Há cursos de duração diferente e matrículas observadas
em diferentes trimestres. A sensibilidade a série 3 versus 3/4 é documentada.
Não usar Censo de toda a população como margem dos concluintes. Não extrapolar
retroativamente PNADC 2012 para 2010/2011.

O ENEM local não disponibiliza residência, e renda familiar em faixas não é
exatamente a renda domiciliar efetiva PNAD. Logo, não se pode preservar a
distribuição populacional conjunta residência × raça × renda × sexo com as
fontes disponíveis. A PNAD permite examinar a tabela conjunta, mas células
amostrais pequenas ou vazias não equivalem a zeros populacionais.

Gerar pesos externos **experimentais e parciais** para 2012–2023: raking para
raça × sexo e idade ampla da proxy PNAD, preservando simultaneamente região da
escola × renda da população elegível ENEM como margem interna. Não calibrar a
região da escola por região de residência. A escala dos pesos externos é o
tamanho do domínio ENEM com raça/sexo conhecidos, não o total nacional PNAD.
Casos não declarados permanecem na amostra com peso de desenho e peso externo
ausente; quantificar o domínio excluído da calibração. Pesos 2010/2011 são
somente de desenho, até obter referência compatível própria.

Raking não garante tabelas conjuntas não impostas. Não aplicar trimming
silencioso; registrar convergência, resíduos, extremos, fatores de calibração
e tamanho efetivo de Kish. Kish é diagnóstico de dispersão, não DEFF completo
para toda estatística. A incerteza PNAD e a participação não probabilística no
ENEM impedem interpretar o intervalo da subamostra como cobertura garantida
para todos os concluintes brasileiros.

## Entrega e estado acadêmico

Entregar PDF, mapas de variáveis, referências oficiais, alocações N_h/n_h/pi_h,
pesos individuais, cenários, fluxo de elegibilidade e diagnóstico das células.
Nenhum teste de associação ou efeito causal está concluído por essa tarefa.
O trabalho permanece no 2º estado; somente a Proposta acadêmica foi concluída.

## Diagnósticos após execução

As 14 amostras têm 20 mil inscrições cada; calibração parcial convergiu nos
12 anos elegíveis. Em 2021, Kish≈2,10 supera a reserva D=2: não garantir 1 pp
para o resultado calibrado. Cenário mais conservador D=3 sugere 30 mil/ano,
não executado nesta entrega. A escolha original de 20 mil foi preservada e
apresentada como plano operacional condicional, não tamanho ideal universal.

A variância das margens PNAD 2023 não foi publicada: estrato de UPA única com
contribuição não nula impede estimá-la pelo procedimento Taylor adotado. EP/CV
ausentes são explicitados no relatório, sem ajuste ou zero arbitrário.
