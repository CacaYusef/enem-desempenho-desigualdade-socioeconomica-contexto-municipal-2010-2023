"""Complete ENEM 2023 frame and socioeconomic/municipal/regional descriptives."""

from __future__ import annotations

import importlib.metadata
import platform

import duckdb
import numpy as np
import pandas as pd

from enem_analysis.data.acquire import ROOT, sha256, write_json
from enem_analysis.data.sampling_plan import dictionary
from enem_analysis.data.territorial_context import INDICATORS, OUT, REGIONS
from enem_analysis.statistics.territorial import association, quintile_codes, summary

FIELDS = [
    "NU_INSCRICAO",
    "TP_ST_CONCLUSAO",
    "TP_ENSINO",
    "IN_TREINEIRO",
    "TP_COR_RACA",
    "TP_SEXO",
    "TP_FAIXA_ETARIA",
    "TP_ESCOLA",
    "TP_DEPENDENCIA_ADM_ESC",
    "TP_LOCALIZACAO_ESC",
    "CO_MUNICIPIO_ESC",
    "CO_UF_ESC",
    "Q001",
    "Q002",
    "Q005",
    "Q006",
    "Q024",
    "Q025",
]
AREAS = ["MT", "CN", "CH", "LC"]
SCORES = [f"NU_NOTA_{a}" for a in AREAS] + ["NU_NOTA_REDACAO"]
LABELS = {
    "Q006": "renda",
    "Q001": "pai",
    "Q002": "mae",
    "TP_COR_RACA": "raca",
    "TP_SEXO": "sexo",
    "TP_FAIXA_ETARIA": "idade",
    "TP_ESCOLA": "escola",
    "TP_DEPENDENCIA_ADM_ESC": "dependencia",
    "TP_LOCALIZACAO_ESC": "localizacao",
    "Q024": "computador",
    "Q025": "internet",
}
INCOME_GROUPS = {
    **dict.fromkeys("AB", "Até R$ 1.320"),
    **dict.fromkeys("CD", "R$ 1.320,01–2.640"),
    **dict.fromkeys("EFGH", "R$ 2.640,01–6.600"),
    **dict.fromkeys("IJKLMNOPQ", "Acima de R$ 6.600"),
}
INCOME_ORDER = list(dict.fromkeys(INCOME_GROUPS.values()))
UF_REGIONS = {
    "11": "Norte",
    "12": "Norte",
    "13": "Norte",
    "14": "Norte",
    "15": "Norte",
    "16": "Norte",
    "17": "Norte",
    "21": "Nordeste",
    "22": "Nordeste",
    "23": "Nordeste",
    "24": "Nordeste",
    "25": "Nordeste",
    "26": "Nordeste",
    "27": "Nordeste",
    "28": "Nordeste",
    "29": "Nordeste",
    "31": "Sudeste",
    "32": "Sudeste",
    "33": "Sudeste",
    "35": "Sudeste",
    "41": "Sul",
    "42": "Sul",
    "43": "Sul",
    "50": "Centro-Oeste",
    "51": "Centro-Oeste",
    "52": "Centro-Oeste",
    "53": "Centro-Oeste",
}


def save(rows, name):
    (rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)).to_csv(
        OUT / name, index=False, encoding="utf-8-sig"
    )


def eligibility_mask(frame):
    note = pd.to_numeric(frame.NU_NOTA_MT, errors="coerce")
    return (
        frame.TP_ST_CONCLUSAO.eq("2")
        & frame.TP_ENSINO.eq("1")
        & frame.IN_TREINEIRO.eq("0")
        & frame.TP_PRESENCA_MT.eq("1")
        & np.isfinite(note)
        & note.ge(0)
    ).fillna(False)


