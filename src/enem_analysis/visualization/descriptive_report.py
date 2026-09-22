"""Render computed descriptive results as figures, PDF and native-authoring blocks."""

# Narrative report prose intentionally uses long string literals.
# ruff: noqa: E501
from __future__ import annotations

import json
from html import escape

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pymupdf
from reportlab.platypus import Image, KeepTogether, Paragraph, Spacer

from enem_analysis.data.acquire import ROOT, write_json
from enem_analysis.data.descriptive_analysis import INCOME_ORDER, OUT, SCORE_NAMES
from enem_analysis.data.sampling_plan import SCORES
from enem_analysis.statistics.descriptive import weighted_correlation, weighted_summary
from enem_analysis.visualization.report_assets import save_table_csv
from enem_analysis.visualization.sampling_report import Report, number

FIG = ROOT / "reports/figures/descriptive"
TABLES = ROOT / "reports/tables/descriptive"
PDF = ROOT / "reports/report/relatorio_descritivo_enem.pdf"
EDUC_LABELS = [
    "Nunca estudou",
    "Fundamental inicial\nincompleto",
    "Fundamental final\nincompleto",
    "Médio incompleto",
    "Médio completo",
    "Superior completo",
    "Pós-graduação",
    "Não sabe",
]


def read(name):
    return pd.read_csv(OUT / name)


def image_save(fig, name):
    fig.savefig(FIG / name, dpi=175, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def box_stats(frame, field, category, score):
    part = frame[frame[field].eq(category)]
    s = weighted_summary(part[score], part.peso_desenho)
    return {
        "label": category,
        "med": s["mediana"],
        "q1": s["q1"],
        "q3": s["q3"],
        "whislo": s["bigode_inferior"],
        "whishi": s["bigode_superior"],
        "fliers": part.loc[
            part[score].lt(s["cerca_inferior"]) | part[score].gt(s["cerca_superior"]),
            score,
        ].to_numpy(),
    }


def figures(sample):
    FIG.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titleweight": "bold",
            "axes.labelcolor": "#253746",
        }
    )
    annual = read("resumos_anuais.csv")
    s = sample[sample.ano.eq(2023)]
    fig, ax = plt.subplots(figsize=(9, 4))
    for score in SCORES:
        part = annual[annual.variavel.eq(score)]
        ax.plot(
            part.ano, part.media, marker="o", label=SCORE_NAMES[score], lw=1.7, ms=3
        )
    ax.set(
        xlabel="Edição do ENEM",
        ylabel="Média ponderada (pontos)",
        xticks=list(range(2010, 2024)),
    )
    ax.tick_params(axis="x", rotation=45)
    ax.legend(ncol=3, loc="upper left", fontsize=9)
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    image_save(fig, "01_evolucao.png")

    fig, axes = plt.subplots(3, 2, figsize=(9, 9), layout="constrained")
    for ax, score in zip(axes.flat, SCORES, strict=False):
        ax.hist(
            s[score],
            bins=np.arange(0, 1021, 20),
            weights=100 * s.peso_desenho / s.peso_desenho.sum(),
            color="#257994",
            edgecolor="white",
            lw=0.35,
        )
        ax.set(
            title=SCORE_NAMES[score],
            xlabel="Nota (pontos)",
            ylabel="% ponderado",
            xlim=(0, 1000),
        )
    bs = []
    for score in SCORES:
        t = s.copy()
        t["area"] = SCORE_NAMES[score]
        bs.append(box_stats(t, "area", SCORE_NAMES[score], score))
    axes.flat[-1].bxp(
        bs,
        orientation="horizontal",
        showfliers=True,
        flierprops={"markersize": 1.5, "alpha": 0.25},
        medianprops={"color": "#B35430"},
    )
    axes.flat[-1].set(
        title="Dispersão e extremos", xlabel="Nota (pontos)", xlim=(0, 1000)
    )
    image_save(fig, "02_distribuicoes.png")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4), sharey=True, layout="constrained")
    labels = ["Até\n1.320", "1.320,01–\n2.640", "2.640,01–\n6.600", "Acima de\n6.600"]
    for ax, score in zip(axes, ["NU_NOTA_MT", "NU_NOTA_REDACAO"], strict=True):
        boxes = [box_stats(s, "renda_grupo", c, score) for c in INCOME_ORDER]
        for b, lab in zip(boxes, labels, strict=True):
            b["label"] = lab
        ax.bxp(
            boxes,
            showfliers=True,
            flierprops={"markersize": 2, "alpha": 0.25},
            medianprops={"color": "#B35430"},
        )
        ax.set(
            title=SCORE_NAMES[score],
            xlabel="Renda familiar mensal (R$)",
            ylabel="Nota (pontos)",
            ylim=(0, 1050),
        )
    image_save(fig, "03_renda.png")

    fig, ax = plt.subplots(figsize=(9, 4.7), layout="constrained")
    for role, col, offset, color in [
        ("Mãe", "Q002", -0.10, "#B35430"),
        ("Pai", "Q001", 0.10, "#257994"),
    ]:
        means = [
            weighted_summary(
                s.loc[s[col].eq(code), "NU_NOTA_MT"],
                s.loc[s[col].eq(code), "peso_desenho"],
            )["media"]
            for code in "ABCDEFGH"
        ]
        ax.scatter(means, np.arange(8) + offset, label=role, c=color, s=45)
    ax.set(
        yticks=np.arange(8),
        yticklabels=EDUC_LABELS,
        xlabel="Média ponderada de matemática (pontos)",
        xlim=(400, 660),
    )
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.2)
    ax.legend()
    image_save(fig, "04_escolaridade_parental.png")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4), layout="constrained")
    races = ["Branca", "Preta", "Parda", "Amarela", "Indigena", "Nao_declarada"]
    boxes = [box_stats(s, "raca", c, "NU_NOTA_MT") for c in races]
    boxes[-2]["label"] = "Indígena"
    boxes[-1]["label"] = "Não declarada"
    axes[0].bxp(
        boxes,
        orientation="horizontal",
        showfliers=True,
        flierprops={"markersize": 1.4, "alpha": 0.3},
    )
    axes[0].set(title="Raça/cor", xlabel="Matemática (pontos)", xlim=(0, 1000))
    axes[1].bxp(
        [box_stats(s, "escola", c, "NU_NOTA_MT") for c in ["Publica", "Privada"]],
        showfliers=True,
        flierprops={"markersize": 1.5, "alpha": 0.3},
    )
    axes[1].set(
        title="Tipo de escola",
        ylabel="Matemática (pontos)",
        ylim=(0, 1000),
        xticklabels=["Pública", "Privada"],
    )
    image_save(fig, "05_grupos.png")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), layout="constrained")
    matrix = np.array(
        [
            [weighted_correlation(s[a], s[b], s.peso_desenho)[0] for b in SCORES]
            for a in SCORES
        ]
    )
    im = axes[0].imshow(matrix, vmin=-1, vmax=1, cmap="RdBu_r")
    short = ["CN", "CH", "LC", "MT", "RED"]
    axes[0].set(
        xticks=np.arange(5),
        yticks=np.arange(5),
        xticklabels=short,
        yticklabels=short,
        title="Pearson ponderado",
    )
    for i in range(5):
        for j in range(5):
            axes[0].text(
                j,
                i,
                f"{matrix[i, j]:.2f}",
                ha="center",
                va="center",
                color="white" if abs(matrix[i, j]) > 0.7 else "black",
                fontsize=9,
            )
    fig.colorbar(im, ax=axes[0], shrink=0.7)
    axes[1].scatter(
        s.NU_NOTA_MT,
        s.NU_NOTA_REDACAO,
        s=3,
        alpha=0.08,
        color="#257994",
        rasterized=True,
    )
    axes[1].set(
        xlabel="Matemática (pontos)",
        ylabel="Redação (pontos)",
        title="Dispersão individual",
        xlim=(0, 1000),
        ylim=(0, 1000),
    )
    image_save(fig, "06_associacoes.png")

    linked = s[s.pib_per_capita_reais.notna()]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.3), layout="constrained")
    axes[0].scatter(
        linked.pib_per_capita_reais / 1000,
        linked.NU_NOTA_MT,
        s=3,
        alpha=0.08,
        color="#257994",
        rasterized=True,
    )
    axes[0].set(
        xlabel="PIB per capita municipal (mil R$ correntes)",
        ylabel="Matemática (pontos)",
        title="Atividade econômica",
        ylim=(0, 1000),
    )
    axes[1].scatter(
        linked.educ_abandono_medio_pct,
        linked.NU_NOTA_MT,
        s=3,
        alpha=0.08,
        color="#B35430",
        rasterized=True,
    )
    axes[1].set(
        xlabel="Abandono no ensino médio municipal (%)",
        ylabel="Matemática (pontos)",
        title="Fluxo escolar",
        ylim=(0, 1000),
    )
    image_save(fig, "07_contexto.png")


