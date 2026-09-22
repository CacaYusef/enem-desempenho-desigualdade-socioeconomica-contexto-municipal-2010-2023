"""Validate the processed municipal time-series correlation products."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from enem_analysis.data.acquire import ROOT, write_json
from enem_analysis.statistics.territorial import association

OUT = ROOT / "data/processed/territorial_series_2010_2023"


def main() -> None:
    municipal = pd.read_parquet(OUT / "municipios_2010_2023.parquet")
    correlations = pd.read_csv(OUT / "correlacoes_municipais_2010_2023.csv")
    coverage = pd.read_csv(OUT / "cobertura_anual.csv")

    checks: dict[str, bool] = {
        "municipio_ano_unico": not municipal.duplicated(["ano", "codigo_ibge"]).any(),
        "anos_2010_2023": set(municipal.ano.unique()) == set(range(2010, 2024)),
        "correlacoes_no_intervalo": correlations[
            ["pearson", "spearman", "pearson_ponderado_n"]
        ]
        .stack()
        .dropna()
        .between(-1, 1)
        .all(),
        "chave_correlacao_unica": not correlations.duplicated(
            ["fonte_grupo", "ano", "n_min", "indicador", "nota"]
        ).any(),
    }

    grouped = municipal.groupby("ano").agg(
        n_vinculados=("n", "sum"),
        municipios_vinculados=("codigo_ibge", "size"),
        municipios_n20=("n", lambda values: values.ge(20).sum()),
        municipios_n30=("n", lambda values: values.ge(30).sum()),
        municipios_n50=("n", lambda values: values.ge(50).sum()),
    )
    coverage_indexed = coverage.set_index("ano")[grouped.columns]
    checks["cobertura_reconciliada"] = grouped.astype(int).equals(
        coverage_indexed.astype(int)
    )

    cell = municipal[municipal.ano.eq(2023) & municipal.n.ge(30)]
    recalculated = association(cell.pib_per_capita_reais, cell.media_NU_NOTA_MT, cell.n)
    saved = correlations[
        correlations.fonte_grupo.eq("anual")
        & correlations.ano.eq(2023)
        & correlations.n_min.eq(30)
        & correlations.indicador.eq("pib_per_capita_reais")
        & correlations.nota.eq("NU_NOTA_MT")
    ].iloc[0]
    checks["recalculo_2023_pib_matematica"] = all(
        np.isclose(saved[name], recalculated[name], rtol=0, atol=1e-12)
        for name in ["pearson", "spearman", "pearson_ponderado_n"]
    )

    finite_ideb_years = set(
        correlations.loc[
            correlations.fonte_grupo.eq("ideb_bienal") & correlations.pearson.notna(),
            "ano",
        ].unique()
    )
    checks["ideb_so_anos_disponiveis"] = finite_ideb_years == {
        2017,
        2019,
        2021,
        2023,
    }
    formal_wage = correlations[
        correlations.fonte_grupo.eq("anual")
        & correlations.indicador.eq("cempre_salario_medio_salarios_minimos_ate2021")
    ]
    checks["salario_formal_termina_2021"] = set(
        formal_wage.loc[formal_wage.pearson.notna(), "ano"].unique()
    ) == set(range(2010, 2022))

    checks = {name: bool(passed) for name, passed in checks.items()}
    report = {
        "status": "aprovado" if all(checks.values()) else "reprovado",
        "checagens": checks,
        "recalculo_2023_pib_matematica": {
            "n_pares": int(recalculated["n_pares"]),
            "pearson": float(recalculated["pearson"]),
            "spearman": float(recalculated["spearman"]),
            "pearson_ponderado_n": float(recalculated["pearson_ponderado_n"]),
        },
    }
    write_json(OUT / "validacao.json", report)
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise AssertionError(f"Temporal municipal validation failed: {failed}")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
