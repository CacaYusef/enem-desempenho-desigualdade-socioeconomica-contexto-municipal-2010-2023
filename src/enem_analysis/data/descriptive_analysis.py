"""Run the pre-specified descriptive analysis without changing the sample."""

from __future__ import annotations

import importlib.metadata
import json
import platform

import duckdb
import numpy as np
import pandas as pd

from enem_analysis.data.acquire import ROOT, sha256, write_json
from enem_analysis.data.sampling_plan import OUT as SAMPLE
from enem_analysis.data.sampling_plan import SCORES, dictionary
from enem_analysis.statistics.descriptive import weighted_correlation, weighted_summary

OUT = ROOT / "data/processed/descriptive"
SCORE_NAMES = dict(
    zip(
        SCORES,
        ["Natureza", "Humanas", "Linguagens", "Matemática", "Redação"],
        strict=True,
    )
)
MUNICIPAL = [
    "pib_per_capita_reais",
    "educ_abandono_medio_pct",
    "populacao",
    "renda_domiciliar_per_capita_censo2022_reais",
    "renda_per_capita_atlas_reais2010",
    "gini_atlas",
    "idhm_educacao",
]
INCOME_2023 = {
    **dict.fromkeys("AB", "Até R$ 1.320"),
    **dict.fromkeys("CD", "R$ 1.320–2.640"),
    **dict.fromkeys("EFGH", "R$ 2.640–6.600"),
    **dict.fromkeys("IJKLMNOPQ", "Acima de R$ 6.600"),
}
INCOME_ORDER = list(dict.fromkeys(INCOME_2023.values()))


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(rows, name):
    pd.DataFrame(rows).to_csv(OUT / name, index=False, encoding="utf-8-sig")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = SAMPLE / "amostra_enem_2010_2023.parquet"
    source_m = ROOT / "data/processed/municipal/base_municipio_ano.parquet"
    sample = pd.read_parquet(source)
    assert len(sample) == 280000
    assert not sample.duplicated(["ano", "NU_INSCRICAO"]).any()
    municipality = pd.read_parquet(source_m)[["codigo_ibge", "ano_enem", *MUNICIPAL]]
    assert not municipality.duplicated(["codigo_ibge", "ano_enem"]).any()
    # Never alter the original municipality table or its residence placeholders.
    sample = sample.merge(
        municipality,
        how="left",
        left_on=["CO_MUNICIPIO_ESC", "ano"],
        right_on=["codigo_ibge", "ano_enem"],
        validate="many_to_one",
        indicator="vinculo",
    )
    assert len(sample) == 280000
    all_stats, quality, frequencies, groups, codes, coverage, sensitivity = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    for year, part in sample.groupby("ano", sort=True):
        plan = read_json(SAMPLE / f"plano_{year}.json")
        assert len(part) == 20000
        assert np.isclose(part.peso_desenho.sum(), plan["N_eligible"])
        definitions, _ = dictionary(year)
        annual_fields = [
            "TP_COR_RACA",
            "TP_SEXO",
            "TP_FAIXA_ETARIA",
            "TP_ESCOLA",
            "TP_DEPENDENCIA_ADM_ESC",
            "TP_LOCALIZACAO_ESC",
        ]
        for role, mapping in plan["question_mapping"].items():
            annual_fields.append(mapping["csv"])
            labels = {
                str(c["code"]): str(c["label"]).strip() for c in mapping["categories"]
            }
            sample.loc[part.index, role + "_rotulo"] = (
                part[mapping["csv"]].map(labels).fillna("Sem resposta")
            )
        part = sample.loc[part.index].copy()
        raw_definitions = {k: definitions[k] for k in annual_fields if k in definitions}
        for mapping in plan["question_mapping"].values():
            raw_definitions[mapping["csv"]] = {
                "description": mapping["description"],
                "categories": mapping["categories"],
            }
        for field in [*annual_fields, "CO_MUNICIPIO_ESC", *SCORES]:
            if (
                field not in part
                or field not in definitions
                and field not in raw_definitions
                and field not in SCORES
                and field != "CO_MUNICIPIO_ESC"
            ):
                continue
            values = part[field]
            missing = values.isna()
            invalid = pd.Series(False, index=part.index)
            nonresponse = pd.Series(False, index=part.index)
            if field in raw_definitions:
                definition = raw_definitions[field]
                cats = {
                    str(c["code"]): str(c["label"]).strip()
                    for c in definition.get("categories", [])
                }
                if cats:
                    invalid = values.notna() & ~values.isin(cats)
                    unknown_codes = [
                        c
                        for c, lab in cats.items()
                        if any(
                            t in lab.lower()
                            for t in [
                                "não sei",
                                "não declarado",
                                "não dispõe",
                                "não informado",
                                "ignorado",
                            ]
                        )
                    ]
                    nonresponse = values.isin(unknown_codes)
                codes.extend(
                    {"ano": year, "coluna": field, "codigo": c, "rotulo": lab}
                    for c, lab in cats.items()
                )
            if field in SCORES:
                numeric = pd.to_numeric(values, errors="raise")
                invalid = values.notna() & (~np.isfinite(numeric) | numeric.lt(0))
                if field == "NU_NOTA_REDACAO":
                    invalid |= numeric.gt(1000)
            quality.append(
                {
                    "ano": year,
                    "variavel": field,
                    "n": len(part),
                    "n_ausente": int(missing.sum()),
                    "n_nao_declarado": int(nonresponse.sum()),
                    "n_codigo_ou_valor_invalido": int(invalid.sum()),
                    "pct_ausente_ponderado": 100
                    * part.loc[missing, "peso_desenho"].sum()
                    / part.peso_desenho.sum(),
                    "pct_nao_declarado_ponderado": 100
                    * part.loc[nonresponse, "peso_desenho"].sum()
                    / part.peso_desenho.sum(),
                }
            )
        for score in SCORES:
            all_stats.append(
                {
                    "ano": year,
                    "variavel": score,
                    **weighted_summary(part[score], part.peso_desenho),
                }
            )
            eligible = part.peso_calibrado_proxy.notna()
            if eligible.any():
                for label, col in [
                    ("desenho_mesmo_dominio", "peso_desenho"),
                    ("calibrado", "peso_calibrado_proxy"),
                ]:
                    sensitivity.append(
                        {
                            "ano": year,
                            "variavel": score,
                            "peso": label,
                            **weighted_summary(
                                part.loc[eligible, score], part.loc[eligible, col]
                            ),
                        }
                    )
        group_fields = ["raca", "sexo", "escola", "regiao_escola", "TP_FAIXA_ETARIA"]
        group_fields += [
            role + "_rotulo" for role in plan["question_mapping"] if role != "moradores"
        ]
        for field in group_fields:
            for category, subset in part.groupby(field, dropna=False, sort=True):
                n, w = len(subset), subset.peso_desenho.sum()
                frequencies.append(
                    {
                        "ano": year,
                        "variavel": field,
                        "categoria": category,
                        "n": n,
                        "total_estimado": w,
                        "pct_bruto": 100 * n / len(part),
                        "pct_ponderado": 100 * w / part.peso_desenho.sum(),
                    }
                )
                for score in SCORES:
                    groups.append(
                        {
                            "ano": year,
                            "grupo": field,
                            "categoria": category,
                            "variavel": score,
                            **weighted_summary(subset[score], subset.peso_desenho),
                        }
                    )
        for indicator in MUNICIPAL:
            available = part[indicator].notna()
            coverage.append(
                {
                    "ano": year,
                    "indicador": indicator,
                    "n_amostra": len(part),
                    "n_sem_chave": int(part.CO_MUNICIPIO_ESC.isna().sum()),
                    "n_chave_sem_correspondencia": int(
                        (part.CO_MUNICIPIO_ESC.notna() & part.vinculo.ne("both")).sum()
                    ),
                    "n_indicador_observado": int(available.sum()),
                    "pct_coberto_ponderado": 100
                    * part.loc[available, "peso_desenho"].sum()
                    / part.peso_desenho.sum(),
                    "municipios_observados": part.loc[
                        available, "CO_MUNICIPIO_ESC"
                    ].nunique(),
                }
            )
    s23 = sample[sample.ano.eq(2023)].copy()
    s23["renda_grupo"] = s23.Q006.map(INCOME_2023).fillna("Sem resposta")
    s23["moradores_num"] = pd.to_numeric(s23.Q005, errors="raise")
    sample.loc[s23.index, "renda_grupo"] = s23.renda_grupo
    sample.loc[s23.index, "moradores_num"] = s23.moradores_num
    for category, subset in s23.groupby("renda_grupo"):
        frequencies.append(
            {
                "ano": 2023,
                "variavel": "renda_grupo",
                "categoria": category,
                "n": len(subset),
                "total_estimado": subset.peso_desenho.sum(),
                "pct_bruto": 100 * len(subset) / len(s23),
                "pct_ponderado": 100
                * subset.peso_desenho.sum()
                / s23.peso_desenho.sum(),
            }
        )
        for score in SCORES:
            groups.append(
                {
                    "ano": 2023,
                    "grupo": "renda_grupo",
                    "categoria": category,
                    "variavel": score,
                    **weighted_summary(subset[score], subset.peso_desenho),
                }
            )
    for field in ["moradores_num", *MUNICIPAL]:
        all_stats.append(
            {
                "ano": 2023,
                "variavel": field,
                **weighted_summary(s23[field], s23.peso_desenho),
            }
        )
    correlations = []
    for year in [2010, 2022, 2023]:
        part = sample[sample.ano.eq(year)].copy()
        fields = [*SCORES, *(m for m in MUNICIPAL if part[m].notna().any())]
        if year == 2023:
            fields.append("moradores_num")
        for i, a in enumerate(fields):
            for b in fields[i:]:
                correlation, n, total = weighted_correlation(
                    part[a], part[b], part.peso_desenho
                )
                correlations.append(
                    {
                        "ano": year,
                        "variavel_a": a,
                        "variavel_b": b,
                        "r_pearson_ponderado": correlation,
                        "n_pares": n,
                        "peso_pares": total,
                    }
                )
    contingency = []
    for (income, school), subset in s23.groupby(["renda_grupo", "escola"]):
        row_total = s23.loc[s23.renda_grupo.eq(income), "peso_desenho"].sum()
        contingency.append(
            {
                "renda_grupo": income,
                "escola": school,
                "n": len(subset),
                "total_estimado": subset.peso_desenho.sum(),
                "pct_dentro_renda": 100 * subset.peso_desenho.sum() / row_total,
            }
        )
    selection = []
    for label, subset in [
        ("Escola identificada", s23[s23.vinculo.eq("both")]),
        ("Escola não vinculada", s23[s23.vinculo.ne("both")]),
    ]:
        for score in ["NU_NOTA_MT", "NU_NOTA_REDACAO"]:
            selection.append(
                {
                    "dominio": label,
                    "variavel": score,
                    **weighted_summary(subset[score], subset.peso_desenho),
                }
            )
    consistency = {
        "duplicate_inscription_year": int(
            sample.duplicated(["ano", "NU_INSCRICAO"]).sum()
        ),
        "municipality_uf_disagreement": int(
            (
                sample.CO_MUNICIPIO_ESC.notna()
                & sample.CO_UF_ESC.notna()
                & sample.CO_MUNICIPIO_ESC.str[:2].ne(sample.CO_UF_ESC)
            ).sum()
        ),
        "school_type_administration_disagreement_2023": int(
            (
                (s23.escola.eq("Publica") & s23.TP_DEPENDENCIA_ADM_ESC.eq("4"))
                | (
                    s23.escola.eq("Privada")
                    & s23.TP_DEPENDENCIA_ADM_ESC.isin(["1", "2", "3"])
                )
            ).sum()
        ),
        "school_type_administration_compared_2023": int(
            s23.TP_DEPENDENCIA_ADM_ESC.isin(["1", "2", "3", "4"]).sum()
        ),
    }
    # Check unusual zeros against the untouched full annual derivative.
    zeros = s23[s23[SCORES].eq(0).any(axis=1)][["NU_INSCRICAO"]]
    db = duckdb.connect()
    db.register("zero_ids", zeros)
    source23 = ROOT / "data/processed/enem/year=2023/participantes.parquet"
    original = db.execute(
        "SELECT p.* FROM read_parquet(?) p JOIN zero_ids z USING (NU_INSCRICAO)",
        [str(source23)],
    ).fetchdf()
    db.close()
    zero_audit = []
    for field in SCORES:
        zero_mask = s23[field].eq(0)
        raw_count = int(pd.to_numeric(original[field], errors="raise").eq(0).sum())
        assert raw_count == int(zero_mask.sum())
        zero_audit.append(
            {
                "ano": 2023,
                "variavel": field,
                "n_zero": raw_count,
                "pct_zero_ponderado": 100
                * s23.loc[zero_mask, "peso_desenho"].sum()
                / s23.peso_desenho.sum(),
                "conferido_na_base_integral": True,
            }
        )
    consistency["zero_rows_original_presence_all_1"] = bool(
        original[[f"TP_PRESENCA_{a}" for a in ["CN", "CH", "LC", "MT"]]]
        .eq("1")
        .all()
        .all()
    )
    save(zero_audit, "zeros_2023.csv")
    for rows, name in [
        (all_stats, "resumos_anuais.csv"),
        (quality, "qualidade.csv"),
        (frequencies, "frequencias.csv"),
        (groups, "resumos_grupos.csv"),
        (codes, "codigos_anuais.csv"),
        (coverage, "cobertura_contextual.csv"),
        (sensitivity, "sensibilidade_pesos.csv"),
        (correlations, "correlacoes.csv"),
        (contingency, "contingencia_renda_escola_2023.csv"),
        (selection, "selecao_contextual_2023.csv"),
    ]:
        save(rows, name)
    sample.to_parquet(
        OUT / "amostra_contexto_escola.parquet", index=False, compression="zstd"
    )
    manifest = {
        "rows": len(sample),
        "columns": len(sample.columns),
        "years": list(range(2010, 2024)),
        "input_sample_sha256": sha256(source),
        "input_municipal_sha256": sha256(source_m),
        "python": platform.python_version(),
        "libraries": {
            p: importlib.metadata.version(p)
            for p in ["pandas", "numpy", "matplotlib", "pyarrow"]
        },
        "weight": "peso_desenho",
        "detailed_year": 2023,
        "municipal_join": "school municipality, exact year, left many-to-one",
        "removed_rows": 0,
        "imputed_values": 0,
        "consistency": consistency,
        "score_invalid_count": sum(
            q["n_codigo_ou_valor_invalido"] for q in quality if q["variavel"] in SCORES
        ),
    }
    write_json(OUT / "manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