def make_blocks():
    blocks = []

    def add(kind, text=None, **kwargs):
        blocks.append(
            {"type": kind, **({"text": text} if text is not None else {}), **kwargs}
        )

    def table(title, headers, rows, widths=None):
        add("caption", title)
        add("table", headers=headers, rows=rows, widths=widths)

    def figure(file, caption):
        add("image", path=str((FIG / file).resolve()), name=file)
        add("caption", caption)

    stats = read("resumos_anuais.csv")
    groups = read("resumos_grupos.csv")
    freq = read("frequencias.csv")
    quality = read("qualidade.csv")
    corr = read("correlacoes.csv")
    coverage = read("cobertura_contextual.csv")
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    plans = [
        json.loads(
            (ROOT / f"data/processed/sampling/plano_{y}.json").read_text(
                encoding="utf-8"
            )
        )
        for y in range(2010, 2024)
    ]

    def g(group, cat, score="NU_NOTA_MT"):
        return groups[
            groups.ano.eq(2023)
            & groups.grupo.eq(group)
            & groups.categoria.eq(cat)
            & groups.variavel.eq(score)
        ].iloc[0]

    def f(group, cat):
        return freq[
            freq.ano.eq(2023) & freq.variavel.eq(group) & freq.categoria.eq(cat)
        ].iloc[0]

    def c(year, a, b):
        return corr[
            corr.ano.eq(year) & corr.variavel_a.eq(a) & corr.variavel_b.eq(b)
        ].iloc[0]

    low, high = g("renda_grupo", INCOME_ORDER[0]), g("renda_grupo", INCOME_ORDER[-1])
    public, private = g("escola", "Publica"), g("escola", "Privada")
    add("title", "Desigualdade socioeconômica, contexto municipal e desempenho no ENEM")
    add("subtitle", "Relatório descritivo — cortes anuais de 2010–2023")
    add(
        "p",
        "Versão para revisão dos autores. O trabalho permanece no 2º estado; a Proposta é a etapa acadêmica previamente concluída. Este relatório apresenta resultados descritivos calculados, sem testes de hipóteses, intervalos inferenciais ou regressões.",
    )
    add("h1", "1. Introdução")
    add(
        "p",
        "O problema investigado é a desigualdade de desempenho educacional entre participantes que chegam ao final do ensino médio em condições familiares, escolares e territoriais distintas. A disponibilidade de recursos financeiros, a escolaridade dos responsáveis e as condições de estudo podem acompanhar diferenças nas notas, mas não atuam de forma isolada: renda, escola e território também se relacionam entre si.",
    )
    add(
        "p",
        "A pergunta de interesse é: quais características socioeconômicas, demográficas e escolares estão associadas às diferenças de desempenho dos concluintes declarados do ensino médio regular no ENEM, e que informação adicional oferece o contexto municipal da escola? O objetivo desta etapa é caracterizar a amostra, avaliar a qualidade dos dados e descrever distribuições, diferenças entre grupos e associações que orientem uma investigação inferencial posterior. A expressão ‘determinantes’ não é usada como conclusão causal.",
    )
    add("h1", "2. Coleta e apresentação dos dados")
    add("h2", "2.1 Origem, unidade de observação e elegibilidade")
    add(
        "p",
        f"Foram utilizados os microdados públicos do INEP para 2010–2023, já importados localmente. A coleção integral contém {number(sum(p['flow'][0]['remaining'] for p in plans))} inscrições; após os critérios de elegibilidade, os cadastros anuais somam {number(sum(p['N_eligible'] for p in plans))} inscrições. Não se trata de uma coleta primária por questionário próprio: os arquivos e seus dicionários foram obtidos de fontes oficiais e processados por código reproduzível. O pacote de 2023 já existia no projeto; sua data e URL exatas de aquisição original não foram recuperadas.",
    )
    add(
        "p",
        "Cada observação representa uma inscrição em uma edição do exame, não uma pessoa acompanhada ao longo de 14 anos. O cadastro elegível exige conclusão declarada no ano, ensino regular, ausência de condição de treineiro quando o campo existe, presença nas quatro provas, cinco notas numéricas e redação regular segundo o dicionário anual. Em 2010–2014 não existe campo independente de treineiro nos arquivos adquiridos. As restrições de presença e redação selecionam participantes; a ausência de notas na amostra não mede a qualidade da base integral.",
    )
    table(
        "Tabela 1. Cadastros anuais e amostra efetivamente analisada.",
        ["Ano", "Inscritos na base", "Elegíveis", "Amostra"],
        [
            [
                p["year"],
                number(p["flow"][0]["remaining"]),
                number(p["N_eligible"]),
                "20.000",
            ]
            for p in plans
        ],
        [50, 165, 155, 110],
    )
    add("h2", "2.2 Amostragem e ponderação")
    add(
        "p",
        "A amostra existente foi preservada: 20.000 inscrições por edição, 280.000 no total. O sorteio ocorreu sem reposição em estratos de ano × região da escola × raça/cor × sexo × renda familiar original. A alocação é proporcional ao tamanho do estrato, com piso de duas observações ou inclusão certa quando há apenas uma. A probabilidade condicional é n_h/N_h e o peso de desenho é N_h/n_h; a semente é 20260920 + ano. As estatísticas principais deste relatório usam esses pesos, que reconstituem o cadastro elegível do ENEM, não a população brasileira de concluintes.",
    )
    add(
        "p",
        "A referência substantiva escolhida foi a população de concluintes anuais. A PNAD Contínua disponível identifica alunos de ensino médio regular nas séries 3/4, uma proxy que não confirma conclusão. A calibração parcial de 2012–2023 ajusta raça × sexo e idade ampla e mantém região da escola × renda ENEM internamente; renda domiciliar e residência PNAD não foram equiparadas a renda familiar e escola ENEM. Em 2010/2011 há somente peso de desenho. O cenário anterior de 95% e erro de 1 ponto percentual com DEFF=2 é planejamento de proporções, não garantia de precisão das médias ou de todos os subgrupos.",
    )
    add("h2", "2.3 Variáveis e indicadores contextuais")
    table(
        "Tabela 2. Variáveis centrais e função na análise (códigos de 2023).",
        ["Dimensão / colunas", "Interpretação"],
        [
            [
                "NU_NOTA_CN, CH, LC, MT e REDACAO",
                "Cinco desfechos em pontos, analisados separadamente; os quatro primeiros nomes também têm prefixo NU_NOTA_.",
            ],
            [
                "Q006; Q005",
                "Renda familiar em faixas; número de moradores. Não se atribuiu renda pontual à faixa.",
            ],
            [
                "Q001; Q002",
                "Escolaridade de pai/responsável e mãe/responsável. ‘Não sei’ permanece explícito.",
            ],
            [
                "TP_COR_RACA; TP_SEXO; TP_FAIXA_ETARIA",
                "Características demográficas categóricas; códigos não são medidas numéricas.",
            ],
            [
                "TP_ESCOLA; TP_DEPENDENCIA_ADM_ESC; TP_LOCALIZACAO_ESC",
                "Tipo de escola, dependência administrativa e localização urbana/rural.",
            ],
            [
                "Q024; Q025",
                "Computador e internet na residência: recursos de estudo potencialmente ligados à renda.",
            ],
            [
                "CO_MUNICIPIO_ESC; ano",
                "Chaves de vínculo contextual, nunca medidas quantitativas nem residência presumida.",
            ],
        ],
        [220, 260],
    )
    add(
        "p",
        "Os códigos dos questionários mudaram: em 2010 a renda familiar é Q04; em 2011, Q004; em 2012–2014, Q003; desde 2015, Q006. As escolaridades dos pais também mudam de coluna. Os mapas anuais do projeto foram usados antes dos cálculos. O detalhamento de grupos e figuras concentra-se em 2023, a última edição do escopo; todas as edições têm tabelas anuais de notas, qualidade e grupos, sem tratar a mesma letra de renda como poder de compra constante.",
    )
    add(
        "p",
        "O contexto municipal provém do PIB dos Municípios/IBGE, das taxas de rendimento escolar/INEP, do Censo 2022/IBGE e de indicadores Atlas disponíveis no Ipeadata. O núcleo anual selecionado é PIB per capita e abandono no ensino médio; renda domiciliar e população são examinadas em 2022, e Gini, renda Atlas e IDHM-E em 2010. O vínculo é à esquerda, por município da escola e mesmo ano, com cardinalidade muitos-para-um. Nenhum dado censitário foi interpolado ou repetido em anos sem observação; o PIB per capita não é a renda recebida pela família.",
    )
    add("h1", "3. Análise descritiva")
    add(
        "p",
        "As médias são somas ponderadas divididas pela soma dos pesos. Variância e desvio-padrão descrevem a dispersão dos valores, com denominador soma dos pesos; não são variância e erro-padrão de um estimador. Mediana e quartis usam a inversa da distribuição empírica ponderada. Correlações são de Pearson ponderado em pares completos. Não foram imputados valores, excluídos extremos ou aplicados testes. Os gráficos não apresentam intervalos de confiança.",
    )
    add("h2", "3.1 Qualidade, ausências e valores atípicos")
    q23 = quality[quality.ano.eq(2023)].set_index("variavel")
    table(
        "Tabela 3. Ausência e não declaração em 2023 (n total = 20.000).",
        ["Campo / situação", "n bruto", "% ponderado"],
        [
            [
                "Município da escola ausente",
                number(q23.loc["CO_MUNICIPIO_ESC", "n_ausente"]),
                number(q23.loc["CO_MUNICIPIO_ESC", "pct_ausente_ponderado"], 2),
            ],
            [
                "Escolaridade paterna: não sei",
                number(q23.loc["Q001", "n_nao_declarado"]),
                number(q23.loc["Q001", "pct_nao_declarado_ponderado"], 2),
            ],
            [
                "Escolaridade materna: não sei",
                number(q23.loc["Q002", "n_nao_declarado"]),
                number(q23.loc["Q002", "pct_nao_declarado_ponderado"], 2),
            ],
            [
                "Raça/cor não declarada",
                number(q23.loc["TP_COR_RACA", "n_nao_declarado"]),
                number(q23.loc["TP_COR_RACA", "pct_nao_declarado_ponderado"], 2),
            ],
            ["Qualquer uma das cinco notas ausente", "0", "0,00 (por construção)"],
        ],
        [300, 85, 95],
    )
    con = manifest["consistency"]
    add(
        "p",
        f"Não foram encontradas duplicidades de inscrição × ano, notas não finitas/negativas, redações fora de 0–1000 ou códigos fora dos domínios verificados. Não se impôs teto universal de 1000 às provas TRI. As chaves municipais conhecidas concordam com a UF registrada. Em 2023, há {number(con['school_type_administration_disagreement_2023'])} divergências entre tipo de escola declarado e dependência administrativa entre {number(con['school_type_administration_compared_2023'])} comparáveis ({number(100 * con['school_type_administration_disagreement_2023'] / con['school_type_administration_compared_2023'], 2)}% bruto). São campos de origem/definição distintas e merecem revisão; nenhum foi sobrescrito automaticamente.",
    )
    zeros = read("zeros_2023.csv")
    add(
        "p",
        "Zeros numéricos nas provas objetivas foram conferidos na base integral: "
        + "; ".join(
            f"{SCORE_NAMES[x.variavel]}: {x.n_zero}" for x in zeros.itertuples()
        )
        + ". Esses registros têm presença informada e não foram convertidos em ausências. A conferência prova sua origem no arquivo, não esclarece sozinha o motivo de cada zero. Os boxplots usam cercas de 1,5 vezes o intervalo interquartil; pontos fora delas permanecem nos cálculos e não são automaticamente erros.",
    )
    mt = stats[stats.ano.eq(2023) & stats.variavel.eq("NU_NOTA_MT")].iloc[0]
    add(
        "p",
        f"Em matemática, {number(mt.n_atipicos_iqr)} observações ficaram fora das cercas globais ({number(mt.pct_atipicos_ponderada, 2)}% ponderado). O número de moradores variou de 1 a 20, com mediana 4; 20 é a última categoria do instrumento e requer atenção à forma de registro. Valores extremos de PIB também foram conservados, pois concentração de atividade econômica não equivale a erro de digitação.",
    )
    add("h2", "3.2 Distribuição das notas e composição da amostra")
    s23 = stats[stats.ano.eq(2023) & stats.variavel.isin(SCORES)]
    table(
        "Tabela 4. Medidas ponderadas das notas em 2023 (20.000 por área).",
        ["Área", "Média", "Mediana", "Variância", "Desvio-padrão"],
        [
            [
                SCORE_NAMES[x.variavel],
                number(x.media, 1),
                number(x.mediana, 1),
                number(x.variancia, 1),
                number(x.dp, 1),
            ]
            for x in s23.itertuples()
        ],
        [105, 80, 90, 105, 100],
    )
    add(
        "p",
        "As notas mostram dispersão considerável dentro da mesma edição. Matemática tem desvio-padrão de "
        + number(mt.dp, 1)
        + " pontos. A redação possui distribuição mais discreta e uma escala de correção distinta; sua média numericamente maior não autoriza concluir que os candidatos ‘sabem mais’ redação que matemática. Média e mediana próximas em algumas áreas não dispensam examinar assimetria e caudas.",
    )
    figure(
        "02_distribuicoes.png",
        "Figura 1. Histogramas com percentuais ponderados e boxplots ponderados das cinco notas, ENEM 2023, n=20.000. Quartis/cercas usam peso de desenho; pontos atípicos representam observações brutas, sem exclusão. Fonte: elaboração própria, microdados INEP.",
    )
    add(
        "p",
        "A composição ponderada de 2023 é distinta da contagem bruta devido à sobreamostragem de células pequenas. Por exemplo, indígenas representam "
        + number(f("raca", "Indigena").pct_bruto, 2)
        + "% das observações sorteadas, mas "
        + number(f("raca", "Indigena").pct_ponderado, 2)
        + "% do cadastro elegível reconstruído. Por isso, proporções sem ponderação não descrevem corretamente esse cadastro. Não declaração aparece no denominador, sem ser confundida com uma categoria racial do IBGE.",
    )
    table(
        "Tabela 5. Composição e médias por grupos em 2023.",
        ["Grupo", "n bruto", "% ponderado", "Média MT", "Média redação"],
        [
            [
                label,
                number(f(field, cat).n),
                number(f(field, cat).pct_ponderado, 2),
                number(g(field, cat).media, 1),
                number(g(field, cat, "NU_NOTA_REDACAO").media, 1),
            ]
            for field, cat, label in [
                ("sexo", "F", "Sexo feminino"),
                ("sexo", "M", "Sexo masculino"),
                ("raca", "Branca", "Branca"),
                ("raca", "Preta", "Preta"),
                ("raca", "Parda", "Parda"),
                ("raca", "Amarela", "Amarela"),
                ("raca", "Indigena", "Indígena"),
                ("raca", "Nao_declarada", "Não declarada"),
                ("escola", "Publica", "Escola pública"),
                ("escola", "Privada", "Escola privada"),
            ]
        ],
        [160, 70, 90, 80, 80],
    )
    add(
        "p",
        "Cada bloco (sexo, raça/cor e escola) tem seu próprio total de 100%; as linhas de blocos diferentes não devem ser somadas. As cinco regiões da escola e as faixas etárias constam nas frequências anuais completas; localização desconhecida é mantida como ausência, não uma sexta região.",
    )
    figure(
        "01_evolucao.png",
        "Figura 2. Médias ponderadas por edição, n=20.000/ano. Cortes transversais repetidos, com mudanças de composição e regras do exame; não é evolução dos mesmos indivíduos nem efeito identificado de políticas. Fonte: elaboração própria, INEP.",
    )
    add("h2", "3.3 Comparação de condições familiares, demográficas e escolares")
    table(
        "Tabela 6. Renda familiar e desempenho em 2023.",
        ["Renda mensal", "n", "% ponderado", "Média MT", "Média redação"],
        [
            [
                cat,
                number(f("renda_grupo", cat).n),
                number(f("renda_grupo", cat).pct_ponderado, 2),
                number(g("renda_grupo", cat).media, 1),
                number(g("renda_grupo", cat, "NU_NOTA_REDACAO").media, 1),
            ]
            for cat in INCOME_ORDER
        ],
        [180, 60, 85, 75, 80],
    )
    add(
        "p",
        f"A média de matemática passa de {number(low.media, 1)} pontos no grupo de até R$1.320 para {number(high.media, 1)} entre os de renda acima de R$6.600, diferença descritiva de {number(high.media - low.media, 1)} pontos. As faixas intermediárias também apresentam médias crescentes. A figura mostra, porém, ampla sobreposição das distribuições: renda não determina a nota de cada candidato. Os limites intermediários da tabela abreviam intervalos que começam em R$1.320,01 e R$2.640,01; o grupo inicial reúne ausência de renda e renda até R$1.320.",
    )
    figure(
        "03_renda.png",
        "Figura 3. Boxplots ponderados de matemática e redação por renda familiar, ENEM 2023, n=20.000. Cada faixa conserva seus extremos. Medianas e dispersões não constituem teste de diferença ou ajuste por confundidores. Fonte: elaboração própria, INEP.",
    )
    figure(
        "04_escolaridade_parental.png",
        "Figura 4. Média ponderada de matemática por escolaridade de cada responsável, ENEM 2023. As oito categorias incluem ‘não sei’; todos os 20.000 casos entram em cada classificação. Pontos não têm intervalos inferenciais. Fonte: elaboração própria, INEP.",
    )
    mae = g("mae_rotulo", "Nunca estudou.")
    mae2 = g("mae_rotulo", "Completou a Pós-graduação.")
    add(
        "p",
        f"A escolaridade parental acompanha diferenças de desempenho: para escolaridade materna, as médias de matemática são {number(mae.media, 1)} pontos em ‘nunca estudou’ (n={number(mae.n)}) e {number(mae2.media, 1)} em pós-graduação (n={number(mae2.n)}). A categoria ‘não sei’ não representa escolaridade zero. Recursos de estudo também se associam às notas: com internet, média {number(g('internet_rotulo', 'Sim.').media, 1)}; sem internet, {number(g('internet_rotulo', 'Não.').media, 1)}. Não é possível separar essas associações da renda ou escolaridade apenas por comparação de médias.",
    )
    figure(
        "05_grupos.png",
        "Figura 5. Matemática por raça/cor e escola, ENEM 2023, n=20.000. Boxplots ponderados; o tamanho bruto e a participação ponderada de cada grupo estão na Tabela 5. Há dispersão e sobreposição dentro de todos os grupos. Fonte: elaboração própria, INEP.",
    )
    add(
        "p",
        f"A diferença média privada–pública em matemática é {number(private.media - public.media, 1)} pontos. O contraste masculino–feminino é {number(g('sexo', 'M').media - g('sexo', 'F').media, 1)} pontos em matemática, mas {number(g('sexo', 'M', 'NU_NOTA_REDACAO').media - g('sexo', 'F', 'NU_NOTA_REDACAO').media, 1)} em redação: a direção e a magnitude dependem da área. Diferenças raciais descrevem desigualdades observadas em contextos sociais e escolares distintos, não capacidades intrínsecas ou efeitos causais da classificação racial.",
    )
    contingency = read("contingencia_renda_escola_2023.csv")

    def ct(income, school):
        return contingency[
            contingency.renda_grupo.eq(income) & contingency.escola.eq(school)
        ].iloc[0]

    table(
        "Tabela 7. Associação entre renda e escola (contingência), 2023.",
        ["Renda mensal", "n pública", "n privada", "% privada dentro da renda"],
        [
            [
                cat,
                number(ct(cat, "Publica").n),
                number(ct(cat, "Privada").n),
                number(ct(cat, "Privada").pct_dentro_renda, 2),
            ]
            for cat in INCOME_ORDER
        ],
        [180, 85, 85, 130],
    )
    add(
        "p",
        f"A participação ponderada de escola privada aumenta de {number(ct(INCOME_ORDER[0], 'Privada').pct_dentro_renda, 2)}% na faixa inferior para {number(ct(INCOME_ORDER[-1], 'Privada').pct_dentro_renda, 2)}% na superior. As contagens são brutas e a última coluna é ponderada; seus denominadores não devem ser confundidos. Esse padrão evidencia composição socioeconômica diferente e impede atribuir a diferença de notas exclusivamente à escola.",
    )
    add("h2", "3.4 Associação entre variáveis quantitativas")
    figure(
        "06_associacoes.png",
        "Figura 6. Correlações de Pearson ponderadas e dispersão matemática × redação, ENEM 2023, n=20.000 pares. Na dispersão, cada ponto tem o mesmo tamanho e não representa expansão; o mapa de calor aplica pesos. CN=natureza; CH=humanas; LC=linguagens; MT=matemática; RED=redação. Fonte: elaboração própria, INEP.",
    )
    add(
        "p",
        f"Matemática e redação apresentam correlação ponderada de {number(c(2023, 'NU_NOTA_MT', 'NU_NOTA_REDACAO').r_pearson_ponderado, 3)}: o desempenho tende a caminhar conjuntamente, sem equivalência perfeita entre habilidades. A correlação de matemática com moradores é {number(c(2023, 'NU_NOTA_MT', 'moradores_num').r_pearson_ponderado, 3)}, de pequena magnitude. Não foram calculadas correlações de Pearson usando números arbitrários para raça, sexo ou letras de renda; nesses casos foram usados grupos e contingências.",
    )
    add("h2", "3.5 Contexto municipal e seleção territorial")
    cov = coverage[
        coverage.ano.eq(2023) & coverage.indicador.eq("pib_per_capita_reais")
    ].iloc[0]
    selection = read("selecao_contextual_2023.csv")
    identified = selection[
        selection.dominio.eq("Escola identificada")
        & selection.variavel.eq("NU_NOTA_MT")
    ].iloc[0]
    noid = selection[
        selection.dominio.eq("Escola não vinculada")
        & selection.variavel.eq("NU_NOTA_MT")
    ].iloc[0]
    add(
        "p",
        f"Em 2023, {number(cov.n_indicador_observado)} dos 20.000 candidatos foram vinculados ao contexto da escola, cobrindo {number(cov.pct_coberto_ponderado, 2)}% do cadastro ponderado e {number(cov.municipios_observados)} municípios. A média de matemática é {number(identified.media, 1)} nesse domínio, contra {number(noid.media, 1)} entre os sem vínculo. A diferença de {number(identified.media - noid.media, 1)} pontos mostra que a disponibilidade territorial não é neutra em relação ao desempenho observado; não se deve generalizar automaticamente a análise municipal para os casos sem localização.",
    )
    table(
        "Tabela 8. Matemática e contexto do município da escola: Pearson ponderado.",
        ["Ano", "Indicador", "n pares", "r"],
        [
            [
                year,
                label,
                number(c(year, "NU_NOTA_MT", var).n_pares),
                number(c(year, "NU_NOTA_MT", var).r_pearson_ponderado, 3),
            ]
            for year, var, label in [
                (2010, "renda_per_capita_atlas_reais2010", "Renda per capita Atlas"),
                (2010, "idhm_educacao", "IDHM-E"),
                (2010, "gini_atlas", "Gini"),
                (
                    2022,
                    "renda_domiciliar_per_capita_censo2022_reais",
                    "Renda domiciliar per capita Censo",
                ),
                (2022, "educ_abandono_medio_pct", "Abandono no ensino médio"),
                (2023, "pib_per_capita_reais", "PIB per capita"),
                (2023, "educ_abandono_medio_pct", "Abandono no ensino médio"),
            ]
        ],
        [45, 290, 80, 65],
    )
    figure(
        "07_contexto.png",
        f"Figura 7. Notas e indicadores do município da escola, 2023, n={number(cov.n_indicador_observado)}. Pontos individuais não expandidos, com contexto repetido por município; extremos mantidos. Fonte: elaboração própria, INEP/IBGE. Associação descritiva não é efeito municipal identificado.",
    )
    add(
        "p",
        "Renda domiciliar e IDHM-E exibem associações positivas nos recortes censitários disponíveis. PIB per capita tem associação positiva mais fraca em 2023; abandono é praticamente não associado linearmente à nota nesse ano e tem sinal diferente em 2022. Isso não demonstra benefício do abandono: diferenças de composição, escala, seleção e confundimento podem gerar esse resultado agregado. A tabela compara recortes distintos, não estima mudança temporal de um mesmo efeito. Não foram transportados Gini/IDHM-E de 2010 para 2023 nem renda censitária de 2022 para outro ano.",
    )
    add("h2", "3.6 Sensibilidade aos pesos externos")
    sens = read("sensibilidade_pesos.csv")
    ss = sens[sens.ano.eq(2023)]

    def se(score, weight):
        return ss[ss.variavel.eq(score) & ss.peso.eq(weight)].iloc[0]

    table(
        "Tabela 9. Médias de 2023 no mesmo domínio com peso externo disponível.",
        ["Área", "n comum", "Peso de desenho", "Peso calibrado"],
        [
            [
                SCORE_NAMES[score],
                number(se(score, "calibrado").n),
                number(se(score, "desenho_mesmo_dominio").media, 1),
                number(se(score, "calibrado").media, 1),
            ]
            for score in SCORES
        ],
        [125, 85, 135, 135],
    )
    add(
        "p",
        "A comparação mantém o mesmo conjunto de observações; assim, a diferença decorre da ponderação, não da retirada adicional de não declarados. Os pesos externos padronizam parcialmente à proxy PNAD e não substituem a análise principal. A incerteza dos alvos PNAD não foi propagada e, em 2023, seus erros-padrão permanecem pendentes devido a um estrato com UPA única. A dispersão dos pesos pode ampliar a variância, sobretudo em grupos raros. Essas restrições impedem afirmar representatividade nacional apenas pela calibração.",
    )
    add("h1", "4. Conclusões e orientação da etapa inferencial")
    add(
        "p",
        f"O relatório identifica um gradiente socioeconômico claro na descrição de 2023: a diferença média de matemática entre as faixas extremas de renda adotadas é {number(high.media - low.media, 1)} pontos, e a diferença entre escola privada e pública é {number(private.media - public.media, 1)}. Escolaridade parental e internet também acompanham diferenças nas notas. Ao mesmo tempo, as distribuições se sobrepõem e renda e escola estão fortemente relacionadas. Logo, não é possível hierarquizar determinantes independentes nem atribuir causalidade a essas diferenças brutas.",
    )
    add(
        "p",
        "A dimensão territorial acrescenta informação, mas sua cobertura seleciona candidatos com notas diferentes dos não vinculados. Associações de renda municipal e IDHM-E não dispensam considerar a composição das famílias; o resultado quase nulo de abandono em 2023 recomenda cautela com expectativas teóricas não confirmadas. A análise descreve inscritos elegíveis que completaram validamente as provas, não jovens que não fizeram o ENEM ou todos os concluintes brasileiros.",
    )
    add(
        "p",
        "A próxima etapa deve pré-especificar os contrastes prioritários e estimar intervalos de confiança respeitando estratos, pesos, frações de amostragem e dependência territorial/escolar relevante. Testes de diferenças entre grupos precisam de hipóteses explícitas, tamanho de efeito e regra para múltiplas comparações. Não usar o tamanho amostral bruto como se o desenho fosse aleatório simples.",
    )
    add(
        "p",
        "Regressões associativas podem comparar blocos: demografia/ano; renda e escolaridade parental; escola e recursos de estudo; contexto municipal. É necessário verificar forma funcional, multicolinearidade, heterocedasticidade, influência e seleção por ausência de localização. Recursos digitais e escola podem mediar parte das associações familiares: modelos com e sem esses blocos respondem a perguntas diferentes. Resultados devem ser confrontados com pesos de desenho/calibrados, tratamento de não declaração e critérios de elegibilidade menos restritivos por área, sempre documentando a mudança de universo.",
    )
    add("h2", "Fontes e reprodução")
    add(
        "p",
        "Fontes oficiais e arquivos de origem: os rótulos a seguir apontam para o INEP e para os arquivos/APIs usados no projeto. As estatísticas deste relatório são cálculos próprios sobre a amostra, não indicadores prontos publicados nessas páginas.",
    )
    add(
        "source",
        "INEP — microdados e dicionários do ENEM",
        url="https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem",
    )
    add(
        "source",
        "IBGE — PNAD Contínua anual, microdados e documentação",
        url="https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Anual/Microdados/Visita/",
    )
    definitions = json.loads(
        (ROOT / "docs/sources/municipal/dicionario_variaveis.json").read_text(
            encoding="utf-8"
        )
    )
    for var, year, label in [
        ("pib_per_capita_reais", 2023, "IBGE — PIB dos Municípios, base 2010–2023"),
        (
            "educ_abandono_medio_pct",
            2023,
            "INEP — taxas municipais de rendimento escolar, 2023",
        ),
        (
            "renda_domiciliar_per_capita_censo2022_reais",
            2022,
            "IBGE — Censo 2022, renda domiciliar per capita",
        ),
        ("idhm_educacao", 2010, "Ipeadata / Atlas — IDHM Educação, referência 2010"),
    ]:
        definition = next(
            d for d in definitions if d["variavel"] == var and d["ano_dado"] == year
        )
        add("source", label, url=definition["link_fonte"])
    add(
        "p",
        "Reprodução: python -m enem_analysis.data.descriptive_analysis; python -m enem_analysis.visualization.descriptive_report. CSVs analíticos: data/processed/descriptive/; tabelas do relatório: reports/tables/descriptive/; figuras: reports/figures/descriptive/. O manifesto registra hashes de entrada, versões e controles de qualidade. As decisões 004 e 005 documentam desenho, recortes, pesos e regras. Nenhuma observação foi removida da amostra de 280.000 nesta etapa; pares incompletos ficam fora apenas do cálculo específico, com denominadores informados.",
    )
    return blocks


