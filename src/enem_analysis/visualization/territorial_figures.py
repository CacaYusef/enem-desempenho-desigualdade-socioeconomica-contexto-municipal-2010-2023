"""Question-led territorial figures; descriptive smoothing, no econometrics."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.nonparametric.smoothers_lowess import lowess

from enem_analysis.data.territorial_analysis import INCOME_ORDER
from enem_analysis.data.territorial_context import INDICATORS, OUT, REGIONS

FIG = OUT / "figures"

# Two restrained color families. Every data mark is a shade from one of them;
# grays are reserved for grids, axes and missing/unknown reference marks.
PALETTES = {
    "azul": ["#123B5D", "#24699A", "#5A9BC7", "#8DBBDA", "#C4DCEB"],
    "amarelo": ["#6F5600", "#947300", "#C99A05", "#E2B83B", "#F1D77A"],
}
COLORS = dict(
    zip(
        REGIONS,
        [
            PALETTES["azul"][1],
            PALETTES["amarelo"][2],
            PALETTES["amarelo"][0],
            PALETTES["azul"][0],
            PALETTES["azul"][3],
        ],
        strict=True,
    )
)
INCOME_COLORS = [
    PALETTES["azul"][0],
    PALETTES["azul"][1],
    PALETTES["azul"][3],
    PALETTES["azul"][4],
]
RACE_COLORS = [
    PALETTES["azul"][4],
    PALETTES["azul"][2],
    PALETTES["amarelo"][0],
    PALETTES["amarelo"][2],
    PALETTES["amarelo"][4],
    PALETTES["azul"][0],
]
EDUC_SHORT = [
    "Nunca estudou",
    "Fund. inicial incompleto",
    "Fund. final incompleto",
    "Médio incompleto",
    "Médio completo",
    "Superior completo",
    "Pós-graduação",
    "Não sabe",
]


def save(fig, name):
    fig.savefig(FIG / name, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def smooth(ax, x, y, color, label=None, log=False):
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    if log:
        ok &= x > 0
    x, y = x[ok], y[ok]
    if len(x) < 15 or len(np.unique(x)) < 4:
        return
    transform = np.log(x) if log else x
    curve = lowess(y, transform, frac=0.6, it=0, delta=0.01 * np.ptp(transform))
    ax.plot(
        np.exp(curve[:, 0]) if log else curve[:, 0],
        curve[:, 1],
        color=color,
        lw=2,
        label=label,
    )


def scatter(ax, part, col, y="media", n="n", color=PALETTES["azul"][1], log=False):
    pair = part[[col, y, n]].dropna()
    sizes = np.clip(5 + np.sqrt(pair[n].astype(float)), 6, 95)
    ax.scatter(pair[col], pair[y], s=sizes, color=color, alpha=0.28, linewidths=0)
    smooth(ax, pair[col], pair[y], color, log=log)
    if log:
        ax.set_xscale("log")
    ax.set_xlabel(INDICATORS[col] + (" — escala log" if log else ""))
    ax.set_ylabel("Média municipal de matemática (pontos)")
    ax.grid(alpha=0.13)
    ax.text(
        0.03,
        0.97,
        f"{len(pair):,} municípios".replace(",", "."),
        transform=ax.transAxes,
        va="top",
        fontsize=9,
    )


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    plt.style.use("ggplot")
    plt.rcParams.update(
        {
            "font.size": 10,
            "font.family": "DejaVu Sans",
            "axes.spines.top": False,
            "axes.spines.right": False,
        "axes.titleweight": "bold",
            "axes.facecolor": "#F2F2F2",
            "axes.edgecolor": "#5A6268",
            "axes.labelcolor": "#26343A",
            "axes.axisbelow": True,
            "grid.color": "#FFFFFF",
            "grid.linewidth": 0.9,
            "grid.alpha": 0.95,
            "legend.frameon": False,
            "lines.linewidth": 1.8,
            "figure.facecolor": "white",
            "figure.constrained_layout.use": True,
        }
    )
    frame = pd.read_parquet(OUT / "candidatos_2023.parquet")
    municipal = pd.read_parquet(OUT / "municipios_2023.parquet")
    m = municipal[municipal.n.ge(30)]
    groups = pd.read_csv(OUT / "grupos_individuais.csv")
    regions = pd.read_csv(OUT / "regioes.csv").set_index("regiao")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    for ax, var, title in zip(
        axes, ["renda_grupo", "raca"], ["Renda familiar", "Raça/cor"], strict=True
    ):
        g = groups[groups.variavel.eq(var) & groups.regiao.isin(REGIONS)]
        table = (
            g.pivot(index="regiao", columns="categoria", values="pct")
            .reindex(REGIONS)
            .fillna(0)
        )
        if var == "renda_grupo":
            table = table.reindex(columns=INCOME_ORDER)
        else:
            table = table.reindex(
                columns=[
                    "Não declarado",
                    "Branca",
                    "Preta",
                    "Parda",
                    "Amarela",
                    "Indígena",
                ],
                fill_value=0,
            )
        table.plot.barh(
            stacked=True,
            ax=ax,
            color=INCOME_COLORS if var == "renda_grupo" else RACE_COLORS,
            width=0.65,
        )
        ax.set_title(title)
        ax.set_xlabel("% dos candidatos da região escolar conhecida")
        ax.set_ylabel("")
        ax.set_xlim(0, 100)
        ax.invert_yaxis()
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -0.17),
            ncol=2,
            fontsize=7.5,
            frameon=False,
        )
    save(fig, "01_composicao_regional.png")
    fig, ax = plt.subplots(figsize=(9, 4.6))
    for region in REGIONS:
        g = (
            groups[groups.regiao.eq(region) & groups.variavel.eq("renda_grupo")]
            .set_index("categoria")
            .reindex(INCOME_ORDER)
        )
        ax.plot(range(4), g.media, marker="o", label=region, color=COLORS[region])
    ax.set_xticks(
        range(4), ["Até 1.320", "1.320,01–2.640", "2.640,01–6.600", "Acima de 6.600"]
    )
    ax.set_xlabel("Renda familiar mensal (R$), categorias agrupadas")
    ax.set_ylabel("Média de matemática (pontos)")
    ax.legend(ncol=3, frameon=False)
    ax.grid(alpha=0.15)
    save(fig, "02_renda_regiao.png")
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2), sharey=True)
    for ax, raw, title in zip(
        axes, ["Q002", "Q001"], ["Mãe/responsável", "Pai/responsável"], strict=True
    ):
        for region in REGIONS:
            means = (
                frame[frame.regiao.eq(region)]
                .groupby(raw, observed=True)
                .NU_NOTA_MT.mean()
                .reindex(list("ABCDEFGH"))
            )
            ax.plot(
                means, range(8), marker="o", ms=3, color=COLORS[region], label=region
            )
        ax.set_title(title)
        ax.set_yticks(range(8), EDUC_SHORT)
        ax.set_xlabel("Média de matemática (pontos)")
        ax.grid(axis="x", alpha=0.15)
    axes[0].invert_yaxis()
    axes[1].legend(fontsize=8, frameon=False)
    save(fig, "03_parental_regiao.png")
    names = [*REGIONS, "Não identificada"]
    fig, axes = plt.subplots(
        1, 2, figsize=(10.5, 4.5), gridspec_kw={"width_ratios": [1.2, 1]}
    )
    for i, region in enumerate(names):
        r = regions.loc[region]
        axes[0].plot(
            [r.q1, r.q3], [i, i], color=COLORS.get(region, "#777777"), lw=6, alpha=0.6
        )
        axes[0].plot(r.mediana, i, "|", color="black", ms=14)
    axes[0].set_yticks(range(6), names)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("Mediana e intervalo interquartil (pontos)")
    axes[0].set_title("Dispersão dentro das regiões")
    axes[1].hist(
        frame.NU_NOTA_MT,
        bins=np.arange(0, 981, 20),
        weights=np.full(len(frame), 100 / len(frame)),
        color=PALETTES["amarelo"][1],
    )
    axes[1].set_xlabel("Matemática (pontos)")
    axes[1].set_ylabel("% dos elegíveis")
    axes[1].set_title("Desfecho: base completa")
    save(fig, "04_distribuicao_desfecho.png")
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7))
    for ax, col in zip(
        axes.flat,
        ["ideb_2023", "pib_pc_2023", "renda_pc_2022", "distorcao_2023"],
        strict=True,
    ):
        values = [
            m.loc[m.regiao.eq(r), col].dropna().astype(float).to_numpy()
            for r in REGIONS
        ]
        stats = []
        for label, array in zip(["N", "NE", "CO", "SE", "S"], values, strict=True):
            q1, median, q3 = np.quantile(
                array, [0.25, 0.5, 0.75], method="inverted_cdf"
            )
            iqr = q3 - q1
            inside = array[(array >= q1 - 1.5 * iqr) & (array <= q3 + 1.5 * iqr)]
            stats.append(
                {
                    "label": label,
                    "q1": q1,
                    "med": median,
                    "q3": q3,
                    "whislo": inside.min(),
                    "whishi": inside.max(),
                    "fliers": array[(array < inside.min()) | (array > inside.max())],
                }
            )
        artists = ax.bxp(
            stats,
            showfliers=True,
            patch_artist=True,
            medianprops={"color": "#26343A", "linewidth": 1.3},
            whiskerprops={"color": "#59666C", "linewidth": 0.9},
            capprops={"color": "#59666C", "linewidth": 0.9},
            flierprops={"markersize": 2, "alpha": 0.28, "markeredgecolor": "#59666C"},
        )
        for box, region in zip(artists["boxes"], REGIONS, strict=True):
            box.set_facecolor(COLORS[region])
            box.set_edgecolor("#45535A")
            box.set_alpha(0.72)
        ax.set_title(INDICATORS[col])
        if col == "pib_pc_2023":
            ax.set_yscale("log")
            ax.set_ylabel("R$ — escala log")
        ax.grid(axis="y", alpha=0.15)
    save(fig, "05_contexto_regional.png")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    scatter(axes[0], m, "ideb_2023", color=PALETTES["azul"][1])
    axes[0].set_title("Todos os candidatos vinculados")
    pub = m[m.n_publica.ge(30)]
    scatter(
        axes[1],
        pub,
        "ideb_2023",
        "media_publica",
        "n_publica",
        PALETTES["amarelo"][2],
    )
    axes[1].set_title("Somente candidatos de escola pública")
    save(fig, "06_ideb_nacional.png")
    fig, axes = plt.subplots(2, 3, figsize=(12, 7.2), sharex=True, sharey=True)
    for ax, region in zip(axes.flat, REGIONS, strict=False):
        scatter(ax, m[m.regiao.eq(region)], "ideb_2023", color=COLORS[region])
        ax.set_title(region)
        ax.set_xlabel("IDEB EM público (2023)")
        ax.set_ylabel("Matemática — média municipal")
    ax = axes.flat[-1]
    for region in REGIONS:
        part = m[m.regiao.eq(region)]
        smooth(ax, part.ideb_2023, part.media, COLORS[region], region)
    ax.set_title("Curvas no suporte observado")
    ax.legend(fontsize=8, frameon=False)
    ax.set_xlabel("IDEB EM público (2023)")
    save(fig, "07_ideb_regioes.png")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    for ax, col, color in zip(
        axes,
        ["pib_pc_2023", "renda_pc_2022"],
        [PALETTES["azul"][1], PALETTES["amarelo"][2]],
        strict=True,
    ):
        scatter(ax, m, col, color=color, log=col.startswith("pib"))
    save(fig, "08_economia_municipal.png")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    for ax, col in zip(axes, ["pib_pc_2023", "renda_pc_2022"], strict=True):
        for region in REGIONS:
            part = m[m.regiao.eq(region)]
            smooth(
                ax,
                part[col],
                part.media,
                COLORS[region],
                region,
                log=col.startswith("pib"),
            )
        if col.startswith("pib"):
            ax.set_xscale("log")
        ax.set_xlabel(
            INDICATORS[col] + (" — escala log" if col.startswith("pib") else "")
        )
        ax.set_ylabel("Média municipal de matemática (pontos)")
        ax.grid(alpha=0.15)
    axes[0].legend(fontsize=8, frameon=False)
    save(fig, "09_economia_regioes.png")
    quint = pd.read_csv(OUT / "desempenho_quintis.csv")
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.7), sharey=True)
    for ax, col in zip(
        axes, ["ideb_2023", "pib_pc_2023", "renda_pc_2022"], strict=True
    ):
        for region in REGIONS:
            q = quint[quint.regiao.eq(region) & quint.indicador.eq(col)].sort_values(
                "quintil"
            )
            ax.plot(
                q.quintil, q.media, marker="o", ms=3, color=COLORS[region], label=region
            )
        ax.set_title(INDICATORS[col], fontsize=9)
        ax.set_xticks(range(1, 6), ["Q1", "Q2", "Q3", "Q4", "Q5"])
        ax.set_xlabel("Quintil municipal nacional")
        ax.grid(alpha=0.15)
    axes[0].set_ylabel("Média dos candidatos em matemática (pontos)")
    axes[1].legend(fontsize=7, frameon=False)
    save(fig, "10_quintis_contextuais.png")
    coverage = pd.read_csv(OUT / "comparacao_cobertura.csv")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    for ax, var in zip(axes, ["renda_grupo", "escola"], strict=True):
        c = coverage[coverage.variavel.eq(var)].pivot(
            index="categoria", columns="dominio", values="pct"
        )
        if var == "renda_grupo":
            c = c.reindex(INCOME_ORDER)
        c.plot.barh(
            ax=ax,
            color=[PALETTES["amarelo"][3], PALETTES["azul"][1]],
            width=0.75,
        )
        ax.set_xlabel("% dentro do domínio de cobertura")
        ax.set_ylabel("")
        ax.set_title("Renda familiar" if var == "renda_grupo" else "Tipo de escola")
        ax.legend(fontsize=7, frameon=False, loc="lower right")
    save(fig, "11_selecao_cobertura.png")
    print(
        f"Figures: {FIG}; 11 files, all five regions; LOWESS descriptive only",
        flush=True,
    )


if __name__ == "__main__":
    main()
