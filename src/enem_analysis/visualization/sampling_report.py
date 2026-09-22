"""Auditable Portuguese sampling report, with computed tables and CSV attachments."""
# Long narrative strings are deliberately kept as editable report prose.
# ruff: noqa: E501

from __future__ import annotations

import importlib.metadata
import json
import platform
from html import escape
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import pymupdf as fitz
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from enem_analysis.data.acquire import ROOT, sha256, write_json
from enem_analysis.data.sampling_plan import OUT, dictionary
from enem_analysis.visualization.report_assets import save_table_csv

REPORT = ROOT / "reports/report/variaveis_plano_amostral_chang.pdf"
TABLES = ROOT / "reports/tables/sampling"
MUNICIPAL = {
    "pib_per_capita_reais": "Atividade econômica por habitante; não renda das famílias",
    "educ_abandono_medio_pct": "Fragilidade do fluxo escolar no ensino médio",
    "populacao": "Porte municipal; controle de escala e urbanização imperfeito",
    "renda_per_capita_atlas_reais2010": "Recursos domiciliares, referência censitária 2010",
    "renda_domiciliar_per_capita_censo2022_reais": "Recursos domiciliares, referência censitária 2022",
    "gini_atlas": "Desigualdade de renda, não nível médio de renda",
    "idhm_educacao": "Ambiente educacional; alternativa ao IDHM total",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def number(value, digits=0):
    if value is None or pd.isna(value):
        return "—"
    return (
        f"{float(value):,.{digits}f}".replace(",", "_")
        .replace(".", ",")
        .replace("_", ".")
    )


def audit_products() -> dict:
    """Check every selected group and weight, and compute descriptive diagnostics."""
    plans = [read_json(OUT / f"plano_{y}.json") for y in range(2010, 2024)]
    calibrations = read_json(OUT / "calibracao_resumo.json")
    checks, sensitivities, aggregates = [], [], []
    for plan in plans:
        year = plan["year"]
        s = pd.read_parquet(OUT / f"amostra_com_pesos_{year}.parquet")
        g = pd.read_csv(OUT / f"alocacao_{year}.csv")
        actual = s.groupby("estrato").size().sort_index()
        expected = g.set_index("estrato").n_h.sort_index()
        assert actual.equals(expected.rename(None)) or np.array_equal(actual, expected)
        assert list(actual.index) == list(expected.index)
        assert len(s) == plan["n_selected"] == 20000
        assert not s.NU_INSCRICAO.duplicated().any()
        assert g.N_h.sum() == plan["N_eligible"]
        assert np.allclose(s.pi_h, s.n_h / s.N_h)
        assert s.pi_h.gt(0).all() and s.pi_h.le(1).all()
        assert np.allclose(s.peso_desenho * s.pi_h, 1)
        assert np.isclose(s.peso_desenho.sum(), plan["N_eligible"])
        assert set(s.sexo) <= {"F", "M"}
        race_codes = {
            str(c["code"]): str(c["label"]).strip()
            for c in dictionary(year)[0]["TP_COR_RACA"]["categories"]
        }
        assert [race_codes[str(i)] for i in range(1, 6)] == [
            "Branca",
            "Preta",
            "Parda",
            "Amarela",
            "Indígena",
        ]
        for name in ["raca", "sexo", "regiao_escola", "renda_categoria", "escola"]:
            part = (
                s.groupby(name)
                .agg(
                    n_selecionado=("peso_desenho", "size"),
                    total_desenho=("peso_desenho", "sum"),
                )
                .reset_index()
                .rename(columns={name: "categoria"})
            )
            part["variavel"] = name
            part["ano"] = year
            aggregates.append(part)
        if year >= 2012:
            c = next(c for c in calibrations if c["year"] == year)
            calibrated = s.peso_calibrado_proxy.dropna()
            assert np.isfinite(calibrated).all() and calibrated.gt(0).all()
            assert np.isclose(calibrated.sum(), c["calibration_target_scale"])
            residual = pd.read_csv(OUT / f"residuos_calibracao_{year}.csv")
            assert residual.residuo.abs().max() / c["calibration_target_scale"] < 1.1e-9
            p = pd.read_parquet(OUT / f"pnad_proxy_{year}.parquet")
            third = p[p.V3006.eq("03")]
            diffs = []
            for dimension in ["raca", "sexo", "regiao"]:
                full = p.groupby(dimension).weight.sum() / p.weight.sum()
                only = third.groupby(dimension).weight.sum() / third.weight.sum()
                diffs.extend(
                    (full - only.reindex(full.index, fill_value=0)).abs().tolist()
                )
            sensitivities.append(
                {
                    "ano": year,
                    "n_pnad": len(p),
                    "total_proxy": p.weight.sum(),
                    "proporcao_serie4": p.loc[p.V3006.eq("04"), "weight"].sum()
                    / p.weight.sum(),
                    "maior_delta_margens_pp_serie3_vs_3e4": 100 * max(diffs),
                }
            )
        checks.append({"ano": year, "validado": True, "n": len(s)})
    pd.DataFrame(sensitivities).to_csv(OUT / "sensibilidade_proxy.csv", index=False)
    pd.concat(aggregates).to_csv(
        OUT / "alocacao_por_caracteristica.csv", index=False, encoding="utf-8-sig"
    )
    pd.concat(
        [pd.read_csv(OUT / f"margens_ibge_{y}.csv") for y in range(2012, 2024)]
    ).to_csv(OUT / "margens_ibge_todos_anos.csv", index=False, encoding="utf-8-sig")
    flows = [{"ano": p["year"], **row} for p in plans for row in p["flow"]]
    pd.DataFrame(flows).to_csv(OUT / "fluxo_elegibilidade.csv", index=False)
    mapping = [
        {
            "ano": p["year"],
            "papel": role,
            "coluna": detail["csv"],
            "descricao": detail["description"],
        }
        for p in plans
        for role, detail in p["question_mapping"].items()
    ]
    pd.DataFrame(mapping).to_csv(
        OUT / "mapa_variaveis_enem.csv", index=False, encoding="utf-8-sig"
    )
    m = pd.read_parquet(ROOT / "data/processed/municipal/base_municipio_ano.parquet")
    coverage = []
    for name in MUNICIPAL:
        for year, group in m.groupby("ano_enem"):
            values = pd.to_numeric(group[name], errors="raise")
            coverage.append(
                {
                    "variavel": name,
                    "ano": year,
                    "municipios": len(group),
                    "observados": int(values.notna().sum()),
                    "minimo": values.min(),
                    "mediana": values.median(),
                    "maximo": values.max(),
                }
            )
    pd.DataFrame(coverage).to_csv(
        OUT / "cobertura_municipal_selecionada.csv", index=False
    )
    baseline = m[m.ano_enem.eq(2010)]
    pairs = []
    names = [
        "renda_per_capita_atlas_reais2010",
        "gini_atlas",
        "idhm_educacao",
        "pib_per_capita_reais",
    ]
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            pair = baseline[[a, b]].dropna().astype(float)
            pairs.append(
                {
                    "variavel_a": a,
                    "variavel_b": b,
                    "n_pares": len(pair),
                    "spearman_descritivo": pair.corr(method="spearman").iloc[0, 1],
                }
            )
    pd.DataFrame(pairs).to_csv(OUT / "redundancia_municipal_2010.csv", index=False)
    versions = {
        name: importlib.metadata.version(name)
        for name in [
            "numpy",
            "pandas",
            "pyarrow",
            "duckdb",
            "scipy",
            "reportlab",
            "pymupdf",
        ]
    }
    result = {
        "checks": checks,
        "python": platform.python_version(),
        "libraries": versions,
        "all_passed": True,
        "rows": sum(c["n"] for c in checks),
        "sample_sha256": sha256(OUT / "amostra_enem_2010_2023.parquet"),
    }
    write_json(OUT / "validacao_amostra.json", result)
    return result


class Report:
    def __init__(self, table_directory: Path | None = None):
        font_dir = Path(matplotlib.get_data_path()) / "fonts/ttf"
        pdfmetrics.registerFont(TTFont("DejaVu", str(font_dir / "DejaVuSans.ttf")))
        pdfmetrics.registerFont(
            TTFont("DejaVu-Bold", str(font_dir / "DejaVuSans-Bold.ttf"))
        )
        pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold")
        self.styles = getSampleStyleSheet()
        for name in ["Normal", "BodyText", "Title", "Heading1", "Heading2"]:
            self.styles[name].fontName = "DejaVu"
        self.styles["BodyText"].fontSize = 9
        self.styles["BodyText"].leading = 13
        self.styles["BodyText"].spaceAfter = 8
        self.styles["Heading1"].fontSize = 17
        self.styles["Heading1"].leading = 21
        self.styles["Heading1"].textColor = colors.HexColor("#17394A")
        self.styles.add(
            ParagraphStyle(
                "Cell", fontName="DejaVu", fontSize=7.4, leading=10, alignment=TA_LEFT
            )
        )
        self.story = []
        self.table_number = 0
        self.table_directory = table_directory

    def heading(self, title):
        if self.story:
            self.story.append(PageBreak())
        self.story.append(Paragraph(title, self.styles["Heading1"]))
        self.story.append(Spacer(1, 9))

    def p(self, text):
        self.story.append(Paragraph(text, self.styles["BodyText"]))

    def table(self, headers, rows, widths=None):
        self.table_number += 1
        if self.table_directory is not None:
            save_table_csv(self.table_directory, self.table_number, headers, rows)
        contents = [
            [
                Paragraph(escape(str(x)).replace("\n", "<br/>"), self.styles["Cell"])
                for x in row
            ]
            for row in [headers, *rows]
        ]
        t = Table(contents, colWidths=widths, repeatRows=1, hAlign="LEFT")
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DFEAF0")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
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
        self.story.extend([t, Spacer(1, 10)])

    def build(self):
        def footer(canvas, doc):
            canvas.setFont("DejaVu", 7)
            canvas.setFillColor(colors.HexColor("#52626A"))
            canvas.drawString(
                42, 25, "ENEM | Plano operacional e limitações | 20/09/2026"
            )
            canvas.drawRightString(A4[0] - 42, 25, str(doc.page))

        REPORT.parent.mkdir(parents=True, exist_ok=True)
        SimpleDocTemplate(
            str(REPORT),
            pagesize=A4,
            rightMargin=42,
            leftMargin=42,
            topMargin=40,
            bottomMargin=43,
            title="Variáveis e plano amostral — ENEM / Chang (2)",
            author="Projeto ENEM — documentação reprodutível",
        ).build(self.story, onFirstPage=footer, onLaterPages=footer)


def main():
    validation = audit_products()
    plans = [read_json(OUT / f"plano_{y}.json") for y in range(2010, 2024)]
    cs = read_json(OUT / "calibracao_resumo.json")
    calibrated = [c for c in cs if c["external_calibration"]]
    r = Report(table_directory=TABLES)
    r.heading("Variáveis e plano amostral<br/>ENEM 2010–2023")
    r.p(
        "<b>Leitura da proposta Chang (2), escolha de variáveis, amostragem estratificada e calibração parcial.</b> "
        "Documento técnico com cálculos executados sobre as bases locais e referências oficiais. "
        "Estado acadêmico: <b>2º estado — Relatório Descritivo em elaboração. Somente a Proposta foi concluída.</b>"
    )
    r.p(
        "A população de referência escolhida pelo autor é a de <b>estudantes concluintes do ensino médio em cada ano</b>. "
        "Esse universo não é a população brasileira inteira. A PNAD disponível identifica alunos nas séries finais, "
        "não a conclusão efetiva: seus totais são uma <b>proxy de potenciais concluintes</b>. "
        "Os pesos externos entregues são experimentais e não resolvem essa diferença de definição."
    )
    r.table(
        ["Pergunta", "Resposta operacional"],
        [
            [
                "Que variáveis priorizar?",
                "Renda familiar, escolaridade dos pais, raça/cor, sexo, idade, escola e recursos de estudo; contexto municipal em bloco separado.",
            ],
            [
                "Qual amostra?",
                "20.000 inscrições por edição, 280.000 no total; sorteio estratificado sem reposição.",
            ],
            [
                "Qual calibração externa?",
                "2012–2023: raça × sexo e idade ampla da proxy PNAD; mantém região da escola × renda ENEM como margem interna.",
            ],
            [
                "O que não foi garantido?",
                "Representatividade nacional de concluintes, distribuição conjunta externa completa e calibração 2010/2011.",
            ],
            [
                "Há determinantes comprovados?",
                "Não. Há hipóteses e variáveis candidatas; nenhum modelo de desempenho ou teste causal foi estimado nesta entrega.",
            ],
        ],
        [125, 386],
    )
    r.p(
        "As escolhas estão registradas na decisão 004, que atualiza o adiamento de amostra da decisão 003. "
        "Os dados brutos e os Parquets integrais não foram alterados. As tabelas completas de alocação e margens "
        "estão anexadas eletronicamente a este PDF e também em data/processed/sampling/."
    )

    r.heading("1. Pergunta, unidade e alcance")
    r.p(
        "A proposta Chang (2), especialmente pp. 5–8, relaciona desempenho, condições familiares, trajetória "
        "escolar e contexto territorial. Para comparar candidatos, a unidade adotada nesta entrega é "
        "<b>inscrição × edição do ENEM</b>. O painel município × ano continua sendo uma base contextual auxiliar. "
        "Não se presume que inscrições de anos diferentes identifiquem a mesma pessoa."
    )
    r.p(
        "Pergunta operacional: entre participantes que declaram concluir o ensino médio regular no ano e "
        "satisfazem os critérios de prova, quais características individuais e escolares estão associadas às "
        "diferenças de notas? Quando o município da escola estiver disponível, seu contexto acrescenta informação "
        "às características familiares? A pergunta sobre <b>município de residência</b> continua inviável nos arquivos locais."
    )
    r.table(
        ["População/estimando", "Definição e limite"],
        [
            [
                "Alvo substantivo",
                "Concluintes do ensino médio em cada ano; a operação atual restringe-se ao regular. EJA não está representada.",
            ],
            [
                "Cadastro observado",
                "Concluintes declarados no ENEM, ensino regular, presentes nas quatro áreas, cinco notas numéricas e redação regular.",
            ],
            [
                "Referência externa",
                "PNADC: frequenta ensino médio regular, série 3 ou 4. Não comprova diploma; série 3 pode não ser terminal em curso de quatro anos.",
            ],
            [
                "Estimando descritivo primário",
                "Médias e distribuições por área dentro do cadastro elegível anual, usando pesos de desenho.",
            ],
            [
                "Estimando secundário",
                "Distribuições/associações padronizadas às margens demográficas da proxy PNAD no domínio de raça e sexo conhecidos.",
            ],
            [
                "Sem identificação causal",
                "Diferenças observadas não são efeitos de raça, escola, renda ou território. Seleção, confundimento e temporalidade permanecem.",
            ],
        ],
        [132, 379],
    )
    r.p(
        "O ingresso no ENEM é voluntário. A probabilidade de um concluinte brasileiro entrar no ENEM é "
        "desconhecida. A calibração aproxima características observadas, mas não corrige automaticamente "
        "diferenças não observadas, ausência às provas ou seleção pela validade da redação."
    )

    r.heading("2. Variáveis individuais prioritárias")
    r.p(
        "Os códigos abaixo referem-se a <b>2023</b>; a seção seguinte mostra alterações históricas. "
        "Prioridade é teórica, não um ranking já demonstrado pelos dados. Não tratar códigos de categorias como números contínuos."
    )
    r.table(
        ["Papel", "Colunas", "Razão e cautela"],
        [
            [
                "Desfechos",
                "NU_NOTA_CN, NU_NOTA_CH, NU_NOTA_LC, NU_NOTA_MT, NU_NOTA_REDACAO",
                "Analisar separadamente as cinco dimensões. Não criar média geral com pesos arbitrários nem comparar áreas como escalas idênticas.",
            ],
            [
                "Recursos familiares",
                "Q006; Q005",
                "Renda familiar em faixas e moradores. Faixa não é renda pontual. Renda familiar / moradores não é automaticamente renda domiciliar per capita exata.",
            ],
            [
                "Capital educacional",
                "Q001; Q002",
                "Escolaridade do pai/responsável e mãe/responsável. Incluir ambos; não sei é categoria distinta, nunca zero escolaridade.",
            ],
            [
                "Desigualdade social",
                "TP_COR_RACA; TP_SEXO",
                "Raça/cor e sexo registrado permitem descrever desigualdades e interações. Não interpretar associação como capacidade inata.",
            ],
            [
                "Idade/trajetória",
                "TP_FAIXA_ETARIA",
                "Faixas etárias captam heterogeneidade e atraso escolar imperfeitamente. Não atribuir idade exata ao ponto médio.",
            ],
            [
                "Escolarização",
                "TP_ESCOLA; TP_DEPENDENCIA_ADM_ESC; TP_LOCALIZACAO_ESC",
                "Público/privado, dependência administrativa e localização urbana/rural da escola. Verificar cobertura; não confundir escola atual com toda a trajetória.",
            ],
            [
                "Condições de estudo",
                "Q024; Q025",
                "Computador e internet. Possíveis mecanismos/mediadores de renda: incluir em bloco adicional, não controlar silenciosamente ao estimar associação total de renda.",
            ],
        ],
        [93, 177, 241],
    )
    r.p(
        "Expansão possível, não obrigatória: ocupação parental (Q003/Q004 desde 2015), cômodos e "
        "infraestrutura doméstica. Evitar incluir todos os bens simultaneamente com renda: isso aumenta redundância "
        "e dificulta interpretação. Esses extras não são necessários ao desenho amostral e não foram harmonizados nesta entrega."
    )

    r.heading("3. Harmonização: códigos mudam")
    r.table(
        ["Ano", "Renda", "Pai", "Mãe", "Moradores", "Internet", "Computador"],
        [
            [
                p["year"],
                *[
                    p["question_mapping"].get(k, {}).get("csv", "—")
                    for k in [
                        "renda",
                        "pai",
                        "mae",
                        "moradores",
                        "internet",
                        "computador",
                    ]
                ],
            ]
            for p in plans
        ],
        [39, 72, 70, 70, 85, 85, 90],
    )
    r.p(
        "Mapeamento obtido dos dicionários de cada pacote, incluindo diferenças entre nomes no dicionário "
        "e cabeçalhos dos CSVs. Traço significa que o mapeamento automático seguro não foi estabelecido nesta "
        "entrega, não prova de ausência de qualquer informação semelhante no questionário."
    )
    r.p(
        "<b>Exceções verificadas:</b> sexo em 2012 é 0=masculino e 1=feminino; nos demais anos usa M/F. "
        "Raça/cor ENEM é 1=branca, 2=preta, 3=parda, 4=amarela, 5=indígena. Na PNAD, os códigos "
        "3 e 4 significam amarela e parda, respectivamente: não unir pelos códigos sem recodificação."
    )
    r.p(
        "TP_ESCOLA também muda: pública/privada são 1/2 em 2012–2014, 2/4 em 2018 e 2/3 nos "
        "demais anos em que essas categorias foram mapeadas. Em 2010 o campo não está disponível na base "
        "adquirida. Em 2018, código 3 não é privada: representa exterior."
    )
    r.p(
        "Valores de renda e salário mínimo variam no tempo. Preservam-se as faixas originais dentro de cada "
        "ano; não se supõe que a mesma letra represente o mesmo poder de compra. Uma análise monetária temporal "
        "exigirá deflator, referência de preços e tratamento explícito dos intervalos abertos."
    )

    r.heading("4. Campos que não devem explicar a nota")
    r.table(
        ["Conjunto", "Uso correto"],
        [
            [
                "NU_INSCRICAO; ano",
                "Identificação e estratificação temporal; inscrição não é covariável numérica nem chave de painel individual longitudinal.",
            ],
            [
                "TP_PRESENCA_*; TP_STATUS_REDACAO; IN_TREINEIRO; TP_ST_CONCLUSAO; TP_ENSINO",
                "Definem elegibilidade. Não incluir como preditores após seleção; muitos ficam constantes ou revelam o próprio desfecho.",
            ],
            [
                "TX_RESPOSTAS_*; TX_GABARITO_*; NU_NOTA_COMP1–5",
                "Respostas, gabaritos e componentes da redação podem revelar ou reconstruir a nota: vazamento de informação para um estudo socioeconômico.",
            ],
            [
                "CO_MUNICIPIO_ESC; CO_UF_ESC",
                "Chaves de ligação e agrupamento. Códigos IBGE não têm ordem quantitativa. Não substituir residência por escola.",
            ],
            [
                "CO_MUNICIPIO_PROVA",
                "Local de aplicação, não moradia nem necessariamente escola. Não usar como atalho residencial.",
            ],
            [
                "As demais notas",
                "Usar matemática para explicar redação muda a pergunta para associação entre habilidades medidas, não o poder explicativo original do contexto socioeconômico.",
            ],
        ],
        [203, 308],
    )
    r.p(
        "Hipóteses de trabalho: recursos familiares e escolaridade parental estão associados ao desempenho; "
        "parte das diferenças entre escolas coincide com composição socioeconômica; o contexto municipal pode "
        "adicionar informação. São hipóteses substantivas, não resultados estatísticos."
    )
    r.p(
        "Para a etapa futura, comparar blocos predefinidos: demografia/ano; família; escola; município. "
        "Reportar diferenças de pontos e intervalos, não apenas p-valores ou R². Avaliar não linearidade da "
        "renda, interações justificadas, multicolinearidade e dependência dentro de escola/município. "
        "Em previsão, separar validação por tempo e/ou município e avaliar erro fora da amostra; importância "
        "preditiva não é efeito causal. Não há testes de hipótese executados neste documento."
    )

    r.heading("5. Contexto municipal: seleção enxuta")
    coverage = pd.read_csv(OUT / "cobertura_municipal_selecionada.csv")
    rows = []
    for name, meaning in MUNICIPAL.items():
        subset = coverage[coverage.variavel.eq(name) & coverage.observados.gt(0)]
        years = sorted(subset.ano.unique())
        span = str(years[0]) if len(years) == 1 else f"{years[0]}–{years[-1]}"
        rows.append(
            [
                name,
                span,
                meaning,
                f"{int(subset.observados.min())}–{int(subset.observados.max())}",
            ]
        )
    r.table(
        ["Coluna existente", "Anos", "Uso proposto", "Municípios/ano"],
        rows,
        [176, 53, 209, 73],
    )
    r.p(
        "Núcleo anual: PIB per capita, abandono no ensino médio e porte populacional. "
        "Aprofundamento censitário: renda domiciliar, Gini e IDHM-E. São sete colunas para seis conceitos, "
        "pois a renda tem duas fontes temporais distintas; não são sete indicadores completos em todos os anos."
    )
    r.p(
        "PIB per capita mede produção local, não dinheiro recebido pela família. Valores correntes não medem "
        "crescimento real sem deflação. IDHM total combina dimensões já representadas por renda/educação: "
        "prefiro IDHM-E em análise de sensibilidade, evitando empilhar o índice e seus componentes. "
        "Abandono pode ser um mediador/contexto contemporâneo, não causa predeterminada. Para previsão, "
        "considerar indicador do ano anterior e disponibilidade real na data da prova."
    )
    r.p(
        "IDEB, IQM, IQIM e IDeA são mencionados na proposta, mas não entraram neste núcleo: não há uma "
        "série municipal harmonizada desses índices na base importada que sustente incluí-los como observações anuais "
        "2010–2023. Não inventar, interpolar ou duplicar um valor censitário como se fosse medição anual."
    )
    r.p(
        "Ligação possível: CO_MUNICIPIO_ESC × ano com codigo_ibge × ano_enem, explicitamente "
        "<b>contexto do município da escola</b>. Não foi feita uma junção residencial. Escolas/localizações "
        "ausentes permanecem ausentes; uma futura análise contextual precisará quantificar sua seleção."
    )

    r.heading("6. Cobertura territorial e redundância")
    r.table(
        ["Ano", "Elegíveis ENEM", "Sem região da escola", "%"],
        [
            [
                p["year"],
                number(p["N_eligible"]),
                number(p["missing_school_region"]),
                number(100 * p["missing_school_region"] / p["N_eligible"], 1),
            ]
            for p in plans
        ],
        [55, 150, 180, 70],
    )
    pairs = pd.read_csv(OUT / "redundancia_municipal_2010.csv")
    labels = {
        "renda_per_capita_atlas_reais2010": "Renda domiciliar 2010",
        "gini_atlas": "Gini",
        "idhm_educacao": "IDHM-E",
        "pib_per_capita_reais": "PIB per capita",
    }
    r.table(
        ["Par de indicadores (2010)", "Pares completos", "Spearman"],
        [
            [
                f"{labels[x.variavel_a]} × {labels[x.variavel_b]}",
                number(x.n_pares),
                number(x.spearman_descritivo, 3),
            ]
            for x in pairs.itertuples()
        ],
        [311, 100, 100],
    )
    r.p(
        "Correlações descritivas entre municípios, sem testes ou interpretação causal; cada par usa sua "
        "cobertura disponível. Elas ajudam a evitar variáveis redundantes, mas não medem quanto cada indicador "
        "explica a nota individual. Não foram excluídos extremos por conveniência."
    )

    r.heading("7. Cadastro elegível e exclusões")
    r.p(
        "Regras anuais: TP_ST_CONCLUSAO=2; TP_ENSINO=1; IN_TREINEIRO=0 quando disponível; "
        "TP_PRESENCA_CN/CH/LC/MT=1; cinco notas numéricas; redação regular conforme dicionário. "
        "Em 2010–2014 não existe IN_TREINEIRO no arquivo: a conclusão declarada é o filtro disponível, "
        "não uma observação independente de ausência de treino. Raça, renda e escola ausentes não eliminam candidatos."
    )

    def flow(p, name):
        return next(x["remaining"] for x in p["flow"] if x["stage"] == name)

    r.table(
        [
            "Ano",
            "Inscritos",
            "Concluintes declarados",
            "Regular",
            "Presença 4",
            "Elegíveis",
        ],
        [
            [
                p["year"],
                *[
                    number(flow(p, stage))
                    for stage in [
                        "inscritos",
                        "concluintes_declarados",
                        "ensino_regular",
                        "presentes_quatro_provas",
                    ]
                ],
                number(p["N_eligible"]),
            ]
            for p in plans
        ],
        [37, 93, 105, 92, 92, 92],
    )
    r.p(
        "Situação regular da redação: P em 2010–2012, 7 em 2013–2014 e 1 a partir de 2015. "
        "O fluxo completo, com exclusões em cada etapa, está em fluxo_elegibilidade.csv. Zero numérico "
        "não é ausência, mas uma redação com situação irregular é excluída pela regra explícita de status."
    )
    r.p(
        "Esta exigência restringe o universo aos que completaram validamente todas as provas. "
        "É mais restritiva que simplesmente se inscrever e pode selecionar desempenho. Recomenda-se, "
        "na análise de sensibilidade futura, repetir resultados por área sem exigir validade das outras "
        "provas e da redação. A amostra atual não permite recuperar candidatos excluídos; os dados integrais foram preservados."
    )

    r.heading("8. Tamanho mínimo e escolha operacional")
    r.p(
        "Para proporção conservadora p=0,5, confiança de 95% (z≈1,96), erro absoluto e e efeito de "
        "desenho D, foi calculado: <b>n = teto[N × D × z² × p(1−p) / ((N−1)e² + D × z² × p(1−p))]</b>. "
        "N é o cadastro elegível da edição, não o total de habitantes do Brasil. Erro de 1% aqui significa "
        "<b>1 ponto percentual</b>, não 1% relativo e não erro de um ponto na nota."
    )
    r.table(
        ["Ano", "N elegível", "2 pp; D=2", "1 pp; D=2", "1 pp; D=3", "Selecionado"],
        [
            [
                p["year"],
                number(p["N_eligible"]),
                *[
                    number(
                        next(
                            s["n"]
                            for s in p["scenarios"]
                            if s["margem_pp"] == e and s["deff_planejado"] == d
                        )
                    )
                    for e, d in [(2, 2), (1, 2), (1, 3)]
                ],
                "20.000",
            ]
            for p in plans
        ],
        [40, 111, 90, 90, 90, 90],
    )
    r.p(
        "<b>Recomendação operacional: 20.000 por ano, 280.000 inscrições no total.</b> "
        "É uma escolha arredondada que cobre o cenário de 1 pp com D=2 em todas as edições. "
        "D=2 é reserva de planejamento, não estimativa demonstrada do efeito de desenho. D=1; 1,5; 2; 3 "
        "e ambos os erros foram calculados no CSV de cenários. Sob D=3, 20 mil não bastam para 1 pp."
    )
    r.p(
        "Não existe um tamanho ideal único para todas as perguntas: 20 mil não garante 1 pp dentro de cada "
        "grupo racial, região ou interação. Também não é cálculo de poder para regressão. Para média de nota, "
        "usar a variância da nota e tolerância em pontos; para comparar grupos, explicitar diferença mínima "
        "relevante e poder antes de testes. O intervalo nominal da subamostra não cobre o viés de entrada no ENEM."
    )

    r.heading("9. Estratos, alocação e probabilidades")
    r.p(
        "Estratificação conjunta <b>dentro de cada edição</b>: região da escola × raça/cor × sexo × faixa "
        "original de renda familiar. Ano é estrato temporal obrigatório. Alocação proporcional a N_h, "
        "com piso de 2 por célula ocupada, ou censo quando N_h=1; ajuste inteiro por maiores resíduos. "
        "Os grupos pequenos são sobreamostrados e corrigidos pelo peso, sem juntar indígenas ou amarelos a outras categorias."
    )
    r.p(
        "Em cada célula, sorteio aleatório sem reposição, cadastro ordenado por inscrição, gerador "
        "numpy.default_rng e semente 20260920 + ano. <b>π_h=n_h/N_h; w_desenho=N_h/n_h.</b> "
        "A soma dos pesos reconstrói o cadastro elegível anual. A probabilidade é condicional a estar nesse cadastro."
    )
    g = (
        pd.read_csv(OUT / "alocacao_2023.csv")
        .sort_values("N_h", ascending=False)
        .head(10)
    )
    r.table(
        [
            "Estrato 2023 (região escola | raça | sexo | renda)",
            "N_h",
            "n_h",
            "π_h",
            "Peso",
        ],
        [
            [
                x.estrato,
                number(x.N_h),
                number(x.n_h),
                number(x.pi_h, 5),
                number(x.peso_desenho, 2),
            ]
            for x in g.itertuples()
        ],
        [251, 75, 50, 70, 65],
    )
    r.p(
        "Exemplos acima são os dez maiores estratos de 2023. <b>TODOS os grupos dos 14 anos, "
        "seus N_h, n_h, π_h e pesos estão em alocacao_todos_estratos.csv, anexo ao PDF.</b> "
        "A tabela alocacao_por_caracteristica.csv mostra os totais selecionados por cada característica, ano a ano."
    )
    r.p(
        "Piso 2 serve à operacionalização, não à divulgação de estimativas confiáveis de células raras. "
        "Células com N_h=1 têm inclusão certa. Sem_escola é uma categoria de ausência de localização, "
        "não uma sexta região brasileira. Nao_declarada não é uma sexta raça/cor do IBGE."
    )

    r.heading("10. Referência externa: PNAD Contínua")
    r.p(
        "Fontes: microdados anuais oficiais, primeira visita em 2012–2019 e 2023; quinta visita em "
        "2020–2022, seguindo a orientação da série de rendimentos do IBGE. Peso anual <b>V1032</b>; "
        "V3002=1, ensino médio regular identificado pelo dicionário, V3006=03/04. Em 2015 há transição "
        "entre V3003 e V3003A: ambos foram tratados, evitando perder trimestres."
    )
    sensitivity = pd.read_csv(OUT / "sensibilidade_proxy.csv")
    r.table(
        [
            "Ano",
            "n observado PNAD",
            "Total proxy estimado",
            "% série 4",
            "Maior Δ margens (pp)",
        ],
        [
            [
                x.ano,
                number(x.n_pnad),
                number(x.total_proxy),
                number(100 * x.proporcao_serie4, 2),
                number(x.maior_delta_margens_pp_serie3_vs_3e4, 2),
            ]
            for x in sensitivity.itertuples()
        ],
        [45, 105, 145, 85, 131],
    )
    r.p(
        "Sensibilidade: última coluna é a maior alteração absoluta entre proporções de raça, sexo ou "
        "região ao trocar séries 3/4 por somente série 3. São diagnósticos da definição da proxy, "
        "não validação de que todos efetivamente concluíram o ensino médio."
    )
    r.p(
        "PNADC não existe para 2010/2011. Não transportar retrospectivamente margens de 2012. "
        "Esses dois anos receberam apenas pesos de desenho. Para uma calibração nacional estrita de "
        "concluintes confirmados seria necessária outra referência compatível, por exemplo registros "
        "educacionais com conclusão observada e características harmonizáveis; isso não foi presumido disponível."
    )

    r.heading("11. Proporções externas: exemplo 2023")
    margins = pd.read_csv(OUT / "margens_ibge_2023.csv")
    r.table(
        ["Característica", "Categoria", "n PNAD", "% ponderado", "EP (pp)"],
        [
            [
                x.variavel,
                x.categoria,
                number(x.n_pnad),
                number(100 * x.proporcao, 2),
                number(100 * x.erro_padrao_proporcao_taylor_wr, 2),
            ]
            for x in margins.itertuples()
        ],
        [102, 155, 76, 95, 83],
    )
    r.p(
        "Denominador: toda a proxy anual 3/4; ausência aparece em categoria própria quando ocorre. "
        "Renda é domiciliar efetiva VD5001, agrupada em até 1, 1–2, 2–5 e mais de 5 unidades do limite "
        "B do questionário ENEM do ano (R$ 1.320 em 2023), não renda familiar idêntica à do ENEM. "
        "Região é de residência PNAD; escola é rede frequentada. <b>Essas duas margens e renda não foram impostas externamente.</b>"
    )
    r.p(
        "EP: linearização de Taylor para proporção, com estratos e UPAs completos da PNAD, incluindo "
        "UPAs sem observações no domínio; aproximação com reposição. Não incorpora toda a incerteza da "
        "calibração original do IBGE. As margens são estimadas, não totais censitários exatos. "
        "Todos os anos e coeficientes de variação estão em margens_ibge_todos_anos.csv."
    )
    r.p(
        "<b>Em 2023, EP e CV estão ausentes:</b> existe um estrato com apenas uma UPA "
        "observada e contribuição não nula ao domínio. A variância dentro desse estrato não "
        "é estimável pelo procedimento adotado. Não foi arbitrado um ajuste nem reportado zero. "
        "A divulgação inferencial dessas proporções exige resolver esse tratamento; as estimativas "
        "pontuais permanecem disponíveis. A calibração continua experimental."
    )

    r.heading("12. Distribuição conjunta e raking")
    r.p(
        "Foi examinada, na PNAD, a tabela <b>5 raças × 5 regiões de residência × 4 faixas de renda "
        "domiciliar × 2 sexos = 200 células</b>, no domínio com raça e renda conhecidas. "
        "Não declarados são mantidos nos diagnósticos marginais e não tratados como raça do IBGE."
    )
    r.table(
        ["Ano", "Células", "Sem observação", "Menos de 5", "Menos de 30"],
        [
            [
                c["year"],
                c["joint_cells_total"],
                c["joint_cells_zero"],
                c["joint_cells_under5"],
                c["joint_cells_under30"],
            ]
            for c in calibrated
        ],
        [51, 75, 125, 130, 130],
    )
    r.p(
        "Contagens são de pessoas observadas na PNAD, antes dos pesos. As colunas são cumulativas: "
        "menos de 5 inclui zero. <b>Célula amostral vazia não significa população inexistente.</b> "
        "Além da esparsidade, faltam geografia e renda equivalentes no ENEM; portanto a conjunta externa "
        "completa solicitada não pode ser preservada honestamente com estas variáveis."
    )
    r.p(
        "Solução executada: raking com alvo externo <b>raça × sexo</b> (interação de 10 células) e "
        "idade (até 17; 18–19; 20+), simultaneamente ao alvo <b>interno</b> região da escola × faixa "
        "de renda ENEM. Conservam-se interações selecionadas, não todas. A idade foi incluída para "
        "reduzir diferenças de composição etária entre concluintes declarados e a proxy PNAD."
    )
    r.p(
        "Se suporte faltar, não fabricar observações nem pesos infinitos: revisar a interação, "
        "usar margens de menor dimensão ou redefinir explicitamente o domínio. Nesta execução, "
        "as restrições escolhidas convergiram sem junção ad hoc de categorias raciais e sem truncamento de pesos."
    )

    r.heading("13. Pesos entregues e diagnóstico")
    r.table(
        ["Coluna", "Interpretação"],
        [
            [
                "pi_h",
                "Probabilidade de sorteio dentro do cadastro elegível ENEM; não probabilidade nacional de participar do exame.",
            ],
            [
                "peso_desenho",
                "N_h/n_h: usar para descrição do ENEM elegível. Disponível nos 14 anos e para não declarados.",
            ],
            [
                "peso_calibrado_proxy",
                "w_desenho × fator g. Experimental, 2012–2023, raça/sexo conhecidos. Soma ao N ENEM desse domínio; não expande para a população brasileira.",
            ],
            [
                "peso_calibrado_proxy_normalizado",
                "Mesmo peso dividido pela média dos pesos calibrados da edição. Escala média 1; não estimar totais populacionais com ele.",
            ],
            [
                "status_calibracao",
                "Distingue domínio calibrado, fora de domínio e anos sem referência. Peso externo ausente não deve ser substituído por zero.",
            ],
        ],
        [183, 328],
    )
    r.table(
        [
            "Ano",
            "n calibrado",
            "Fora domínio",
            "Kish D",
            "n efetivo",
            "g mínimo",
            "g máximo",
        ],
        [
            [
                c["year"],
                number(c["sample_calibrated_n"]),
                number(c["sample_not_calibrated_n"]),
                number(c["kish_deff"], 2),
                number(c["effective_size_kish"]),
                number(c["calibration_factor_min"], 2),
                number(c["calibration_factor_max"], 2),
            ]
            for c in calibrated
        ],
        [38, 82, 86, 64, 83, 79, 79],
    )
    r.p(
        "Kish D = n × Σw²/(Σw)²; n efetivo = (Σw)²/Σw². É diagnóstico de dispersão de pesos, "
        "<b>não o efeito de desenho completo</b> da nota ou regressão. O efeito também depende da "
        "estratificação, relação peso–desfecho e dependência escolar/territorial. Não reinterpretar "
        "1/peso_calibrado como probabilidade nacional de inclusão."
    )
    r.p(
        "Nenhum peso foi aparado. Antes de inferência, comparar resultados com peso de desenho, "
        "calibrado e alternativas limitadas justificadas; se truncar, recalibrar e registrar resíduos. "
        "Erros-padrão futuros precisam respeitar desenho e, quando relevante, incerteza dos alvos PNAD; "
        "não usar fórmulas de amostra aleatória simples como se todos tivessem igual probabilidade."
    )
    r.p(
        "<b>Alerta de precisão:</b> em 2021, a dispersão de pesos calibrados já supera D=2. "
        "Assim, 20 mil não deve ser anunciado como garantia de 1 pp para a análise calibrada. "
        "Se 1 pp for requisito rígido com reserva D=3, a opção operacional mais conservadora é "
        "30 mil por edição (420 mil no período), ainda sujeita ao efeito efetivo de cada estimador. "
        "Essa ampliação é um cenário, não a amostra efetivamente sorteada nesta entrega."
    )

    r.heading("14. Como analisar sem exceder a evidência")
    r.p(
        "<b>Análise principal:</b> usar peso_desenho para descrever participantes elegíveis por ano. "
        "<b>Sensibilidade:</b> comparar com a padronização demográfica parcial PNAD em 2012–2023, "
        "sempre no mesmo domínio para atribuir diferenças à ponderação, e não à retirada de não declarados. "
        "Não misturar pesos externos ausentes de 2010/2011 com pesos calibrados como se fossem uma série uniforme."
    )
    r.p(
        "O uso de 20 mil por edição produz igualdade de tamanhos brutos, não igualdade de populações anuais. "
        "Para combinar anos, declarar o estimando: média das edições com igual peso temporal, ou média de "
        "inscrições elegíveis no período ponderada pelos totais anuais. Pessoas não são identificadas "
        "longitudinalmente, portanto o total é de inscrições, não de indivíduos únicos em 14 anos."
    )
    r.p(
        "Antes da modelagem: quantificar ausência em cada covariável, revisar códigos impossíveis, "
        "verificar notas/extremos, composição por escola, redundância dos indicadores e disponibilidade "
        "municipal. Não excluir automaticamente todos os incompletos: isso altera a população. "
        "Se imputação vier a ser necessária, predefinir modelo e análise de sensibilidade; não foi feita imputação aqui."
    )
    r.p(
        "O modelo associativo pode usar efeitos anuais e estrutura hierárquica por território/escola "
        "quando identificáveis. Escola pública/privada e recursos digitais podem ser mediadores de "
        "condições familiares: separar modelos com e sem esses blocos. Pré-especificar contrastes, "
        "hipóteses nula/alternativa, nível de significância e múltiplas comparações antes de testar."
    )
    r.p(
        "Para falar em variáveis que <b>discriminam desempenho</b>, prefiro manter a nota contínua "
        "inicialmente. Classificar alto/baixo desempenho exige limiares substantivos escolhidos antes, "
        "não cortes ajustados para maximizar diferenças. Avaliar relevância por magnitude e estabilidade, "
        "não selecionar variáveis somente por p-valor, coeficiente bruto ou importância de árvore."
    )
    r.p(
        "Limitações centrais: proxy de conclusão, participação voluntária, exclusão por presença/validade, "
        "ausência de residência, categorias históricas, referências externas amostrais, anos pandêmicos "
        "e cobertura municipal desigual. A calibração não converte o ENEM em levantamento probabilístico "
        "de todos os concluintes brasileiros."
    )

    r.heading("15. Auditoria, arquivos e reprodução")
    r.p(
        f"Validação executada: <b>{validation['rows']:,} registros</b> em 14 edições; unicidade de inscrição "
        "dentro da edição; n por estrato; limites de probabilidades; pesos inversos; reconstrução dos totais; "
        "pesos calibrados positivos e finitos; resíduos relativos de calibração abaixo de 1,1 × 10⁻⁹. "
        "Esse controle valida implementação, não identifica causalidade nem remove limitações de cobertura."
    )
    r.table(
        ["Arquivo em data/processed/sampling/", "Conteúdo"],
        [
            [
                "amostra_enem_2010_2023.parquet / .csv",
                "280 mil registros, variáveis originais selecionadas, estratos e pesos. Qxxx mantém significado original condicionado ao ano; usar o mapa anual.",
            ],
            [
                "alocacao_todos_estratos.csv",
                "N_h, n_h, π_h e peso de cada grupo/ano. Anexado ao PDF.",
            ],
            [
                "alocacao_por_caracteristica.csv",
                "Quantidades selecionadas e totais de desenho por característica/ano. Anexado.",
            ],
            [
                "margens_ibge_todos_anos.csv",
                "Proporções PNAD, n, totais estimados, EP e CV. Anexado.",
            ],
            [
                "cenarios_tamanho_amostral.csv",
                "2 margens × 4 efeitos de desenho × 14 anos. Anexado.",
            ],
            [
                "fluxo_elegibilidade.csv; mapa_variaveis_enem.csv",
                "Exclusões sequenciais e semântica anual dos questionários. Anexados.",
            ],
            [
                "calibracao_YYYY.json; residuos_calibracao_YYYY.csv",
                "Convergência, extremos, domínio e verificação de cada restrição.",
            ],
            [
                "validacao_amostra.json; sample_manifest.json",
                "Versões, seed, hash e controles reprodutíveis.",
            ],
        ],
        [237, 274],
    )
    r.p(
        "Com ambiente do projeto ativado, executar em ordem: python -m enem_analysis.data.pnad_sampling "
        "(usar --acquire somente para obtenção oficial); python -m enem_analysis.data.sampling_plan; "
        "python -m enem_analysis.data.calibrate_sample; python -m enem_analysis.visualization.sampling_report. "
        "Os cadastros anuais já gerados são reutilizados; para mudar o desenho, criar uma nova decisão "
        "e versão de derivados, sem editar dados brutos."
    )
    r.p(
        f"Python {validation['python']}; "
        + "; ".join(f"{k} {v}" for k, v in validation["libraries"].items())
        + "."
    )
    r.p(
        "Manifestos de aquisição e hashes: docs/sources/manifests/pnad*; catálogo anual: "
        "docs/sources/pnad_sampling_catalog.json. O pacote ENEM 2023 era preexistente e não teve "
        "URL/data de download original recuperadas; sua proveniência local está explicitada no inventário."
    )

    r.heading("16. Fontes e sustentação metodológica")
    sources = [
        (
            "Proposta fornecida pelo autor",
            "Chang (2).pdf, pp. 5–8; documento local, não fonte de resultados empíricos",
            None,
        ),
        (
            "INEP — Microdados ENEM",
            "Pacotes e dicionários anuais",
            "https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem",
        ),
        (
            "IBGE — PNADC anual, visita 1",
            "Dados, dicionários e entradas oficiais",
            "https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Anual/Microdados/Visita/Visita_1/",
        ),
        (
            "IBGE — PNADC anual, visita 5",
            "Referência de rendimento 2020–2022",
            "https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Anual/Microdados/Visita/Visita_5/",
        ),
        (
            "IBGE — divulgação de rendimentos",
            "Notas metodológicas da série anual de renda",
            "https://www.ibge.gov.br/biblioteca/visualizacao/livros/liv102176.pdf",
        ),
        (
            "IBGE — Educação 2023",
            "Contexto da investigação educacional; não confundir publicação do 2º trimestre com os arquivos anuais usados aqui",
            "https://biblioteca.ibge.gov.br/visualizacao/livros/liv102068_informativo.pdf",
        ),
        (
            "Survey — rake",
            "Calibração de margens e limites das tabelas conjuntas",
            "https://r-survey.r-forge.r-project.org/survey/html/rake.html",
        ),
        (
            "Survey — calibrate",
            "Calibração, limites de pesos e convergência",
            "https://r-survey.r-forge.r-project.org/survey/html/calibrate.html",
        ),
        (
            "Statistics Canada — Survey Methodology",
            "Dispersão de pesos e efeito de desenho",
            "https://www150.statcan.gc.ca/n1/pub/12-001-x/2015002/article/14236/02-eng.htm",
        ),
        (
            "Statistics Canada — amostras não probabilísticas",
            "Limitações de inferência e ajustes",
            "https://www150.statcan.gc.ca/n1/pub/12-001-x/2024001/article/00002-eng.htm",
        ),
    ]
    for title, meaning, url in sources:
        if url:
            r.p(
                f'<b>{escape(title)}</b> — {escape(meaning)}. <link href="{escape(url, quote=True)}" color="#17628A">Fonte oficial/documentação</link>.'
            )
        else:
            r.p(f"<b>{escape(title)}</b> — {escape(meaning)}.")
    definitions = read_json(ROOT / "docs/sources/municipal/dicionario_variaveis.json")
    seen = set()
    for d in definitions:
        if d["variavel"] in MUNICIPAL and d["link_fonte"] not in seen:
            seen.add(d["link_fonte"])
            r.p(
                f"<b>{escape(d['fonte'])}</b> — {escape(d['variavel'])}. "
                f'<link href="{escape(d["link_fonte"], quote=True)}" color="#17628A">Arquivo/API de origem municipal</link>.'
            )
    r.p(
        "Consulta e produção: 20/09/2026. URLs completas, versões, datas e hashes constam nos "
        "manifestos locais; as referências acima distinguem observações oficiais, documentação "
        "metodológica e decisões específicas deste projeto."
    )
    r.build()
    # Embed exhaustive numeric appendices so the PDF contains every group allocation.
    document = fitz.open(REPORT)
    attachments = [
        "alocacao_todos_estratos.csv",
        "alocacao_por_caracteristica.csv",
        "margens_ibge_todos_anos.csv",
        "cenarios_tamanho_amostral.csv",
        "fluxo_elegibilidade.csv",
        "mapa_variaveis_enem.csv",
    ]
    for name in attachments:
        document.embfile_add(name, (OUT / name).read_bytes(), filename=name)
    document.saveIncr()
    document.close()
    doc = fitz.open(REPORT)
    preview = OUT / "pdf_previews"
    preview.mkdir(exist_ok=True)
    bad_blocks = []
    for i, page in enumerate(doc):
        for block in page.get_text("blocks"):
            if block[0] < 25 or block[2] > A4[0] - 25 or block[3] > A4[1] - 15:
                bad_blocks.append({"page": i + 1, "bbox": list(block[:4])})
    for i in [0, min(2, len(doc) - 1), min(10, len(doc) - 1), len(doc) - 1]:
        doc[i].get_pixmap(matrix=fitz.Matrix(1.3, 1.3)).save(
            preview / f"page_{i + 1}.png"
        )
    write_json(
        OUT / "pdf_validation.json",
        {
            "pages": len(doc),
            "attachments": doc.embfile_names(),
            "out_of_bounds_blocks": bad_blocks,
            "sha256": sha256(REPORT),
        },
    )
    assert not bad_blocks, bad_blocks
    print(
        f"PDF: {REPORT}; {len(doc)} pages; {len(attachments)} attachments", flush=True
    )


if __name__ == "__main__":
    main()
