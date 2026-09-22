"""Build annual ENEM analytical frames, auditable stratified samples and diagnostics."""

from __future__ import annotations

import argparse
import json
import unicodedata

import duckdb
import numpy as np
import pandas as pd

from enem_analysis.data.acquire import ROOT, write_json
from enem_analysis.statistics.sampling import allocate, size_for_proportion

OUT = ROOT / "data/processed/sampling"
SCORES = ["NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT", "NU_NOTA_REDACAO"]
REGIONS = {
    "1": "Norte",
    "2": "Nordeste",
    "3": "Sudeste",
    "4": "Sul",
    "5": "Centro-Oeste",
}
RACES = {"1": "Branca", "2": "Preta", "3": "Parda", "4": "Amarela", "5": "Indigena"}
SEED = 20260920


def dictionary(year: int) -> tuple[dict, dict]:
    audit = json.loads(
        (ROOT / f"docs/sources/enem/{year}.json").read_text(encoding="utf-8")
    )
    books = json.loads(
        (ROOT / f"docs/sources/enem/dictionary_{year}.json").read_text(encoding="utf-8")
    )
    sheet = max(
        (s for b in books.values() for s in b.values()),
        key=lambda s: len(set(s["variables"]) & set(audit["columns"])),
    )
    return sheet["variables"], audit


def question_column(
    variables: dict, columns: list[str], needles: list[str]
) -> tuple[str, str]:
    candidates = [
        (k, str(v["description"]))
        for k, v in variables.items()
        if k.startswith("Q")
        and any(t in str(v["description"]).lower() for t in needles)
    ]
    if len(candidates) != 1:
        raise ValueError(f"Ambiguous question: {needles}: {candidates}")
    name, description = candidates[0]
    matching = [c for c in columns if c.startswith("Q") and int(c[1:]) == int(name[1:])]
    if len(matching) != 1:
        raise ValueError(f"No unique CSV question for {name}")
    return matching[0], name