def build_pdf(blocks):
    # Reuse the validated typography/table renderer, without its sampling-specific text.
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate

    r = Report()
    table_number = 0
    for b in blocks:
        kind = b["type"]
        if kind in ["title", "subtitle", "h1", "h2"]:
            style = {
                "title": "Title",
                "subtitle": "BodyText",
                "h1": "Heading1",
                "h2": "Heading2",
            }[kind]
            r.story.append(Paragraph(escape(b["text"]), r.styles[style]))
            r.story.append(Spacer(1, 6))
        elif kind in ["p", "caption", "source"]:
            content = escape(b["text"])
            if kind == "source":
                content = f'<link href="{escape(b["url"], quote=True)}" color="#17628A">{content}</link>'
            r.p(content)
        elif kind == "table":
            table_number += 1
            save_table_csv(TABLES, table_number, b["headers"], b["rows"])
            r.table(b["headers"], b["rows"], b.get("widths"))
        elif kind == "image":
            img = Image(b["path"])
            factor = min(480 / img.imageWidth, 560 / img.imageHeight)
            img.drawWidth = img.imageWidth * factor
            img.drawHeight = img.imageHeight * factor
            r.story.append(KeepTogether([img, Spacer(1, 5)]))

    def footer(canvas, doc):
        canvas.setFont("DejaVu", 7)
        canvas.drawString(
            42, 24, "ENEM — Relatório descritivo | versão para revisão dos autores"
        )
        canvas.drawRightString(A4[0] - 42, 24, str(doc.page))

    SimpleDocTemplate(
        str(PDF),
        pagesize=A4,
        leftMargin=42,
        rightMargin=42,
        topMargin=40,
        bottomMargin=42,
        title="Relatório descritivo — ENEM 2010–2023",
    ).build(r.story, onFirstPage=footer, onLaterPages=footer)


