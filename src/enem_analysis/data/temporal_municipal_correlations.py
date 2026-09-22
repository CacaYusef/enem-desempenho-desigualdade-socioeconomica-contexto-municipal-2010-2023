"""Municipal ENEM/context correlations through time; descriptive, not inferential."""

from __future__ import annotations

import importlib.metadata
import json
import platform

import numpy as np
import pandas as pd

from enem_analysis.data.acquire import ROOT, sha256, write_json
from enem_analysis.data.sampling_plan import SCORES
from enem_analysis.data.territorial_context import read_spreadsheet
from enem_analysis.statistics.territorial import association

YEARS = tuple(range(2010, 2024))
CUTOFFS = (20, 30, 50)
OUT = ROOT / "data/processed/territorial_series_2010_2023"
ELIGIBLE = ROOT / "data/processed/sampling"
MUNICIPAL_SOURCE = ROOT / "data/processed/municipal/base_municipio_ano.parquet"

SCORE_LABELS = {
    "NU_NOTA_CN": "Natureza",
    "NU_NOTA_CH": "Humanas",
    "NU_NOTA_LC": "Linguagens",
    "NU_NOTA_MT": "Matemática",
    "NU_NOTA_REDACAO": "Redação",
}

# These are the only selected municipal measures with a repeated, documented
# series. CEMPRE ends in 2021 because the source changes in 2022.
ANNUAL_INDICATORS = {
    "pib_per_capita_reais": "PIB per capita",
    "cempre_salario_medio_salarios_minimos_ate2021": (
        "Salário médio formal (salários mínimos)"
    ),
    "educ_aprovacao_medio_pct": "Aprovação no ensino médio",
    "educ_abandono_medio_pct": "Abandono no ensino médio",
}

# Census/Atlas anchors are not interpolated or connected as a time series.
CENSUS_ANCHORS = {
    2010: {
        "renda_per_capita_atlas_reais2010": "Renda per capita (Atlas)",
        "gini_atlas": "Gini (Atlas)",
        "idhm_educacao": "IDHM Educação",
        "pobreza_atlas_pct": "Pobreza",
        "extrema_pobreza_atlas_pct": "Extrema pobreza",
    },
    2022: {
        "renda_domiciliar_per_capita_censo2022_reais": ("Renda domiciliar per capita"),
        "renda_domiciliar_per_capita_mediana_censo2022_reais": (
            "Renda domiciliar per capita mediana"
        ),
        "alfabetizacao_15mais_censo2022_pct": "Alfabetização 15+",
    },
}

IDEB_YEARS = (2017, 2019, 2021, 2023)
IDEB_INDICATORS = {
    "ideb_publico": "IDEB EM público",
    "saeb_mt_publico": "Saeb matemática",
}


def normalize_municipality_code(values: pd.Series) -> pd.Series:
    """Return nullable seven-digit IBGE municipality codes."""
    codes = values.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    valid = codes.str.fullmatch(r"\d{7}", na=False)
    return codes.where(valid)


def aggregate_year(frame: pd.DataFrame, year: int) -> pd.DataFrame:
    """Aggregate complete-score eligible registrations by school municipality."""
    required = ["CO_MUNICIPIO_ESC", *SCORES]
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing eligible columns in {year}: {missing}")
    work = frame[required].copy()
    work["codigo_ibge"] = normalize_municipality_code(work.CO_MUNICIPIO_ESC)
    for score in SCORES:
        work[score] = pd.to_numeric(work[score], errors="coerce")
        invalid = work[score].notna() & (~np.isfinite(work[score]) | work[score].lt(0))
        if invalid.any():
            raise ValueError(f"Invalid {score} values in {year}: {int(invalid.sum())}")
    work = work.dropna(subset=["codigo_ibge", *SCORES])
    grouped = work.groupby("codigo_ibge", observed=True)
    result = (
        grouped[list(SCORES)]
        .mean()
        .rename(columns={score: f"media_{score}" for score in SCORES})
    )
    result.insert(0, "n", grouped.size())
    result = result.reset_index()
    result.insert(0, "ano", int(year))
    return result


def extract_ideb_panel() -> pd.DataFrame:
    """Read the public-network municipal IDEB/Saeb vintages already on disk."""
    raw = read_spreadsheet("ideb_municipios_em_v2025.zip", 9)
    public = raw[raw.REDE.eq("Pública")].copy()
    public["codigo_ibge"] = normalize_municipality_code(public.CO_MUNICIPIO)
    rows = []
    for year in IDEB_YEARS:
        part = public[
            [
                "codigo_ibge",
                f"VL_OBSERVADO_{year}",
                f"VL_NOTA_MATEMATICA_{year}",
            ]
        ].rename(
            columns={
                f"VL_OBSERVADO_{year}": "ideb_publico",
                f"VL_NOTA_MATEMATICA_{year}": "saeb_mt_publico",
            }
        )
        for column in IDEB_INDICATORS:
            part[column] = pd.to_numeric(part[column], errors="coerce")
        part.insert(0, "ano", year)
        rows.append(part)
    result = pd.concat(rows, ignore_index=True)
    if result.duplicated(["ano", "codigo_ibge"]).any():
        raise ValueError("Duplicate public IDEB municipality-year keys")
    return result


