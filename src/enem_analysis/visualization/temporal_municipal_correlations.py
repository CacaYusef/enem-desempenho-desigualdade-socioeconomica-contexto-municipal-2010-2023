"""Academic plots for municipal ENEM/context correlation trajectories."""

from __future__ import annotations

import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from enem_analysis.data.temporal_municipal_correlations import (
    ANNUAL_INDICATORS,
    CENSUS_ANCHORS,
    IDEB_INDICATORS,
    OUT,
    SCORE_LABELS,
)

FIG = OUT / "figures"

# Two restrained color families; neutral grays remain structural.
PALETTES = {
    "azul": ["#123B5D", "#24699A", "#5A9BC7", "#8DBBDA", "#C4DCEB"],
    "amarelo": ["#6F5600", "#947300", "#C99A05", "#E2B83B", "#F1D77A"],
}
SCORE_COLORS = {
    "NU_NOTA_CN": PALETTES["azul"][1],
    "NU_NOTA_CH": PALETTES["amarelo"][2],
    "NU_NOTA_LC": PALETTES["azul"][2],
    "NU_NOTA_MT": PALETTES["azul"][0],
    "NU_NOTA_REDACAO": PALETTES["amarelo"][0],
}


def setup_style() -> None:
    plt.style.use("ggplot")
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9.2,
            "axes.titlesize": 11,
            "axes.titleweight": "bold",
            "axes.labelsize": 9.5,
            "axes.facecolor": "#F2F2F2",
            "axes.edgecolor": "#59636B",
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": "white",
            "grid.linewidth": 0.9,
            "legend.frameon": False,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def save(fig: plt.Figure, name: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / name, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def zero_axis(ax: plt.Axes) -> None:
    ax.axhline(0, color="#59636B", linewidth=0.8, linestyle="--", zorder=1)
    ax.set_ylim(-0.75, 0.85)
    ax.set_xticks(range(2010, 2024, 2))
    ax.set_xlabel("Ano do ENEM e do indicador")
    ax.set_ylabel("Correlação")


def footer(fig: plt.Figure, text: str) -> None:
    fig.text(
        0.01,
        0.01,
        textwrap.fill(text, 175),
        ha="left",
        va="bottom",
        fontsize=7.4,
        color="#42484D",
    )


def trajectory_figure(corr: pd.DataFrame, metric: str, filename: str) -> None:
    selected = corr[corr.fonte_grupo.eq("anual") & corr.n_min.eq(30)].copy()
    fig, axes = plt.subplots(2, 2, figsize=(12.4, 7.8), sharex=True, sharey=True)
    axes = axes.ravel()
    for ax, (indicator, label) in zip(axes, ANNUAL_INDICATORS.items(), strict=True):
        part = selected[selected.indicador.eq(indicator)]
        for score, score_label in SCORE_LABELS.items():
            line = part[part.nota.eq(score)].dropna(subset=[metric]).sort_values("ano")
            ax.plot(
                line.ano,
                line[metric],
                color=SCORE_COLORS[score],
                marker="o",
                markersize=3.8,
                linewidth=1.8,
                label=score_label,
            )
        ax.set_title(label)
        zero_axis(ax)
    title = "Pearson" if metric == "pearson" else "Spearman"
    fig.suptitle(
        f"Trajetória das correlações municipais entre contexto e notas — {title}",
        fontsize=14,
        fontweight="bold",
        y=0.985,
    )
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=5, bbox_to_anchor=(0.5, 0.945))
    footer(
        fig,
        "Cada ponto usa municípios da escola com pelo menos 30 candidatos "
        "elegíveis e dá o mesmo peso a cada município. Os pontos são conectados "
        "apenas como guia descritiva; não há regressão, teste ou afirmação "
        "causal. O salário formal do CEMPRE termina em 2021 devido à quebra de "
        "série em 2022. Fontes: ENEM/INEP, PIB municipal/IBGE, CEMPRE/IBGE e "
        "rendimento escolar/INEP.",
    )
    fig.tight_layout(rect=(0, 0.08, 1, 0.90))
    save(fig, filename)