def build_frame():
    definitions, inventory = dictionary(2023)
    for field, code, text in [
        ("TP_ST_CONCLUSAO", 2, "2023"),
        ("TP_ENSINO", 1, "Regular"),
        ("IN_TREINEIRO", 0, "Não"),
        ("TP_PRESENCA_MT", 1, "Presente"),
    ]:
        label = next(
            c["label"] for c in definitions[field]["categories"] if c["code"] == code
        )
        if text not in label:
            raise ValueError(f"Eligibility dictionary drift: {field}")
    source = ROOT / "data/processed/enem/year=2023/participantes.parquet"
    db = duckdb.connect()
    db.execute("SET memory_limit='2GB'")
    db.read_parquet(str(source)).create_view("source")
    clauses = [
        ("Inscritos", "TRUE"),
        ("Conclusão declarada em 2023", "TP_ST_CONCLUSAO='2'"),
        ("Ensino regular declarado", "TP_ENSINO='1'"),
        ("Não treineiro", "IN_TREINEIRO='0'"),
        ("Presente em matemática", "TP_PRESENCA_MT='1'"),
        (
            "Nota MT numérica, finita e não negativa",
            "isfinite(try_cast(NU_NOTA_MT AS DOUBLE)) "
            "AND try_cast(NU_NOTA_MT AS DOUBLE)>=0",
        ),
    ]
    conditions, flow, previous = [], [], None
    for label, rule in clauses:
        conditions.append(rule)
        n = db.execute(
            "SELECT count(*) FROM source WHERE " + " AND ".join(conditions)
        ).fetchone()[0]
        flow.append(
            {
                "etapa": label,
                "n_retido": n,
                "n_excluido_etapa": 0 if previous is None else previous - n,
            }
        )
        previous = n
    save(flow, "fluxo_elegibilidade.csv")
    fields = FIELDS + [f"TP_PRESENCA_{a}" for a in AREAS] + ["TP_STATUS_REDACAO"]
    sql_fields = fields + [f"try_cast({s} AS DOUBLE) AS {s}" for s in SCORES]
    frame = db.execute(
        "SELECT "
        + ",".join(sql_fields)
        + " FROM source WHERE "
        + " AND ".join(conditions)
    ).fetchdf()
    db.close()
    if len(frame) != flow[-1]["n_retido"] or frame.NU_INSCRICAO.duplicated().any():
        raise AssertionError("Frame count/identifier validation failed")
    if not eligibility_mask(frame).all():
        raise AssertionError("Independent eligibility check failed")
    quality = []
    for field in fields:
        cats = {
            str(c["code"]): c["label"].strip()
            for c in definitions.get(field, {}).get("categories", [])
        }
        unknown = [
            c
            for c, label in cats.items()
            if any(
                x in label.lower()
                for x in [
                    "não sei",
                    "não declarou",
                    "não declarado",
                    "não dispõe",
                    "não respondeu",
                ]
            )
        ]
        invalid = (
            frame[field].notna() & ~frame[field].isin(cats)
            if cats
            else pd.Series(False, index=frame.index)
        )
        quality.append(
            {
                "campo": field,
                "n": len(frame),
                "n_ausente": int(frame[field].isna().sum()),
                "n_nao_declarado": int(frame[field].isin(unknown).sum()),
                "n_invalido": int(invalid.sum()),
            }
        )
        if cats and invalid.any():
            raise ValueError(f"Invalid categories require review: {field}")
        if field in LABELS:
            frame[LABELS[field]] = (
                frame[field].map(cats).fillna("Sem informação").astype("category")
            )
        frame[field] = frame[field].astype("category")
    save(quality, "qualidade_individual.csv")
    write_json(
        OUT / "dicionario_individual.json",
        {k: definitions[k] for k in fields + SCORES if k in definitions},
    )
    frame["renda_grupo"] = (
        frame.Q006.map(INCOME_GROUPS)
        .astype("string")
        .fillna("Sem informação")
        .astype("category")
    )
    frame["moradores"] = pd.to_numeric(
        frame.Q005.astype("string"), errors="raise"
    ).astype(float)
    context = pd.read_parquet(OUT / "contexto_municipal.parquet")
    frame = frame.merge(
        context,
        how="left",
        left_on="CO_MUNICIPIO_ESC",
        right_on="codigo_ibge",
        validate="many_to_one",
        indicator="vinculo",
    )
    if len(frame) != previous:
        raise AssertionError("Context join changed population")
    uf_region = frame.CO_UF_ESC.astype("string").map(UF_REGIONS)
    frame["regiao"] = (
        frame.regiao.fillna(uf_region).fillna("Não identificada").astype("category")
    )
    if not frame.regiao.isin([*REGIONS, "Não identificada"]).all():
        raise ValueError("Unrecognized region would be omitted from regional tables")
    frame["cobertura"] = np.where(
        frame.vinculo.eq("both"),
        "Município conhecido",
        "Município ausente/não vinculado",
    )
    write_json(
        OUT / "frame_manifest.json",
        {
            "n_inscritos": flow[0]["n_retido"],
            "n_elegivel": len(frame),
            "n_vinculado": int(frame.vinculo.eq("both").sum()),
            "n_sem_codigo_municipio": int(frame.CO_MUNICIPIO_ESC.isna().sum()),
            "n_codigo_sem_vinculo": int(
                (frame.CO_MUNICIPIO_ESC.notna() & frame.vinculo.ne("both")).sum()
            ),
            "n_uf_municipio_divergente": int(
                (
                    frame.CO_MUNICIPIO_ESC.notna()
                    & frame.CO_UF_ESC.notna()
                    & frame.CO_MUNICIPIO_ESC.astype("string")
                    .str[:2]
                    .ne(frame.CO_UF_ESC.astype("string"))
                ).sum()
            ),
            "n_tipo_dependencia_divergente": int(
                (
                    (frame.TP_ESCOLA.eq("2") & frame.TP_DEPENDENCIA_ADM_ESC.eq("4"))
                    | (
                        frame.TP_ESCOLA.eq("3")
                        & frame.TP_DEPENDENCIA_ADM_ESC.isin(["1", "2", "3"])
                    )
                ).sum()
            ),
            "n_mt_zero": int(frame.NU_NOTA_MT.eq(0).sum()),
            "peso": 1,
            "pi_condicional": 1,
            "input_sha256": sha256(source),
            "context_sha256": sha256(OUT / "contexto_municipal.parquet"),
            "python": platform.python_version(),
            "versions": {
                p: importlib.metadata.version(p)
                for p in [
                    "pandas",
                    "numpy",
                    "duckdb",
                    "scipy",
                    "matplotlib",
                    "statsmodels",
                ]
            },
            "econometric_models": 0,
            "sample_draw": False,
            "score_composite": False,
        },
    )
    frame.to_parquet(OUT / "candidatos_2023.parquet", index=False, compression="zstd")
    return frame


