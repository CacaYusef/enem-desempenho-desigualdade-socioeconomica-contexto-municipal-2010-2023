"""Render the approved ENEM 2023 socioeconomic/territorial descriptive report."""

# Narrative prose is deliberately kept close to the computed tables.
# ruff: noqa: E501
from __future__ import annotations

import json
from html import escape
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import pandas as pd
import pymupdf
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from enem_analysis.data.acquire import ROOT, sha256, write_json
from enem_analysis.data.territorial_context import INDICATORS, OUT, REGIONS
from enem_analysis.visualization.report_assets import save_table_csv

PDF = ROOT / "reports/report/relatorio_descritivo_territorial_enem_2023.pdf"
FIG = ROOT / "reports/figures/territorial_2023"
TABLES = ROOT / "reports/tables/territorial_2023"


def number(value, digits=0):
    if value is None or pd.isna(value):
        return "—"
    return (
        f"{float(value):,.{digits}f}".replace(",", "_")
        .replace(".", ",")
        .replace("_", ".")
    )


def pct(value, digits=1):
    return f"{number(value, digits)}%"


def read(name):
    return pd.read_csv(OUT / name)


class Report:
    def __init__(self):
        font_dir = Path(matplotlib.get_data_path()) / "fonts/ttf"
        pdfmetrics.registerFont(TTFont("DejaVu", str(font_dir / "DejaVuSans.ttf")))
        pdfmetrics.registerFont(
            TTFont("DejaVu-Bold", str(font_dir / "DejaVuSans-Bold.ttf"))
        )
        pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold")
        self.styles = getSampleStyleSheet()
        for name in ["Normal", "BodyText", "Title", "Heading1", "Heading2"]:
            self.styles[name].fontName = "DejaVu"
        self.styles["BodyText"].fontSize = 9.3
        self.styles["BodyText"].leading = 13.2
        self.styles["BodyText"].spaceAfter = 8
        self.styles["Heading1"].fontSize = 17
        self.styles["Heading1"].leading = 21
        self.styles["Heading1"].textColor = colors.HexColor("#17394A")
        self.styles["Heading1"].keepWithNext = 1
        self.styles["Heading2"].fontSize = 12
        self.styles["Heading2"].leading = 15
        self.styles["Heading2"].spaceBefore = 10
        self.styles["Heading2"].spaceAfter = 6
        self.styles["Heading2"].textColor = colors.HexColor("#1E6374")
        self.styles["Heading2"].keepWithNext = 1
        self.styles.add(
            ParagraphStyle(
                "Cell", fontName="DejaVu", fontSize=7.3, leading=9.5, alignment=TA_LEFT
            )
        )
        self.styles.add(
            ParagraphStyle(
                "Caption",
                fontName="DejaVu",
                fontSize=7.8,
                leading=10.2,
                textColor=colors.HexColor("#43545C"),
                spaceAfter=5,
            )
        )
        self.styles.add(
            ParagraphStyle(
                "Source",
                fontName="DejaVu",
                fontSize=6.8,
                leading=9,
                textColor=colors.HexColor("#59676C"),
                spaceAfter=8,
            )
        )
        self.story = []
        self.figure_number = 0
        self.table_number = 0

    def section(self, title, break_page=True):
        if self.story and break_page:
            self.story.append(PageBreak())
        self.story.extend([Paragraph(title, self.styles["Heading1"]), Spacer(1, 7)])

    def h2(self, title):
        self.story.append(Paragraph(title, self.styles["Heading2"]))

    def p(self, text):
        self.story.append(Paragraph(text, self.styles["BodyText"]))

    def table(self, headers, rows, widths=None, font_size=None):
        self.table_number += 1
        save_table_csv(TABLES, self.table_number, headers, rows)
        style = self.styles["Cell"]
        if font_size:
            style = ParagraphStyle(
                f"Cell{font_size}",
                parent=style,
                fontSize=font_size,
                leading=font_size + 2,
            )
        contents = [
            [Paragraph(escape(str(x)).replace("\n", "<br/>"), style) for x in row]
            for row in [headers, *rows]
        ]
        table = Table(contents, colWidths=widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DFEAF0")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#17394A")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#17394A")),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#F5F7F8")],
                    ),
                ]
            )
        )
        self.story.extend([table, Spacer(1, 9)])

    def figure(self, filename, caption, source, max_height=400):
        self.figure_number += 1
        path = FIG / filename
        from PIL import Image as PILImage

        with PILImage.open(path) as picture:
            width, height = picture.size
        draw_width = 500
        draw_height = draw_width * height / width
        if draw_height > max_height:
            scale = max_height / draw_height
            draw_width *= scale
            draw_height = max_height
        block = [
            Paragraph(
                f"<b>Figura {self.figure_number}.</b> {caption}", self.styles["Caption"]
            ),
            Image(str(path), width=draw_width, height=draw_height),
            Paragraph(source, self.styles["Source"]),
        ]
        self.story.append(KeepTogether(block))

    def build(self):
        def footer(canvas, doc):
            canvas.setFont("DejaVu", 7)
            canvas.setFillColor(colors.HexColor("#52626A"))
            canvas.drawString(
                42, 25, "ENEM 2023 | Relatório descritivo territorial | 21/09/2026"
            )
            canvas.drawRightString(A4[0] - 42, 25, str(doc.page))

        PDF.parent.mkdir(parents=True, exist_ok=True)
        SimpleDocTemplate(
            str(PDF),
            pagesize=A4,
            rightMargin=42,
            leftMargin=42,
            topMargin=40,
            bottomMargin=43,
            title="Desigualdade socioeconômica e contexto territorial — ENEM 2023",
            author="Projeto ENEM — análise reprodutível",
            subject="Segundo estado: relatório descritivo em elaboração",
        ).build(self.story, onFirstPage=footer, onLaterPages=footer)