def prepare(year: int) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    cached = OUT / f"plano_{year}.json"
    if cached.exists() and (
        year != 2012
        or json.loads(cached.read_text(encoding="utf-8")).get("sex_harmonized")
    ):
        print(f"EXISTS ENEM sampling {year}", flush=True)
        return json.loads((OUT / f"plano_{year}.json").read_text(encoding="utf-8"))
    variables, audit = dictionary(year)
    essay_codes = [
        str(c["code"])
        for c in variables["TP_STATUS_REDACAO"]["categories"]
        if any(t in str(c["label"]).lower() for t in ["sem problemas", "presente"])
    ]
    if len(essay_codes) != 1:
        raise ValueError(f"Ambiguous regular essay status for {year}: {essay_codes}")
    mappings = {}
    needles = {
        "renda": ["renda familiar mensal", "renda mensal de sua família"],
        "pai": ["seu pai"],
        "mae": ["sua mãe"],
        "moradores": ["quantas pessoas moram", "pessoas moram atualmente"],
        "internet": ["acesso à internet"],
        "computador": ["tem computador", "microcomputador"],
    }
    for role, terms in needles.items():
        try:
            mappings[role] = question_column(variables, audit["columns"], terms)
        except ValueError:
            if role in {"renda", "pai", "mae"}:
                # Occupation mentions a parent too; education must refer to studies.
                subset = {
                    k: v
                    for k, v in variables.items()
                    if any(
                        t in str(v["description"]).lower()
                        for t in ["estudou", "escolaridade"]
                    )
                }
                mappings[role] = question_column(subset, audit["columns"], terms)
    income_col, income_dict = mappings["renda"]
    # Keep original income categories within year; no unsupported temporal recoding.
    selected = [
        "NU_INSCRICAO",
        "TP_COR_RACA",
        "TP_SEXO",
        "TP_ESCOLA",
        "TP_FAIXA_ETARIA",
        "CO_MUNICIPIO_ESC",
        "CO_UF_ESC",
        "CO_MUNICIPIO_PROVA",
        "TP_DEPENDENCIA_ADM_ESC",
        "TP_LOCALIZACAO_ESC",
        *SCORES,
    ]
    selected = list(
        dict.fromkeys(
            [c for c in selected if c in audit["columns"]]
            + [v[0] for v in mappings.values()]
        )
    )
    source = ROOT / f"data/processed/enem/year={year}/participantes.parquet"
    db = duckdb.connect()
    db.execute("SET memory_limit='2GB'")
    db.execute("SET threads=2")
    db.read_parquet(str(source)).create_view("source")
    steps = [
        ("inscritos", "TRUE"),
        ("concluintes_declarados", "TP_ST_CONCLUSAO='2'"),
        ("ensino_regular", "TP_ENSINO='1'"),
    ]
    if "IN_TREINEIRO" in audit["columns"]:
        steps.append(("nao_treineiro", "IN_TREINEIRO='0'"))
    steps += [
        (
            "presentes_quatro_provas",
            " AND ".join(f"TP_PRESENCA_{a}='1'" for a in ["CN", "CH", "LC", "MT"]),
        ),
        (
            "notas_numericas",
            " AND ".join(f"try_cast({c} AS DOUBLE) IS NOT NULL" for c in SCORES),
        ),
        ("redacao_regular", f"TP_STATUS_REDACAO='{essay_codes[0]}'"),
    ]
    filters, flow = [], []
    for name, condition in steps:
        filters.append(condition)
        n = db.execute(
            "SELECT count(*) FROM source WHERE " + " AND ".join(filters)
        ).fetchone()[0]
        flow.append(
            {
                "stage": name,
                "remaining": n,
                "excluded_since_previous": flow[-1]["remaining"] - n if flow else 0,
            }
        )
    frame = db.execute(
        "SELECT " + ",".join(selected) + " FROM source WHERE " + " AND ".join(filters)
    ).fetchdf()
    db.close()
    if frame.empty:
        raise ValueError(f"Empty analytical frame {year}")
    frame["ano"] = year
    frame["raca"] = frame.TP_COR_RACA.map(RACES).fillna("Nao_declarada")
    sex_codes = {
        str(c["code"]): str(c["label"]).strip()[0].upper()
        for c in variables["TP_SEXO"]["categories"]
    }
    frame["sexo"] = frame.TP_SEXO.map(sex_codes).fillna("Nao_declarado")
    frame["regiao_escola"] = frame.CO_UF_ESC.str[0].map(REGIONS).fillna("Sem_escola")
    frame["renda_categoria"] = frame[income_col].fillna("Sem_resposta")
    if "TP_ESCOLA" in frame:
        school_codes = {
            str(c["code"]): unicodedata.normalize("NFKD", str(c["label"]).strip())
            .encode("ascii", "ignore")
            .decode()
            for c in variables["TP_ESCOLA"]["categories"]
            if str(c["label"]).strip() in {"Pública", "Privada"}
        }
        frame["escola"] = frame.TP_ESCOLA.map(school_codes).fillna("Nao_informada")
    else:
        frame["escola"] = "Nao_informada"
    for score in SCORES:
        frame[score] = pd.to_numeric(frame[score])
    stratum_cols = ["regiao_escola", "raca", "sexo", "renda_categoria"]
    frame["estrato"] = frame[stratum_cols[0]].str.cat(
        [frame[c] for c in stratum_cols[1:]], sep="|"
    )
    groups = (
        frame.groupby(["estrato", *stratum_cols], sort=True)
        .size()
        .rename("N_h")
        .reset_index()
    )
    size = min(20000, len(frame))
    groups["n_h"] = allocate(groups.N_h.to_numpy(), size)
    groups["pi_h"] = groups.n_h / groups.N_h
    groups["peso_desenho"] = 1 / groups.pi_h
    groups["ano"] = year
    rng = np.random.default_rng(SEED + year)
    allocations = groups.set_index("estrato").n_h
    selections = []
    for stratum, part in frame.groupby("estrato", sort=True):
        # Sorting by registration fixes the frame order for reproducibility.
        ordered = part.sort_values("NU_INSCRICAO")
        selections.append(
            ordered.iloc[
                rng.choice(len(ordered), int(allocations[stratum]), replace=False)
            ]
        )
    sample = pd.concat(selections, ignore_index=True).merge(
        groups[["estrato", "N_h", "n_h", "pi_h", "peso_desenho"]],
        on="estrato",
        validate="many_to_one",
    )
    frame.to_parquet(
        OUT / f"cadastro_elegivel_{year}.parquet", index=False, compression="zstd"
    )
    sample.to_parquet(
        OUT / f"amostra_estratificada_{year}.parquet", index=False, compression="zstd"
    )
    groups.to_csv(OUT / f"alocacao_{year}.csv", index=False, encoding="utf-8-sig")
    scenarios = [
        {
            "ano": year,
            "N_elegivel": len(frame),
            "margem_pp": 100 * margin,
            "deff_planejado": d,
            "n": size_for_proportion(len(frame), margin, d),
        }
        for margin in [0.02, 0.01]
        for d in [1, 1.5, 2, 3]
    ]
    result = {
        "sex_harmonized": True,
        "year": year,
        "flow": flow,
        "N_eligible": len(frame),
        "n_selected": len(sample),
        "seed": SEED + year,
        "stratification": stratum_cols,
        "strata_occupied": len(groups),
        "strata_with_less_than_5_in_frame": int(groups.N_h.lt(5).sum()),
        "strata_with_less_than_5_in_sample": int(groups.n_h.lt(5).sum()),
        "strata_certainty": int(groups.N_h.eq(groups.n_h).sum()),
        "max_pi": float(groups.pi_h.max()),
        "min_pi": float(groups.pi_h.min()),
        "kish_design_weights": float(
            len(sample)
            * np.sum(sample.peso_desenho**2)
            / sample.peso_desenho.sum() ** 2
        ),
        "missing_race": int(frame.raca.eq("Nao_declarada").sum()),
        "missing_school_region": int(frame.regiao_escola.eq("Sem_escola").sum()),
        "sd_math": float(frame.NU_NOTA_MT.std()),
        "scenarios": scenarios,
        "question_mapping": {
            k: {"csv": v[0], "dictionary": v[1], **variables[v[1]]}
            for k, v in mappings.items()
        },
        "income_categories": variables[income_dict]["categories"],
        "residence_available": False,
        "selection_scope": "eligible ENEM only",
    }
    result["essay_status_code"] = essay_codes[0]
    write_json(OUT / f"plano_{year}.json", result)
    print(
        f"ENEM {year}: N={len(frame):,}, n={len(sample):,}, strata={len(groups)}",
        flush=True,
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", nargs="+", type=int, default=list(range(2010, 2024)))
    args = parser.parse_args()
    for year in args.years:
        prepare(year)


if __name__ == "__main__":
    main()