def individual_tables(frame):
    rows, regions, coverage = [], [], []
    for region in ["Brasil", *REGIONS, "Não identificada"]:
        part = frame if region == "Brasil" else frame[frame.regiao.eq(region)]
        regions.append(
            {
                "regiao": region,
                **summary(part.NU_NOTA_MT),
                "pct_base": 100 * len(part) / len(frame),
            }
        )
        for field in [*LABELS.values(), "renda_grupo"]:
            for category, group in part.groupby(field, observed=True, dropna=False):
                rows.append(
                    {
                        "regiao": region,
                        "variavel": field,
                        "categoria": str(category),
                        "pct": 100 * len(group) / len(part),
                        **summary(group.NU_NOTA_MT),
                    }
                )
    save(rows, "grupos_individuais.csv")
    if sum(r["n"] for r in regions if r["regiao"] != "Brasil") != len(frame):
        raise AssertionError("Regional counts must conserve the complete frame")
    save(regions, "regioes.csv")
    for domain, part in frame.groupby("cobertura", observed=True):
        coverage.append(
            {
                "dominio": domain,
                "variavel": "NOTA_MT",
                "categoria": "Total",
                "pct": 100,
                **summary(part.NU_NOTA_MT),
            }
        )
        for field in ["regiao", *LABELS.values(), "renda_grupo"]:
            for category, group in part.groupby(field, observed=True, dropna=False):
                coverage.append(
                    {
                        "dominio": domain,
                        "variavel": field,
                        "categoria": str(category),
                        "pct": 100 * len(group) / len(part),
                        **summary(group.NU_NOTA_MT),
                    }
                )
    save(coverage, "comparacao_cobertura.csv")
    representation = []
    for field in ["regiao", "raca", "sexo", "renda"]:
        for cat, n in frame[field].value_counts(dropna=False).items():
            representation.append(
                {
                    "dimensao": field,
                    "grupo": cat,
                    "populacao_alvo_n": None,
                    "populacao_alvo_pct": None,
                    "alvo_status": (
                        "Sem referência exata e comparável de concluintes; "
                        "não inferir de PNAD residência/renda domiciliar"
                    ),
                    "base_elegivel_n": int(n),
                    "base_elegivel_pct": 100 * n / len(frame),
                    "amostra_bruta_n": int(n),
                    "amostra_bruta_pct": 100 * n / len(frame),
                    "amostra_ponderada_n": int(n),
                    "amostra_ponderada_pct": 100 * n / len(frame),
                    "pi_condicional": 1,
                    "peso": 1,
                }
            )
    save(representation, "representacao_populacoes.csv")
    # External proxy only; do not silently promote it to an exact target.
    p = pd.read_parquet(ROOT / "data/processed/sampling/pnad_proxy_2023.parquet")
    proxy = []
    for col in ["sexo", "raca"]:
        for cat, g in p.groupby(col, dropna=False):
            proxy.append(
                {
                    "dimensao": col,
                    "categoria": cat,
                    "n_pnad": len(g),
                    "total_proxy": g.weight.sum(),
                    "pct_proxy": 100 * g.weight.sum() / p.weight.sum(),
                    "universo": (
                        "Ensino médio regular séries 3/4, proxy de potenciais "
                        "concluintes, não conclusão comprovada"
                    ),
                    "uso": (
                        "Referência contextual; sem calibração; "
                        "incerteza PNAD não propagada"
                    ),
                }
            )
    save(proxy, "referencia_proxy_pnad.csv")
    robustness = []
    for region in ["Brasil", *REGIONS]:
        part = frame if region == "Brasil" else frame[frame.regiao.eq(region)]
        for score in SCORES:
            a = score.removeprefix("NU_NOTA_")
            valid = part[score].notna() & np.isfinite(part[score]) & part[score].ge(0)
            valid &= (
                part.TP_STATUS_REDACAO.eq("1")
                if a == "REDACAO"
                else part[f"TP_PRESENCA_{a}"].eq("1")
            )
            for inc in INCOME_ORDER:
                g = part[valid & part.renda_grupo.eq(inc)]
                robustness.append(
                    {
                        "regiao": region,
                        "area": a,
                        "renda_grupo": inc,
                        "universo": (
                            "Elegíveis MT; presença e nota da área, "
                            "redação regular quando REDACAO"
                        ),
                        **summary(g[score]),
                    }
                )
    save(robustness, "robustez_areas.csv")
    save(
        [
            {"variavel": "moradores", **summary(frame.moradores)},
            {"variavel": "matematica", **summary(frame.NU_NOTA_MT)},
        ],
        "resumos_individuais.csv",
    )