def group_row(groups, variable, category, region="Brasil"):
    return groups[
        groups.regiao.eq(region)
        & groups.variavel.eq(variable)
        & groups.categoria.eq(category)
    ].iloc[0]


def main():
    manifest = json.loads((OUT / "frame_manifest.json").read_text(encoding="utf-8"))
    validation = json.loads((OUT / "validacao.json").read_text(encoding="utf-8"))
    regions = read("regioes.csv")
    groups = read("grupos_individuais.csv")
    flow = read("fluxo_elegibilidade.csv")
    quality = read("qualidade_individual.csv")
    coverage = read("cobertura_contextual.csv")
    selection = read("comparacao_cobertura.csv")
    sensitivity = read("sensibilidade_n_municipal.csv")
    assoc = read("associacoes_municipais.csv")
    robust = read("robustez_areas.csv")
    pnad = read("referencia_proxy_pnad.csv")
    cuts = json.loads((OUT / "cortes_quintis.json").read_text(encoding="utf-8"))

    national = regions[regions.regiao.eq("Brasil")].iloc[0]
    known = regions[regions.regiao.isin(REGIONS)]
    income_low = group_row(groups, "renda_grupo", "Até R$ 1.320")
    income_high = group_row(groups, "renda_grupo", "Acima de R$ 6.600")
    public = group_row(groups, "escola", "Pública")
    private = group_row(groups, "escola", "Privada")
    known_score = selection[
        selection.variavel.eq("NOTA_MT") & selection.dominio.eq("Município conhecido")
    ].iloc[0]
    missing_score = selection[
        selection.variavel.eq("NOTA_MT")
        & selection.dominio.eq("Município ausente/não vinculado")
    ].iloc[0]

    r = Report()
    r.section("Desigualdade socioeconômica e contexto territorial<br/>ENEM 2023")
    r.p(
        "<b>Relatório descritivo reprodutível.</b> Pergunta central: até que ponto características socioeconômicas individuais e diferenças econômicas, sociais e educacionais entre municípios e regiões se associam às diferenças de desempenho em matemática entre concluintes declarados do ensino médio regular que participaram do ENEM 2023?"
    )
    r.p(
        "<b>Estado acadêmico:</b> 2º estado — Relatório Descritivo em elaboração e submetido à revisão dos autores. <b>Somente a Proposta foi concluída.</b> A etapa econométrica foi explicitamente adiada e não há regressões, testes de hipótese, p-valores, intervalos de confiança, ICC ou afirmações causais neste documento."
    )
    r.table(
        ["Decisão", "Implementação nesta versão"],
        [
            ["Ano e base", "2023; todos os 1.027.924 elegíveis, sem sorteio."],
            [
                "Desfecho principal",
                "NU_NOTA_MT, escala original; matemática não é combinada com outras provas.",
            ],
            [
                "Unidade",
                "Inscrição individual; contexto ligado ao município da escola.",
            ],
            [
                "Território",
                "Norte, Nordeste, Centro-Oeste, Sudeste e Sul; município ausente preservado como categoria de cobertura.",
            ],
            [
                "Municípios",
                "Referência n≥30; sensibilidades n≥20 e n≥50; igual peso municipal no estimando principal.",
            ],
            [
                "Métodos",
                "Frequências, medidas de posição/dispersão, Pearson, Spearman, quintis e LOWESS apenas visual.",
            ],
        ],
        [120, 391],
    )
    r.p(
        f"Três fatos orientam a leitura: (i) a média de matemática foi {number(national.media, 1)} pontos; (ii) a média passou de {number(income_low.media, 1)} no grupo de renda até R$ 1.320 para {number(income_high.media, 1)} acima de R$ 6.600, diferença descritiva de {number(income_high.media - income_low.media, 1)} pontos; (iii) o município da escola foi identificado para {pct(100 * manifest['n_vinculado'] / manifest['n_elegivel'], 1)} dos elegíveis, e essa cobertura é seletiva."
    )

    r.section("1. Introdução")
    r.p(
        "O ENEM mede competências em um ponto do percurso educacional, mas os candidatos chegam à prova sob condições familiares, escolares e territoriais muito distintas. A proposta do estudo sugere que renda, escolaridade parental, raça/cor, sexo, idade, recursos de estudo e tipo de escola podem discriminar diferenças de desempenho; também sugere que o ambiente do município — condições econômicas, fluxo e qualidade educacional — pode acrescentar contexto. O objetivo desta etapa é organizar a evidência descritiva necessária antes de qualquer modelagem."
    )
    r.h2("Perguntas descritivas")
    r.table(
        ["Bloco", "Pergunta"],
        [
            [
                "Composição",
                "Quem está na base elegível e como a composição varia entre as cinco regiões?",
            ],
            [
                "Gradientes individuais",
                "Como a distribuição de matemática varia com renda, escolaridade parental, raça/cor, sexo, idade, recursos domésticos e tipo de escola?",
            ],
            [
                "Contexto",
                "Como desempenho municipal, IDEB/Saeb, renda, PIB, urbanização, fluxo, distorção e infraestrutura se distribuem e covariam?",
            ],
            [
                "Heterogeneidade regional",
                "As formas das associações e os gradientes observados são semelhantes nas cinco regiões?",
            ],
            [
                "Cobertura",
                "Quem possui município escolar observado e como difere de quem não possui?",
            ],
        ],
        [105, 406],
    )
    r.p(
        "A palavra <i>associação</i> é deliberada. Mesmo relações intensas podem refletir composição dos candidatos, seleção para o ENEM, trajetórias escolares anteriores, variáveis omitidas e diferenças na mensuração. A análise municipal é ecológica: correlação entre médias municipais não é correlação entre indivíduos nem efeito de morar ou estudar naquele município."
    )

    r.section("2. Coleta e apresentação dos dados")
    r.h2("2.1 Fontes oficiais e referências temporais")
    r.table(
        ["Fonte", "Referência/unidade", "Uso e cautela"],
        [
            [
                "INEP — Microdados ENEM",
                "2023; inscrição",
                "Desfecho, perfil, questionário socioeconômico e município da escola.",
            ],
            [
                "INEP — IDEB/Saeb municipal EM",
                "2023; município/rede pública; planilha de divulgação vintage 2025",
                "IDEB publicado e componentes Saeb; valores de 2025 não foram usados; não foi feita média de escolas.",
            ],
            [
                "INEP — rendimento escolar",
                "2023; município; ensino médio total",
                "Aprovação, reprovação e abandono.",
            ],
            [
                "INEP — distorção idade-série",
                "2023; município; ensino médio total",
                "Percentual de matrículas em distorção.",
            ],
            [
                "INEP — Censo Escolar",
                "2023; escola ativa com IN_MED=1",
                "Internet para alunos e laboratório: proporção simples entre escolas com item observado, todas as redes.",
            ],
            [
                "IBGE — PIB dos Municípios",
                "2023; município; R$ correntes/habitante",
                "PIB per capita mede atividade econômica, não renda familiar.",
            ],
            [
                "IBGE — Censo 2022/SIDRA",
                "2022; município",
                "Renda domiciliar per capita, população e urbanização; defasagem explícita de um ano.",
            ],
        ],
        [120, 135, 256],
        font_size=6.9,
    )
    r.p(
        'Referências oficiais: <a href="https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem">microdados ENEM</a>; <a href="https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/ideb/resultados/2005-2025">resultados IDEB</a>; <a href="https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/taxas-de-distorcao-idade-serie/2023">distorção idade-série</a>; <a href="https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar">Censo Escolar</a>; <a href="https://ftp.ibge.gov.br/Pib_Municipios/2022_2023/base/base_de_dados_2010_2023_txt.zip">PIB municipal</a>. URLs, arquivos, datas e SHA-256 estão no catálogo e nos manifestos do projeto.'
    )
    r.h2("2.2 População observada e elegibilidade")
    r.p(
        "Cada observação representa uma inscrição do ENEM 2023. A população substantiva são concluintes do ensino médio regular em 2023; a população observada é mais estreita: concluintes <i>declarados</i>, ensino regular declarado, não treineiros, presentes em matemática e com nota de matemática numérica, finita e não negativa. Participação no ENEM é voluntária e conclusão efetiva não foi observada."
    )
    r.table(
        ["Etapa cumulativa", "Retidos", "Excluídos nesta etapa"],
        [
            [row.etapa, number(row.n_retido), number(row.n_excluido_etapa)]
            for row in flow.itertuples()
        ],
        [275, 115, 121],
    )
    r.p(
        f"Foram retidas {number(manifest['n_elegivel'])} inscrições. Todas foram processadas: probabilidade de inclusão <i>condicional à elegibilidade</i> π=1 e peso analítico=1. Isso não é a probabilidade de um concluinte brasileiro participar do ENEM. Não houve deduplicação, imputação ou remoção de extremos; {number(manifest['n_mt_zero'])} notas iguais a zero permanecem."
    )
    r.h2("2.3 Variáveis e papel analítico")
    r.table(
        ["Papel", "Variáveis", "Tratamento"],
        [
            [
                "Desfecho",
                "NU_NOTA_MT",
                "Matemática, contínua na escala publicada; principal e isolada.",
            ],
            [
                "Recursos familiares",
                "Q006, Q005, Q024, Q025",
                "Renda em 17 faixas; moradores; computadores; internet. Não converter faixa em renda pontual.",
            ],
            [
                "Capital educacional",
                "Q001, Q002",
                "Escolaridade do pai/responsável e da mãe/responsável; “não sabe” preservado.",
            ],
            [
                "Demografia",
                "TP_COR_RACA, TP_SEXO, TP_FAIXA_ETARIA",
                "Categorias oficiais; códigos não tratados como números contínuos.",
            ],
            [
                "Escola",
                "TP_ESCOLA, TP_DEPENDENCIA_ADM_ESC, TP_LOCALIZACAO_ESC",
                "Tipo, dependência e localização; ausências preservadas.",
            ],
            [
                "Contexto",
                "IDEB, Saeb, fluxo, TDI, PIB, renda, população, urbanização, infraestrutura",
                "Junção muitos-para-um pelo município da escola; ano/rede/unidade mantidos.",
            ],
        ],
        [100, 170, 241],
    )
    r.p(
        "Para apresentação, as 17 faixas de Q006 também foram agrupadas em quatro: A/B (até R$ 1.320), C/D (R$ 1.320,01–2.640), E–H (R$ 2.640,01–6.600) e I–Q (acima de R$ 6.600). A tabela completa conserva as categorias originais. O agrupamento não cria escala contínua."
    )

    r.section("3. Análise descritiva")
    r.h2("3.1 Qualidade, ausências e consistência")
    fields = [
        "TP_COR_RACA",
        "TP_ESCOLA",
        "TP_DEPENDENCIA_ADM_ESC",
        "TP_LOCALIZACAO_ESC",
        "CO_MUNICIPIO_ESC",
        "Q001",
        "Q002",
        "TP_STATUS_REDACAO",
    ]
    q = quality[quality.campo.isin(fields)].set_index("campo").loc[fields]
    r.table(
        ["Campo", "Ausente", "Não declarado/não sabe", "Inválido"],
        [
            [
                idx,
                number(row.n_ausente),
                number(row.n_nao_declarado),
                number(row.n_invalido),
            ]
            for idx, row in q.iterrows()
        ],
        [190, 95, 150, 76],
    )
    r.p(
        f"Não houve código inválido nesses campos. Município, dependência e localização escolar faltam para {number(manifest['n_sem_codigo_municipio'])} candidatos ({pct(100 * manifest['n_sem_codigo_municipio'] / manifest['n_elegivel'], 1)}). Tipo de escola e dependência administrativa discordam em {number(manifest['n_tipo_dependencia_divergente'])} registros; o dado foi sinalizado, não 'corrigido' silenciosamente. Os extremos são candidatos a investigação, não erros automáticos."
    )
    r.figure(
        "04_distribuicao_desfecho.png",
        "Distribuição de matemática na base elegível e dispersão por região escolar.",
        f"Fonte: microdados ENEM 2023. Base integral elegível (n={number(manifest['n_elegivel'])}); para regiões, município/UF escolar observado. Barras regionais: mediana e intervalo interquartil pela EDF inversa; extremos mantidos.",
        245,
    )
    r.p(
        f"A média foi {number(national.media, 1)}, mediana {number(national.mediana, 1)}, variância {number(national.variancia, 1)} e desvio-padrão {number(national.dp, 1)}. O intervalo interquartil foi {number(national.q1, 1)}–{number(national.q3, 1)}; mínimo {number(national['min'], 1)} e máximo {number(national['max'], 1)}. A regra 1,5×IQR marcou {number(national.n_atipicos_iqr)} observações ({pct(national.pct_atipicos_iqr, 2)}), todas preservadas."
    )

    r.h2("3.2 Composição e cinco regiões")
    r.table(
        ["Região escolar", "n", "% dos elegíveis", "Média", "Mediana", "DP"],
        [
            [
                row.regiao,
                number(row.n),
                pct(100 * row.n / manifest["n_elegivel"], 1),
                number(row.media, 1),
                number(row.mediana, 1),
                number(row.dp, 1),
            ]
            for row in pd.concat(
                [known, regions[regions.regiao.eq("Não identificada")]]
            ).itertuples()
        ],
        [120, 80, 95, 72, 72, 72],
    )
    r.figure(
        "01_composicao_regional.png",
        "Composição de renda familiar e raça/cor entre candidatos com região escolar conhecida.",
        "Fonte: microdados ENEM 2023. Percentuais dentro de cada região; renda em quatro grupos de apresentação; categorias de raça/cor mantêm não declaração.",
        280,
    )
    r.p(
        "As médias regionais não devem ser lidas como ranking de qualidade educacional. As composições de renda, raça/cor, escola e escolaridade parental variam entre regiões; além disso, 31,0% dos elegíveis não têm região escolar identificada. A etapa econométrica futura poderá separar associações condicionais, mas não tornará causal um desenho observacional por si só."
    )

    r.h2("3.3 Gradiente de renda familiar")
    income_rows = []
    income_gaps = []
    for region in REGIONS:
        low = group_row(groups, "renda_grupo", "Até R$ 1.320", region)
        high = group_row(groups, "renda_grupo", "Acima de R$ 6.600", region)
        income_gaps.append(high.media - low.media)
        income_rows.append(
            [
                region,
                number(low.media, 1),
                number(high.media, 1),
                number(high.media - low.media, 1),
                number(low.n),
                number(high.n),
            ]
        )
    r.table(
        [
            "Região",
            "Média até R$ 1.320",
            "Média acima R$ 6.600",
            "Diferença",
            "n baixo",
            "n alto",
        ],
        income_rows,
        [90, 102, 110, 70, 70, 69],
        font_size=7.0,
    )
    r.figure(
        "02_renda_regiao.png",
        "Média de matemática por faixa agregada de renda e região escolar.",
        "Fonte: microdados ENEM 2023. Linhas conectam quatro categorias ordenadas apenas para facilitar a leitura; não são regressões nem supõem distância monetária uniforme.",
        280,
    )
    r.p(
        f"No conjunto elegível, {pct(income_low.pct, 1)} estavam até R$ 1.320 e {pct(income_high.pct, 1)} acima de R$ 6.600. O gradiente é monotônico nos quatro grupos e aparece nas cinco regiões. A diferença entre extremos variou de aproximadamente {number(min(income_gaps), 1)} a {number(max(income_gaps), 1)} pontos; continua sendo diferença bruta, sujeita à composição."
    )

    r.h2("3.4 Escolaridade parental e tipo de escola")
    r.figure(
        "03_parental_regiao.png",
        "Média de matemática segundo escolaridade declarada dos responsáveis, por região.",
        "Fonte: microdados ENEM 2023. Categorias A–H do questionário; “não sabe” é categoria substantiva, não ausência numérica. Nenhuma escolaridade foi convertida em anos.",
        310,
    )
    r.table(
        ["Grupo", "n", "%", "Média", "Mediana", "DP"],
        [
            [
                "Escola pública",
                number(public.n),
                pct(public.pct, 1),
                number(public.media, 1),
                number(public.mediana, 1),
                number(public.dp, 1),
            ],
            [
                "Escola privada",
                number(private.n),
                pct(private.pct, 1),
                number(private.media, 1),
                number(private.mediana, 1),
                number(private.dp, 1),
            ],
            [
                "Diferença privada–pública",
                "—",
                "—",
                number(private.media - public.media, 1),
                "—",
                "—",
            ],
        ],
        [150, 85, 70, 70, 70, 66],
    )
    r.p(
        "A escolaridade parental exibe gradiente ordenado, com exceções possíveis entre categorias próximas e heterogeneidade regional. Escola privada apresenta média 125,6 pontos maior que pública. Essa diferença resume grupos com perfis econômicos e escolares muito diferentes; não estima efeito de trocar um candidato de rede. Computador e internet também podem funcionar como marcadores de recursos e como mecanismos, questão a ser explicitada na modelagem futura."
    )

    r.section("3.5 Contexto municipal e associações ecológicas", break_page=False)
    r.p(
        f"O vínculo escolar identificou {number(manifest['n_vinculado'])} candidatos em 5.475 municípios. A base municipal contém contagem, média, mediana, variância populacional (ddof=0), desvio-padrão, quartis, extremos e composições. O corte principal n≥30 reteve {number(sensitivity.loc[sensitivity.n_min.eq(30), 'n_municipios'].iloc[0])} municípios e {number(sensitivity.loc[sensitivity.n_min.eq(30), 'n_candidatos'].iloc[0])} candidatos — {pct(sensitivity.loc[sensitivity.n_min.eq(30), 'pct_vinculados'].iloc[0], 1)} dos vinculados."
    )
    r.figure(
        "05_contexto_regional.png",
        "Distribuições municipais de IDEB, PIB per capita, renda per capita e distorção idade-série.",
        "Fontes: INEP e IBGE. Municípios com n≥30 candidatos; cada município tem o mesmo peso. Caixas usam quartis pela EDF inversa e regra 1,5×IQR; PIB em escala logarítmica; extremos não removidos.",
        335,
    )
    r.story.append(PageBreak())
    r.h2("IDEB/Saeb: contexto público, não nota individual")
    r.figure(
        "06_ideb_nacional.png",
        "IDEB municipal público e média de matemática: todos os vinculados e domínio de escolas públicas.",
        "Fontes: ENEM 2023 e IDEB 2023 publicado pelo INEP (planilha vintage 2025, somente referência 2023). Municípios n≥30 no respectivo domínio. Tamanho dos círculos indica n apenas visualmente; LOWESS é descritiva, sem extrapolação ou inferência.",
        260,
    )
    r.figure(
        "07_ideb_regioes.png",
        "IDEB municipal público e média de matemática, separadamente nas cinco regiões.",
        "Fontes: ENEM 2023 e INEP/IDEB 2023. Municípios com n≥30 candidatos; igual peso municipal nos painéis. Curvas LOWESS apenas guiam a forma observada.",
        330,
    )
    ideb = assoc[assoc.n_min.eq(30) & assoc.indicador.eq("ideb_2023")]
    r.table(
        [
            "Região",
            "Domínio dos candidatos",
            "Municípios",
            "Pearson",
            "Spearman",
            "Pearson ponderado por n",
        ],
        [
            [
                row.regiao,
                row.rede_candidatos,
                number(row.n_pares),
                number(row.pearson, 3),
                number(row.spearman, 3),
                number(row.pearson_ponderado_n, 3),
            ]
            for row in ideb[ideb.regiao.isin(["Brasil", *REGIONS])].itertuples()
        ],
        [82, 115, 70, 70, 74, 100],
        font_size=6.8,
    )
    r.p(
        "No corte principal, a correlação nacional IDEB–média municipal foi 0,337 (Pearson) e 0,337 (Spearman) com igual peso municipal, mas 0,023 quando ponderada pelo número de candidatos. No domínio público, os valores foram 0,439, 0,431 e 0,212. A variação por região é substantiva: no Sul a associação ficou próxima de zero, enquanto no Norte foi mais forte. Portanto, não há base para resumir o IDEB por um único coeficiente supostamente universal."
    )

    r.h2("Economia municipal")
    r.figure(
        "08_economia_municipal.png",
        "PIB per capita de 2023, renda domiciliar per capita de 2022 e média municipal de matemática.",
        "Fontes: ENEM 2023 e IBGE. Municípios n≥30; igual peso municipal; PIB no eixo log; LOWESS descritiva. Renda municipal é domiciliar per capita e não equivale a Q006, renda familiar em faixas.",
        255,
    )
    r.figure(
        "09_economia_regioes.png",
        "Formas regionais das associações entre contexto econômico e média municipal de matemática.",
        "Fontes: ENEM 2023 e IBGE. LOWESS dentro do suporte observado em cada região; sem reta OLS, teste ou ajuste por composição.",
        255,
    )
    selected_indicators = [
        "ideb_2023",
        "saeb_mt_2023",
        "pib_pc_2023",
        "renda_pc_2022",
        "distorcao_2023",
        "urbanizacao_2022",
        "internet_escolas_pct",
        "laboratorio_escolas_pct",
    ]
    national_assoc = (
        assoc[
            assoc.n_min.eq(30)
            & assoc.regiao.eq("Brasil")
            & assoc.rede_candidatos.eq("Todas")
            & assoc.indicador.isin(selected_indicators)
        ]
        .set_index("indicador")
        .loc[selected_indicators]
    )
    r.table(
        ["Indicador", "Pares", "Pearson", "Spearman", "Pearson pond. n"],
        [
            [
                INDICATORS[idx],
                number(row.n_pares),
                number(row.pearson, 3),
                number(row.spearman, 3),
                number(row.pearson_ponderado_n, 3),
            ]
            for idx, row in national_assoc.iterrows()
        ],
        [225, 65, 70, 75, 76],
        font_size=7.0,
    )
    r.p(
        "A renda domiciliar per capita apresentou a associação mais alta entre os indicadores econômicos selecionados (Pearson 0,735; Spearman 0,765; Pearson ponderado 0,780). PIB per capita foi mais sensível à medida: Pearson 0,301 e Spearman 0,591, coerente com assimetria e valores extremos. Distorção idade-série foi negativamente associada. Infraestrutura simples mostrou correlações pequenas e sensíveis à ponderação; sua medida por proporção de escolas não descreve o acesso de cada candidato."
    )
    r.h2("Quintis municipais com cortes nacionais fixos")
    r.figure(
        "10_quintis_contextuais.png",
        "Média dos candidatos por quintil municipal nacional, dentro de cada região.",
        "Fontes: ENEM 2023, INEP e IBGE. Cortes calculados entre municípios n≥30, iguais para as regiões, por EDF inversa; empates permanecem juntos. Médias no eixo vertical dão peso igual aos candidatos vinculados a cada quintil.",
        255,
    )
    r.table(
        ["Indicador", "Cortes nacionais Q20 / Q40 / Q60 / Q80", "Municípios"],
        [
            [
                INDICATORS[name],
                " / ".join(number(value, 2) for value in detail["cortes"]),
                number(detail["n_municipios"]),
            ]
            for name, detail in cuts.items()
        ],
        [190, 235, 86],
    )
    r.p(
        "Os quintis são uma discretização descritiva do contexto, não faixas individuais. Como os cortes são nacionais, algumas regiões concentram-se em certos quintis; grupos eventualmente vazios não foram preenchidos. O padrão de renda municipal é mais regular que o de IDEB, mas ambos ainda misturam composição individual e contexto."
    )

    r.section("3.6 Cobertura, sensibilidade e robustez")
    r.h2("Seleção pela disponibilidade do município escolar")
    r.figure(
        "11_selecao_cobertura.png",
        "Composição de renda e tipo de escola segundo disponibilidade do município escolar.",
        "Fonte: microdados ENEM 2023. Percentuais calculados separadamente entre município conhecido e ausente/não vinculado.",
        270,
    )
    r.table(
        ["Domínio", "n", "% base", "Média MT", "Mediana MT", "DP MT"],
        [
            [
                "Município conhecido",
                number(known_score.n),
                pct(100 * known_score.n / manifest["n_elegivel"], 1),
                number(known_score.media, 1),
                number(known_score.mediana, 1),
                number(known_score.dp, 1),
            ],
            [
                "Município ausente/não vinculado",
                number(missing_score.n),
                pct(100 * missing_score.n / manifest["n_elegivel"], 1),
                number(missing_score.media, 1),
                number(missing_score.mediana, 1),
                number(missing_score.dp, 1),
            ],
            [
                "Diferença conhecido–ausente",
                "—",
                "—",
                number(known_score.media - missing_score.media, 1),
                "—",
                "—",
            ],
        ],
        [185, 85, 75, 65, 65, 66],
    )
    r.p(
        "Candidatos vinculados têm média 51,9 pontos maior. Entre vinculados, 29,6% estão na faixa de renda mais baixa e 18,3% na mais alta; entre não vinculados, 45,3% e 5,2%, respectivamente. Escola pública representa 72,7% dos vinculados e 91,6% dos não vinculados. Logo, análises territoriais descrevem um subconjunto socialmente selecionado e não podem ser generalizadas automaticamente aos 1.027.924 elegíveis."
    )
    r.h2("Cobertura dos indicadores")
    r.table(
        ["Indicador", "Candidatos cobertos", "% dos elegíveis", "Municípios"],
        [
            [
                INDICATORS[row.indicador],
                number(row.n_observado),
                pct(row.pct_coberto, 1),
                number(row.municipios_observados),
            ]
            for row in coverage.itertuples()
        ],
        [235, 105, 85, 86],
        font_size=6.9,
    )
    r.p(
        "IDEB e Saeb cobrem menos candidatos que as variáveis do IBGE porque o indicador público não é divulgado para todos os municípios. A nota técnica do IDEB exige participação mínima e outros critérios de divulgação. Ausência de indicador restringe apenas sua análise; não foi transformada em zero e não excluiu o candidato da descrição individual."
    )
    r.h2("Cortes municipais e outras áreas")
    r.table(
        [
            "Mínimo de candidatos",
            "Municípios",
            "Candidatos",
            "% vinculados",
            "% elegíveis",
        ],
        [
            [
                number(row.n_min),
                number(row.n_municipios),
                number(row.n_candidatos),
                pct(row.pct_vinculados, 1),
                pct(row.pct_elegiveis, 1),
            ]
            for row in sensitivity.itertuples()
        ],
        [120, 95, 95, 100, 101],
    )
    rb = robust[
        robust.regiao.eq("Brasil")
        & robust.renda_grupo.isin(["Até R$ 1.320", "Acima de R$ 6.600"])
    ]
    rb_low = rb[rb.renda_grupo.eq("Até R$ 1.320")].set_index("area")
    rb_high = rb[rb.renda_grupo.eq("Acima de R$ 6.600")].set_index("area")
    area_names = {
        "MT": "Matemática",
        "CN": "Ciências da Natureza",
        "CH": "Ciências Humanas",
        "LC": "Linguagens",
        "REDACAO": "Redação",
    }
    r.table(
        [
            "Área",
            "n renda baixa",
            "Média baixa",
            "n renda alta",
            "Média alta",
            "Diferença",
        ],
        [
            [
                area_names[area],
                number(rb_low.loc[area, "n"]),
                number(rb_low.loc[area, "media"], 1),
                number(rb_high.loc[area, "n"]),
                number(rb_high.loc[area, "media"], 1),
                number(rb_high.loc[area, "media"] - rb_low.loc[area, "media"], 1),
            ]
            for area in area_names
        ],
        [125, 82, 72, 82, 72, 78],
        font_size=7.0,
    )
    r.p(
        "O gradiente de renda também aparece nas outras áreas, cada uma em seu domínio de presença/nota e, para redação, status regular. As escalas não foram comparadas entre si e nenhuma nota foi usada para explicar outra. Essas tabelas são robustez descritiva, não um desfecho composto."
    )

    r.section("4. Conclusões e encaminhamento inferencial")
    r.p(
        "A análise identifica desigualdades descritivas grandes e sistemáticas. Renda familiar, escolaridade parental e tipo de escola discriminam fortemente a distribuição de matemática. As cinco regiões têm composições distintas e os gradientes não possuem exatamente a mesma amplitude. No nível municipal, renda domiciliar, urbanização, Saeb, IDEB e distorção idade-série covariam com a média dos candidatos, porém a intensidade depende da região, do domínio e de dar peso igual aos municípios ou aos candidatos."
    )
    r.table(
        ["Achado", "Leitura permitida", "Leitura não permitida"],
        [
            [
                "Renda familiar: +173,2 pontos entre grupos extremos",
                "Diferença bruta importante no cadastro elegível.",
                "Efeito causal da renda ou valor esperado após ajuste.",
            ],
            [
                "Privada–pública: +125,6 pontos",
                "Grupos observados diferem amplamente.",
                "Efeito de matrícula privada.",
            ],
            [
                "Renda municipal: r=0,735",
                "Municípios economicamente distintos também diferem nas médias ENEM observadas.",
                "Efeito individual da renda municipal.",
            ],
            [
                "IDEB varia por região/ponderação",
                "Heterogeneidade e escolha do estimando importam.",
                "Coeficiente nacional universal ou impacto do IDEB.",
            ],
            [
                "31,0% sem município",
                "Cobertura territorial é seletiva e mensurável.",
                "Generalização automática do subconjunto vinculado.",
            ],
        ],
        [140, 185, 186],
        font_size=6.9,
    )
    r.h2("Limitações")
    r.p(
        "O ENEM não é censo obrigatório de concluintes; conclusão é autodeclarada; município é o da escola e falta para parcela expressiva; contexto municipal não mede o domicílio nem a experiência de cada estudante; variáveis do Censo 2022 têm defasagem de um ano; IDEB é da rede pública; infraestrutura é proporção de escolas; respostas socioeconômicas podem conter erro; e as correlações municipais sofrem falácia ecológica. A PNAD disponível não identifica com exatidão o mesmo universo de concluintes e não foi usada para forçar calibração."
    )
    r.h2("Como esta etapa orienta a econometria futura")
    r.p(
        "Após revisão dos autores, a etapa inferencial deve pré-especificar estimando e blocos: (1) renda e capital educacional familiar; (2) demografia; (3) escola; (4) contexto municipal; (5) interações regionais justificadas. Deve considerar dependência de candidatos dentro de municípios, forma funcional, heterocedasticidade, multicolinearidade, influência, seleção pela cobertura e análises de sensibilidade n≥20/30/50. Recursos como computador e internet podem ser mediadores da renda e não devem entrar mecanicamente. IDEB, Saeb e fluxo compartilham construção/conteúdo e exigem cautela de especificação. Nenhuma dessas decisões econométricas foi executada neste relatório."
    )
    r.p(
        "Os resultados atuais fornecem magnitudes, distribuições, domínios e sinais para formular hipóteses e escolher modelos; não substituem intervalos, testes ou estimativas ajustadas. A próxima etapa deve ser iniciada somente após aprovação deste relatório descritivo e registro de uma nova decisão metodológica."
    )

    r.section("Apêndice A — população, base, amostra e pesos")
    r.p(
        "A tabela solicitada de alvo/base/amostra foi preservada integralmente em <b>representacao_populacoes.csv</b>. Abaixo, a síntese por dimensão. Como não existe nesta entrega uma referência externa com conceito idêntico — concluintes efetivos do ensino médio regular em 2023, nas mesmas categorias e com município da escola — as colunas de alvo permanecem ausentes em vez de receber uma proxy incompatível."
    )
    r.table(
        [
            "Dimensão",
            "Categorias",
            "Alvo externo exato",
            "Base elegível",
            "Amostra bruta",
            "Peso",
        ],
        [
            [
                "Região escolar",
                "5 regiões + não identificada",
                "Não disponível de modo comparável",
                number(manifest["n_elegivel"]),
                number(manifest["n_elegivel"]),
                "1",
            ],
            [
                "Raça/cor",
                "6 categorias observadas",
                "Não disponível de modo comparável",
                number(manifest["n_elegivel"]),
                number(manifest["n_elegivel"]),
                "1",
            ],
            [
                "Sexo",
                "Feminino, masculino",
                "Não disponível de modo comparável",
                number(manifest["n_elegivel"]),
                number(manifest["n_elegivel"]),
                "1",
            ],
            [
                "Renda familiar",
                "17 faixas Q006",
                "Não disponível; PNAD mede outro conceito",
                number(manifest["n_elegivel"]),
                number(manifest["n_elegivel"]),
                "1",
            ],
        ],
        [105, 120, 145, 70, 70, 45],
        font_size=6.9,
    )
    r.p(
        "Em todas as linhas do arquivo completo: amostra bruta=base elegível, amostra ponderada=base elegível, π condicional=1 e peso=1. Não se atribuiu margem de erro amostral ao processamento integral. A incerteza relevante inclui seleção para o ENEM, mensuração, cobertura territorial e, futuramente, variação estatística do modelo/estimando."
    )
    r.h2("Proxy PNAD, somente como referência contextual")
    r.table(
        ["Dimensão", "Categoria", "n PNAD", "Total expandido", "% proxy"],
        [
            [
                row.dimensao,
                row.categoria,
                number(row.n_pnad),
                number(row.total_proxy),
                pct(row.pct_proxy, 1),
            ]
            for row in pnad.itertuples()
        ],
        [85, 105, 75, 135, 80],
    )
    r.p(
        "Universo da proxy: estudantes que frequentavam ensino médio regular nas séries 3/4 na PNAD Contínua, não concluintes comprovados. Região de residência não substitui região da escola e renda domiciliar não substitui Q006. A incerteza complexa da PNAD não foi propagada. Portanto, a proxy não foi alvo de calibração e não transforma os elegíveis do ENEM em amostra representativa de todos os concluintes brasileiros."
    )

    r.section("Apêndice B — reprodutibilidade e auditoria")
    r.table(
        ["Produto", "Local/resultado"],
        [
            ["Decisão vigente", "docs/decisions/006-reconstrucao-enem-2023.md"],
            [
                "Base individual derivada",
                "data/processed/territorial_2023/candidatos_2023.parquet",
            ],
            [
                "Base municipal derivada",
                "data/processed/territorial_2023/municipios_2023.parquet/csv",
            ],
            ["Tabelas do relatório", "reports/tables/territorial_2023/; CSVs analíticos em data/processed/territorial_2023/"],
            [
                "Código",
                "territorial_context.py; territorial_analysis.py; territorial_figures.py; territorial_report.py",
            ],
            [
                "Validação",
                f"{validation['checagens']} verificações aprovadas; data/processed/territorial_2023/validacao.json",
            ],
        ],
        [150, 361],
    )
    r.p(
        "A cadeia é raw → clean/processed → análise → relatório. Arquivos raw permaneceram imutáveis. O rótulo de origem ‘Centro-oeste’ foi padronizado para ‘Centro-Oeste’ e validado contra o conjunto fechado de cinco regiões; nenhuma observação foi alterada ou realocada. Junções foram validadas como muitos-para-um e não aumentaram o número de candidatos."
    )
    r.table(
        ["Hash/versão", "Valor"],
        [
            ["Parquet ENEM 2023 de entrada", manifest["input_sha256"]],
            ["Contexto municipal derivado", manifest["context_sha256"]],
            ["Base individual desta análise", validation["hash_candidatos"]],
            ["Base municipal desta análise", validation["hash_municipios"]],
            ["Python", manifest["python"]],
            [
                "Bibliotecas",
                "; ".join(
                    f"{key} {value}" for key, value in manifest["versions"].items()
                ),
            ],
        ],
        [155, 356],
        font_size=6.4,
    )
    r.p(
        "Notas de método: variância descritiva calculada com ddof=0; quartis pela EDF inversa; atípicos pela regra 1,5×IQR e preservados; Spearman com postos médios nos empates; pares completos por indicador; quintis nacionais com empates mantidos; LOWESS com fração 0,6, sem iterações robustas, apenas guia visual. Correlações principais atribuem igual peso a cada município; ponderação por n é sensibilidade e responde a outro estimando."
    )
    r.p(
        "Aquisição: o servidor download.inep.gov.br reiniciou conexões TLS neste ambiente; os mesmos caminhos oficiais foram obtidos por HTTP e verificados por CRC/SHA-256, com data e rota registradas. Essa limitação de transporte consta no catálogo; a proveniência institucional e as páginas oficiais de referência estão preservadas."
    )
    r.build()
    audit = {
        "pdf": str(PDF.relative_to(ROOT)),
        "pages": len(pymupdf.open(PDF)),
        "sha256": sha256(PDF),
        "figures": 11,
        "validation_checks": validation["checagens"],
        "econometric_models": 0,
    }
    write_json(OUT / "relatorio_manifest.json", audit)
    print(
        f"Relatório: {PDF}; {audit['pages']} páginas; SHA-256 {audit['sha256']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