def association_rows(
    municipal: pd.DataFrame,
    indicators: dict[str, str],
    source_group: str,
) -> list[dict]:
    rows: list[dict] = []
    for cutoff in CUTOFFS:
        selected = municipal[municipal.n.ge(cutoff)]
        for year, annual in selected.groupby("ano", sort=True):
            for indicator, label in indicators.items():
                if indicator not in annual:
                    continue
                for score in SCORES:
                    result = association(
                        annual[indicator], annual[f"media_{score}"], annual.n
                    )
                    rows.append(
                        {
                            "fonte_grupo": source_group,
                            "ano": int(year),
                            "n_min": cutoff,
                            "indicador": indicator,
                            "indicador_rotulo": label,
                            "nota": score,
                            "nota_rotulo": SCORE_LABELS[score],
                            **result,
                        }
                    )
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    context_columns = sorted(
        {
            *ANNUAL_INDICATORS,
            *(column for items in CENSUS_ANCHORS.values() for column in items),
        }
    )
    context = pd.read_parquet(
        MUNICIPAL_SOURCE,
        columns=[
            "ano_enem",
            "codigo_ibge",
            "municipio",
            "uf",
            "regiao",
            *context_columns,
        ],
    )
    context["codigo_ibge"] = normalize_municipality_code(context.codigo_ibge)
    if context.duplicated(["ano_enem", "codigo_ibge"]).any():
        raise ValueError("Duplicate municipal context keys")

    aggregates, coverage = [], []
    for year in YEARS:
        source = ELIGIBLE / f"cadastro_elegivel_{year}.parquet"
        eligible = pd.read_parquet(source, columns=["CO_MUNICIPIO_ESC", *SCORES])
        municipal = aggregate_year(eligible, year)
        matched = municipal.merge(
            context[context.ano_enem.eq(year)].drop(columns="ano_enem"),
            how="inner",
            on="codigo_ibge",
            validate="one_to_one",
        )
        if len(matched) != len(municipal):
            raise ValueError(
                "Municipal context mismatch in "
                f"{year}: {len(municipal)} vs {len(matched)}"
            )
        aggregates.append(matched)
        row = {
            "ano": year,
            "n_elegiveis": len(eligible),
            "n_com_codigo_municipio": int(eligible.CO_MUNICIPIO_ESC.notna().sum()),
            "n_vinculados": int(matched.n.sum()),
            "municipios_vinculados": len(matched),
        }
        for cutoff in CUTOFFS:
            selected = matched[matched.n.ge(cutoff)]
            row[f"municipios_n{cutoff}"] = len(selected)
            row[f"candidatos_n{cutoff}"] = int(selected.n.sum())
            row[f"pct_vinculados_n{cutoff}"] = 100 * selected.n.sum() / matched.n.sum()
        coverage.append(row)

    municipal = pd.concat(aggregates, ignore_index=True)
    municipal.to_parquet(OUT / "municipios_2010_2023.parquet", index=False)
    municipal.to_csv(
        OUT / "municipios_2010_2023.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(coverage).to_csv(
        OUT / "cobertura_anual.csv", index=False, encoding="utf-8-sig"
    )

    rows = association_rows(municipal, ANNUAL_INDICATORS, "anual")
    for year, indicators in CENSUS_ANCHORS.items():
        rows.extend(
            association_rows(
                municipal[municipal.ano.eq(year)], indicators, f"censitario_{year}"
            )
        )

    ideb = extract_ideb_panel()
    ideb_municipal = municipal.merge(
        ideb, how="left", on=["ano", "codigo_ibge"], validate="one_to_one"
    )
    rows.extend(association_rows(ideb_municipal, IDEB_INDICATORS, "ideb_bienal"))
    correlations = pd.DataFrame(rows)
    correlations.to_csv(
        OUT / "correlacoes_municipais_2010_2023.csv",
        index=False,
        encoding="utf-8-sig",
    )

    manifest = {
        "anos": list(YEARS),
        "unidade": "municipio da escola x ano",
        "populacao_observada": (
            "cadastros elegiveis integrais da decisao 004; cinco notas completas"
        ),
        "n_min_principal": 30,
        "n_min_sensibilidades": [20, 50],
        "estimandos": ["pearson", "spearman", "pearson_ponderado_n"],
        "modelos_econometricos": 0,
        "input_municipal_sha256": sha256(MUNICIPAL_SOURCE),
        "input_eligible_sha256": {
            str(year): sha256(ELIGIBLE / f"cadastro_elegivel_{year}.parquet")
            for year in YEARS
        },
        "output_municipal_sha256": sha256(OUT / "municipios_2010_2023.parquet"),
        "output_correlations_sha256": sha256(
            OUT / "correlacoes_municipais_2010_2023.csv"
        ),
        "python": platform.python_version(),
        "versions": {
            name: importlib.metadata.version(name)
            for name in ["numpy", "pandas", "scipy", "pyarrow"]
        },
    }
    write_json(OUT / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "municipios_ano": len(municipal),
                "correlacoes": len(correlations),
                "anos": [min(YEARS), max(YEARS)],
                "saida": str(OUT),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