def municipal_tables(frame):
    linked = frame[frame.vinculo.eq("both")]
    g = linked.groupby("codigo_ibge", observed=True).NU_NOTA_MT
    municipal = g.agg(
        n="size", media="mean", mediana="median", dp="std", minimo="min", maximo="max"
    ).reset_index()
    # Match documented inverse-EDF quantiles and population descriptive variance.
    moments = (
        linked.groupby("codigo_ibge", observed=True)
        .NU_NOTA_MT.apply(lambda x: pd.Series(summary(x)))
        .unstack()
    )
    municipal = moments.reset_index()
    context = pd.read_parquet(OUT / "contexto_municipal.parquet")
    municipal = context.merge(
        municipal, how="inner", on="codigo_ibge", validate="one_to_one"
    )
    for field in ["Q006", "Q001", "Q002", "TP_COR_RACA", "TP_ESCOLA", "TP_SEXO"]:
        counts = (
            linked.groupby(["codigo_ibge", field], observed=True, dropna=False)
            .size()
            .unstack(fill_value=0)
        )
        counts.columns = [f"prop_{field}_{str(c)}" for c in counts.columns]
        counts = counts.div(counts.sum(axis=1), axis=0)
        municipal = municipal.merge(
            counts.reset_index(), how="left", on="codigo_ibge", validate="one_to_one"
        )
    public = (
        linked[linked.TP_ESCOLA.eq("2")]
        .groupby("codigo_ibge", observed=True)
        .NU_NOTA_MT.agg(n_publica="size", media_publica="mean")
    )
    municipal = municipal.merge(
        public, how="left", on="codigo_ibge", validate="one_to_one"
    )
    municipal.to_parquet(OUT / "municipios_2023.parquet", index=False)
    save(municipal, "municipios_2023.csv")
    correlations, distributions, thresholds, coverage = [], [], [], []
    for col in INDICATORS:
        observed = frame[col].notna()
        coverage.append(
            {
                "indicador": col,
                "n_candidatos": len(frame),
                "n_observado": int(observed.sum()),
                "pct_coberto": 100 * observed.mean(),
                "municipios_observados": frame.loc[observed, "codigo_ibge"].nunique(),
            }
        )
    for cutoff in [20, 30, 50]:
        chosen = municipal[municipal.n.ge(cutoff)]
        thresholds.append(
            {
                "n_min": cutoff,
                "n_municipios": len(chosen),
                "n_candidatos": int(chosen.n.sum()),
                "pct_vinculados": 100 * chosen.n.sum() / len(linked),
                "pct_elegiveis": 100 * chosen.n.sum() / len(frame),
            }
        )
        for region in ["Brasil", *REGIONS]:
            part = chosen if region == "Brasil" else chosen[chosen.regiao.eq(region)]
            for col in INDICATORS:
                distributions.append(
                    {
                        "n_min": cutoff,
                        "regiao": region,
                        "indicador": col,
                        **summary(part[col]),
                    }
                )
                correlations.append(
                    {
                        "n_min": cutoff,
                        "regiao": region,
                        "rede_candidatos": "Todas",
                        "indicador": col,
                        **association(part[col], part.media, part.n),
                    }
                )
                if col in ["ideb_2023", "saeb_mt_2023", "saeb_lp_2023"]:
                    pub = part[part.n_publica.ge(cutoff)]
                    correlations.append(
                        {
                            "n_min": cutoff,
                            "regiao": region,
                            "rede_candidatos": "Pública",
                            "indicador": col,
                            **association(pub[col], pub.media_publica, pub.n_publica),
                        }
                    )
    save(correlations, "associacoes_municipais.csv")
    save(distributions, "distribuicoes_contextuais.csv")
    save(thresholds, "sensibilidade_n_municipal.csv")
    save(coverage, "cobertura_contextual.csv")
    cuts_meta, quintiles = {}, []
    for col in ["ideb_2023", "pib_pc_2023", "renda_pc_2022"]:
        domain = municipal[municipal.n.ge(30) & municipal[col].notna()].copy()
        cuts = np.quantile(domain[col], [0.2, 0.4, 0.6, 0.8], method="inverted_cdf")
        domain["quintil"] = quintile_codes(domain[col], cuts)
        cuts_meta[col] = {
            "cortes": cuts.tolist(),
            "n_municipios": len(domain),
            "regra": (
                "inversa EDF municipal, n>=30; empates mantidos, "
                "limites direitos inclusivos"
            ),
        }
        lookup = domain.set_index("codigo_ibge").quintil
        frame["quintil_" + col] = frame.codigo_ibge.map(lookup)
        for region in ["Brasil", *REGIONS]:
            part = frame if region == "Brasil" else frame[frame.regiao.eq(region)]
            for q in range(1, 6):
                group = part[part["quintil_" + col].eq(q)]
                quintiles.append(
                    {
                        "indicador": col,
                        "regiao": region,
                        "quintil": q,
                        "municipios": group.codigo_ibge.nunique(),
                        **summary(group.NU_NOTA_MT),
                    }
                )
    save(quintiles, "desempenho_quintis.csv")
    write_json(OUT / "cortes_quintis.json", cuts_meta)
    frame.to_parquet(OUT / "candidatos_2023.parquet", index=False, compression="zstd")
    # Distinguish observed ENEM municipalities from all source territories.
    all_context = []
    for region in ["Brasil", *REGIONS]:
        part = context if region == "Brasil" else context[context.regiao.eq(region)]
        for col in INDICATORS:
            all_context.append(
                {
                    "regiao": region,
                    "indicador": col,
                    "universo": "Municípios do cadastro IBGE 2023 com indicador",
                    **summary(part[col]),
                }
            )
    save(all_context, "distribuicoes_contexto_integral.csv")
    return municipal


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frame = build_frame()
    print(f"Eligible frame: {len(frame):,}", flush=True)
    individual_tables(frame)
    municipal = municipal_tables(frame)
    print(
        f"Municipal frame: {len(municipal):,}; descriptive tables complete; "
        "no econometric model",
        flush=True,
    )


if __name__ == "__main__":
    main()