def weighting_figure(corr: pd.DataFrame) -> None:
    selected = corr[
        corr.fonte_grupo.eq("anual") & corr.n_min.eq(30) & corr.nota.eq("NU_NOTA_MT")
    ].copy()
    fig, axes = plt.subplots(2, 2, figsize=(12.4, 7.6), sharex=True, sharey=True)
    axes = axes.ravel()
    for ax, (indicator, label) in zip(axes, ANNUAL_INDICATORS.items(), strict=True):
        part = selected[selected.indicador.eq(indicator)].sort_values("ano")
        ax.plot(
            part.ano,
            part.pearson,
            color=PALETTES["azul"][1],
            marker="o",
            linewidth=2,
            markersize=4,
            label="Igual peso municipal",
        )
        ax.plot(
            part.ano,
            part.pearson_ponderado_n,
            color=PALETTES["amarelo"][2],
            marker="s",
            linewidth=2,
            markersize=3.8,
            label="Ponderado pelo nº de candidatos",
        )
        ax.set_title(label)
        zero_axis(ax)
    fig.suptitle(
        "Matemática: sensibilidade da correlação de Pearson à ponderação",
        fontsize=14,
        fontweight="bold",
        y=0.985,
    )
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 0.94))
    footer(
        fig,
        "A linha azul responde como municípios típicos covariam; a amarela "
        "aproxima a distribuição dos candidatos vinculados. As duas medidas são "
        "estimandos descritivos diferentes. Municípios com n≥30; extremos "
        "preservados; sem inferência ou causalidade.",
    )
    fig.tight_layout(rect=(0, 0.075, 1, 0.90))
    save(fig, "03_matematica_sensibilidade_ponderacao.png")


def ideb_figure(corr: pd.DataFrame) -> None:
    selected = corr[corr.fonte_grupo.eq("ideb_bienal") & corr.n_min.eq(30)].copy()
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.9), sharey=True)
    for ax, (indicator, label) in zip(axes, IDEB_INDICATORS.items(), strict=True):
        part = selected[selected.indicador.eq(indicator)]
        for score, score_label in SCORE_LABELS.items():
            line = (
                part[part.nota.eq(score)].dropna(subset=["pearson"]).sort_values("ano")
            )
            ax.plot(
                line.ano,
                line.pearson,
                color=SCORE_COLORS[score],
                marker="o",
                linewidth=1.9,
                markersize=4.2,
                label=score_label,
            )
        ax.set_title(label)
        ax.axhline(0, color="#59636B", linewidth=0.8, linestyle="--")
        ax.set_xticks([2017, 2019, 2021, 2023])
        ax.set_ylim(-0.35, 0.80)
        ax.set_xlabel("Ano de referência")
        ax.set_ylabel("Pearson — igual peso municipal")
    fig.suptitle(
        "IDEB/Saeb municipal público e notas do ENEM — referências disponíveis",
        fontsize=14,
        fontweight="bold",
        y=0.99,
    )
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=5, bbox_to_anchor=(0.5, 0.90))
    footer(
        fig,
        "A divulgação local utilizada contém 2017, 2019, 2021 e 2023; anos "
        "intermediários não foram interpolados. IDEB/Saeb é da rede pública, "
        "enquanto as médias ENEM incluem todos os candidatos elegíveis vinculados "
        "ao município da escola. Municípios com n≥30. Fontes: INEP.",
    )
    fig.tight_layout(rect=(0, 0.13, 1, 0.83))
    save(fig, "04_ideb_saeb_bienal.png")


