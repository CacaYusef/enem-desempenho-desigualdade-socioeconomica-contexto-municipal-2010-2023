# Variáveis e plano amostral — entrega de 20/09/2026

O [PDF de 18 páginas](../reports/report/variaveis_plano_amostral_chang.pdf)
contém escolhas, cálculos reais, referências e seis anexos CSV com todos os
estratos, margens, cenários, exclusões e mapeamento anual. Alguns leitores de
PDF no navegador não exibem anexos: os mesmos arquivos estão em
`data/processed/sampling/`. Estado acadêmico: 2º estado, somente Proposta concluída.

## Resultado e limites

- 280.000 inscrições: 20.000 em cada edição 2010–2023.
- Sorteio sem reposição em estratos conjuntos de região **da escola**, raça,
  sexo e categoria anual original de renda familiar; ano também estratifica.
- Alocação proporcional com piso 2 ou censo de estrato unitário. Piso não
  garante precisão para minorias/interações. Tabela completa tem N_h e n_h.
- `pi_h = n_h/N_h`; `peso_desenho = N_h/n_h`. São probabilidades condicionais
  ao cadastro ENEM elegível, não probabilidades nacionais de fazer o exame.
- `peso_calibrado_proxy`: raking experimental 2012–2023 para raça × sexo e
  idade ampla da PNAD, preservando região da escola × renda ENEM internamente.
  Não inclui margem geográfica/renda externa incompatível. Não declarado
  mantém peso de desenho e peso externo ausente, nunca zero.
- A escala calibrada soma ao total **ENEM** do domínio conhecido, não ao total
  brasileiro. `peso_calibrado_proxy_normalizado` tem média 1 dentro da edição.
- Referência escolhida pelo autor: concluintes anuais. Referência disponível:
  PNADC matriculados no ensino médio regular nas séries 3/4, **proxy** que não
  confirma conclusão. Não é população brasileira inteira nem inclui EJA.
- 2010/2011 sem referência PNADC; pesos externos ausentes. Não foi emprestado
  um ano posterior. Não há amostra nacional plenamente calibrada nesses anos.
- 95%, 1 e 2 pp e DEFF 1; 1,5; 2; 3: cenários para proporções, não notas ou
  poder de regressão. 20 mil cobre 1 pp sob DEFF=2 no cadastro; não prova esse
  DEFF. Kish calibrado em 2021 é aproximadamente 2,10, alertando para precisão.
  Cenário mais conservador DEFF=3: arredondar para 30 mil/ano; não executado.

## Variáveis prioritárias

Em 2023: notas `NU_NOTA_CN/CH/LC/MT/REDACAO`; renda `Q006`; escolaridade
parental `Q001/Q002`; moradores `Q005`; computador/internet `Q024/Q025`;
`TP_COR_RACA`, `TP_SEXO`, `TP_FAIXA_ETARIA`, `TP_ESCOLA`,
`TP_DEPENDENCIA_ADM_ESC`, `TP_LOCALIZACAO_ESC`.
Usar o mapa anual: Qxxx **não tem semântica constante em 2010–2023**.
A amostra consolidada conserva as colunas originais, não renomeia silenciosamente.

Contexto proposto: PIB per capita, abandono no ensino médio, porte populacional,
renda domiciliar censitária, Gini e IDHM-E. Nem todos são anuais; IDHM e Atlas
têm observação 2010, não uma série interpolada. PIB per capita não é renda
familiar. Residência não está disponível; eventual junção usa município da
escola com nome explícito e avaliação de cobertura, nunca residência presumida.

## Proveniência e reprodução

1. Fontes ENEM e municipais já locais: `docs/importacao.md`.
2. PNADC: catálogo `docs/sources/pnad_sampling_catalog.json`, fontes oficiais
   IBGE, manifestos individuais com URL/hash; arquivos originais imutáveis.
3. Código e comandos, ambiente `.venv` ativado:

```powershell
python -m enem_analysis.data.pnad_sampling
python -m enem_analysis.data.sampling_plan
python -m enem_analysis.data.calibrate_sample
python -m enem_analysis.visualization.sampling_report
python -m pytest -q
```

`pnad_sampling --acquire` serve à aquisição oficial quando necessária. O código
de seleção reaproveita cadastros/amostras já produzidos; alterações futuras de
critérios exigem nova decisão e nova versão de derivados. Semente por edição:
20260920 + ano. Versões e hash final: `validacao_amostra.json`.

Tratamentos: PNAD por posições fixas oficiais; ENEM por Parquets completos;
campos originais preservados, categorias comparáveis mapeadas; renda mantida em
faixas por ano; nenhuma imputação, remoção por extremos ou truncamento de pesos.
Exclusões de elegibilidade são sequenciais e quantificadas. Sexo de 2012
harmonizado de 0/1 para M/F; raça 3/4 tem significados invertidos ENEM/PNAD;
tipo de escola resolvido por rótulos anuais. Registros excluídos da amostra
analítica continuam nas bases integrais.

Calibração converge com resíduo absoluto dividido pelo total inferior a 1e-9.
Seu domínio PNAD exclui raça/sexo desconhecidos e renormaliza as margens nesse
domínio; a tabela de margens descritivas apresenta também não declarados quando
observados. Restrições exatas: `residuos_calibracao_YYYY.csv`.

Erros-padrão das proporções PNAD: linearização de Taylor da razão, estratos e
UPAs incluindo unidades sem observações no domínio, aproximação com reposição.
Não se propaga essa incerteza ao ENEM nesta entrega. Kish mede dispersão de
pesos, não todo o efeito de desenho. Modelagem, inferência e análise causal não
foram executadas. Não chamar variáveis candidatas de determinantes comprovados.

Em 2023, erros-padrão e CV das margens ficam ausentes: há estrato com uma única
UPA e contribuição não nula ao domínio; sua variância não é estimável pela
linearização implementada. Não foi imposto ajuste silencioso ou variância zero.
Essa pendência precisa ser resolvida antes de divulgar intervalos das margens.