def main():
    sample = pd.read_parquet(OUT / "amostra_contexto_escola.parquet")
    figures(sample)
    blocks = make_blocks()
    write_json(OUT / "report_blocks.json", blocks)
    build_pdf(blocks)
    md = []
    for b in blocks:
        if b["type"] == "table":
            md += [
                "| " + " | ".join(map(str, b["headers"])) + " |",
                "|" + "---|" * len(b["headers"]),
            ]
            md += ["| " + " | ".join(map(str, row)) + " |" for row in b["rows"]]
        elif b["type"] == "image":
            md.append(f"![Figura]({b['path']})")
        elif b["type"] == "source":
            md.append(f"[{b['text']}]({b['url']})")
        else:
            md.append(
                {"title": "# ", "h1": "## ", "h2": "### "}.get(b["type"], "")
                + b["text"]
            )
        md.append("")
    (OUT / "relatorio_descritivo.md").write_text("\n".join(md), encoding="utf-8")
    doc = pymupdf.open(PDF)
    previews = OUT / "pdf_previews"
    previews.mkdir(exist_ok=True)
    for i, page in enumerate(doc):
        page.get_pixmap(matrix=pymupdf.Matrix(1.2, 1.2)).save(
            previews / f"page_{i + 1}.png"
        )
    print(f"PDF: {PDF}; {len(doc)} pages; {len(blocks)} content blocks", flush=True)


if __name__ == "__main__":
    main()