def census_anchor_figure(corr: pd.DataFrame) -> None:
    display_labels = {
        "Renda per capita (Atlas)": "Renda per capita (Atlas)",
        "Gini (Atlas)": "Gini (Atlas)",
        "IDHM Educação": "IDHM Educação",
        "Pobreza": "Pobreza",
        "Extrema pobreza": "Extrema pobreza",
        "Renda domiciliar per capita": "Renda domiciliar pc",
        "Renda domiciliar per capita mediana": "Mediana da renda domiciliar pc",
        "Alfabetização 15+": "Alfabetização 15+",
    }
    cmap = LinearSegmentedColormap.from_list(
        "academic_diverging",
        [PALETTES["amarelo"][0], "#F2F2F2", PALETTES["azul"][0]],
    )
    fig, axes = plt.subplots(
        1, 2, figsize=(14.5, 5.4), gridspec_kw={"width_ratios": [5, 3]}
    )
    last_image = None
    for ax, (year, indicators) in zip(axes, CENSUS_ANCHORS.items(), strict=True):
        part = corr[corr.fonte_grupo.eq(f"censitario_{year}") & corr.n_min.eq(30)]
        matrix = np.full((len(indicators), len(SCORE_LABELS)), np.nan)
        for i, indicator in enumerate(indicators):
            for j, score in enumerate(SCORE_LABELS):
                cell = part[part.indicador.eq(indicator) & part.nota.eq(score)].pearson
                if len(cell):
                    matrix[i, j] = cell.iloc[0]
        last_image = ax.imshow(matrix, cmap=cmap, vmin=-0.7, vmax=0.7, aspect="auto")
        ax.set_title(f"Âncora {year}")
        ax.set_xticks(
            range(len(SCORE_LABELS)), SCORE_LABELS.values(), rotation=35, ha="right"
        )
        ax.set_yticks(
            range(len(indicators)),
            [
                display_labels.get(indicator, indicator)
                for indicator in indicators.values()
            ],
        )
        ax.grid(False)
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                if np.isfinite(matrix[i, j]):
                    color = "white" if abs(matrix[i, j]) > 0.42 else "#202428"
                    ax.text(
                        j,
                        i,
                        f"{matrix[i, j]:.2f}",
                        ha="center",
                        va="center",
                        color=color,
                        fontsize=8.4,
                    )
    fig.suptitle(
        "Correlações municipais em âncoras censitárias — não formam série anual",
        fontsize=14,
        fontweight="bold",
        y=0.985,
    )
    if last_image is not None:
        color_axis = fig.add_axes([0.925, 0.22, 0.015, 0.60])
        cbar = fig.colorbar(last_image, cax=color_axis)
        cbar.set_label("Pearson — igual peso municipal")
    footer(
        fig,
        "Os indicadores de 2010 (Atlas) e 2022 (Censo) têm conceitos e fontes "
        "distintas e, por isso, não são ligados por linhas nem interpretados "
        "como variação do mesmo coeficiente. Municípios com n≥30; fontes: "
        "Ipeadata/Atlas e IBGE.",
    )
    fig.subplots_adjust(left=0.15, right=0.90, bottom=0.20, top=0.84, wspace=0.50)
    save(fig, "05_ancoras_censitarias.png")


def coverage_figure(coverage: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.6), sharex=True)
    axes[0].plot(
        coverage.ano,
        coverage.municipios_n30,
        color=PALETTES["azul"][1],
        marker="o",
        linewidth=2,
    )
    axes[0].set_title("Municípios no corte principal")
    axes[0].set_ylabel("Número de municípios com n≥30")
    axes[1].plot(
        coverage.ano,
        coverage.pct_vinculados_n30,
        color=PALETTES["amarelo"][2],
        marker="o",
        linewidth=2,
    )
    axes[1].set_title("Candidatos vinculados retidos pelo corte")
    axes[1].set_ylabel("% dos vinculados em municípios n≥30")
    for ax in axes:
        ax.set_xticks(range(2010, 2024, 2))
        ax.set_xlabel("Ano do ENEM")
    fig.suptitle(
        "Cobertura do domínio municipal usado nas correlações",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )
    footer(
        fig,
        "O município é o da escola. A queda de cobertura em 2020–2023 reflete "
        "maior ausência do código escolar e mudanças na composição dos "
        "participantes; isso pode alterar as correlações mesmo sem mudança "
        "estrutural subjacente. Fonte: Microdados ENEM/INEP.",
    )
    fig.tight_layout(rect=(0, 0.11, 1, 0.89))
    save(fig, "06_cobertura_temporal.png")


def main() -> None:
    setup_style()
    correlations = pd.read_csv(OUT / "correlacoes_municipais_2010_2023.csv")
    coverage = pd.read_csv(OUT / "cobertura_anual.csv")
    trajectory_figure(correlations, "pearson", "01_trajetorias_pearson.png")
    trajectory_figure(correlations, "spearman", "02_trajetorias_spearman.png")
    weighting_figure(correlations)
    ideb_figure(correlations)
    census_anchor_figure(correlations)
    coverage_figure(coverage)
    files = sorted(FIG.glob("*.png"))
    print(f"Figures: {FIG}; {len(files)} files")


if __name__ == "__main__":
    main()
