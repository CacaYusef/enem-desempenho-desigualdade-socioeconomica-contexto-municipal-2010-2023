# Importação das fontes e contexto município–ano

Status: aceito — 2026-09-09, por solicitação do usuário.

## Escopo autorizado

Importar os microdados oficiais do ENEM 2010–2022 e aproveitar o pacote 2023
existente. Construir a base contextual municipal conforme a instrução anexada
`f4676ede-5e56-446d-97a2-ebe5f88ecdbc/pasted-text.txt`.

A unidade principal pretendida passa a ser município × ano do ENEM. A unidade
dos arquivos brutos continua inscrição × edição. Esta decisão atualiza a unidade
principal preliminar da decisão 002, sem apagar aquele registro.

## Decisões de ingestão

- Preservar integralmente as edições anuais, sem amostragem, filtros de
  elegibilidade, exclusão de ausentes ou remoção de outliers.
- Não definir tamanho da amostra, parâmetros estatísticos, percentis, pontos de
  corte, modelo, covariáveis finais, medida composta de notas ou defasagens.
- Os indicadores importados são candidatos para avaliação de disponibilidade e
  qualidade; sua aquisição não os seleciona para um modelo.
- Manter ZIPs e respostas das APIs oficiais em `data/raw/`, hashes e metadados em
  `docs/sources/manifests/` e derivados em `data/processed/`.
- Preservar a localização atual no projeto, autorizada para escrita. Não mover
  dados para outro diretório ou alterar a sincronização do OneDrive nesta tarefa.
- Consultar indicadores municipais por código IBGE; registrar categorias, unidade,
  ano do dado, ano do ENEM e defasagem. No painel contextual inicial, somente
  coincidência exata de ano; indicadores censitários ficam nos anos censitários.
- Não usar município de escola ou prova como residência. Inventariar cada
  significado geográfico separadamente. Se residência não existir, deixar
  pendente a integração substantiva entre residentes e contexto municipal.
- Conservar os valores monetários nas unidades e preços divulgados. A escolha do
  deflator e ano-base será posterior, conforme a orientação de não fixar parâmetros.
- Não produzir testes, inferência ou estimativas da futura amostra nesta etapa.

## Limites

O catálogo temporal 2010–2023 é escopo de aquisição, não seleção definitiva dos
anos ou participantes da amostra. As estatísticas de inventário descrevem os
arquivos importados e não constituem resultados da pesquisa.

A aprovação das fontes ocorreu após sua apresentação na conversa. IBGE e INEP
são as fontes principais; Ipeadata pode complementar indicadores censitários
municipais com documentação. Saúde e finanças são módulos condicionais no texto
recebido, portanto dependem de justificativa substantiva posterior.

O estudo permanece no **2º estado — Relatório Descritivo em elaboração**.
**Somente a Proposta foi concluída.** A importação não conclui a etapa acadêmica.
