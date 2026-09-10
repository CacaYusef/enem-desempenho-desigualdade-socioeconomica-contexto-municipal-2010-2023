"""Build an auditable municipal context panel with exact-year source values.

No ENEM cohort, statistical model, imputation, outlier removal or lag is chosen.
"""

from __future__ import annotations

import io
import json
import re
import zipfile

import pandas as pd

from enem_analysis.data.acquire import MANIFESTS, RAW, ROOT, sha256, write_json

OUT = ROOT / "data/processed/municipal"
DOCS = ROOT / "docs/sources/municipal"

# Positions and widths transcribed from the PDF bundled with the official TXT.
PIB_FIELDS = {
    "ano_dado": (1, 4),
    "regiao": (8, 12),
    "uf": (24, 2),
    "codigo_ibge": (47, 7),
    "municipio": (55, 40),
    "vab_agropecuaria_mil_reais": (821, 18),
    "vab_industria_mil_reais": (840, 18),
    "vab_servicos_mil_reais": (859, 18),
    "vab_administracao_publica_mil_reais": (878, 18),
    "vab_total_mil_reais": (897, 18),
    "impostos_liquidos_mil_reais": (916, 18),
    "pib_mil_reais": (935, 18),
    "pib_per_capita_reais": (954, 18),
}
PIB_NUMERIC = list(PIB_FIELDS)[5:]
IPEA_ALIASES = {
    "ADH_IDHM": "idhm",
    "ADH_IDHM_E": "idhm_educacao",
    "ADH_RDPC": "renda_per_capita_atlas_reais2010",
    "ADH_GINI": "gini_atlas",
    "ADH_PMPOB": "pobreza_atlas_pct",
    "ADH_PIND": "extrema_pobreza_atlas_pct",
    "ADH_T_ANALF15M": "analfabetismo_15mais_atlas_pct",
    "ADH_T_MED25M": "ensino_medio_completo_25mais_atlas_pct",
    "ADH_T_SUPER25M": "superior_completo_25mais_atlas_pct",
    "ADH_T_FREQ6A14": "atendimento_escolar_6a14_atlas_pct",
    "ADH_T_FREQ15A17": "atendimento_escolar_15a17_atlas_pct",
    "ADH_T_FLMED": "frequencia_liquida_medio_atlas_pct",
    "ADH_T_DES18M": "desocupacao_18mais_atlas_pct",
    "ADH_T_AGUA": "agua_encanada_atlas_pct",
    "ADH_T_AGUA_ESGOTO": "agua_esgoto_inadequados_atlas_pct",
    "ADH_T_LIXO": "coleta_lixo_urbano_atlas_pct",
    "ADH_P_AGRO": "ocupados_agropecuaria_atlas_pct",
    "ADH_P_COM": "ocupados_comercio_atlas_pct",
    "ADH_P_SERV": "ocupados_servicos_atlas_pct",
}


def numeric_value(value: object, *, source: str = "sidra") -> tuple[float | None, str]:
    """Preserve missingness and the SIDRA status; '-' is officially absolute zero."""
    if value is None:
        return None, "ausente"
    text = str(value).strip()
    special = {
        "": "ausente",
        "...": "nao_disponivel",
        "..": "nao_aplicavel",
        "X": "sigilo",
        "x": "sigilo",
    }
    if text in special:
        return None, special[text]
    if text == "-":
        return (
            (0.0, "zero_absoluto_sidra")
            if source == "sidra"
            else (None, "marcador_fonte")
        )
    try:
        result = float(text.replace(",", "."))
    except ValueError:
        return None, "nao_numerico"
    if not pd.notna(result) or result in (float("inf"), -float("inf")):
        return None, "nao_finito"
    return result, "observado"


def plain_html(text: str) -> str:
    import html

    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", text))).strip()


def read_pib() -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    record = json.loads(
        (MANIFESTS / "ibge_pib_2010_2023.json").read_text(encoding="utf-8")
    )
    with zipfile.ZipFile(RAW / record["path"]) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".txt"))
        with archive.open(name) as stream:
            frame = pd.read_fwf(
                io.TextIOWrapper(stream, encoding="cp1252"),
                colspecs=[
                    (start - 1, start - 1 + width)
                    for start, width in PIB_FIELDS.values()
                ],
                names=list(PIB_FIELDS),
                dtype=str,
                keep_default_na=False,
            )
    frame["ano_dado"] = frame["ano_dado"].astype(int)
    if frame.duplicated(["ano_dado", "codigo_ibge"]).any():
        raise ValueError("Duplicate keys in official PIB source")
    backbone = frame[["ano_dado", "codigo_ibge", "municipio", "uf", "regiao"]].copy()
    observations = []
    dictionary = []
    for column in PIB_NUMERIC:
        unit = "Reais" if column == "pib_per_capita_reais" else "Mil Reais"
        for year in sorted(frame.ano_dado.unique()):
            dictionary.append(
                {
                    "variavel": column,
                    "descricao": column.replace("_", " "),
                    "fonte": "IBGE — PIB dos Municípios",
                    "link_fonte": record["url"],
                    "ano_dado": int(year),
                    "unidade": unit,
                    "nivel_geografico": "Município",
                    "forma_calculo": (
                        "Valor publicado, lido por posição fixa; preços correntes."
                    ),
                    "limitacoes": (
                        "PIB per capita não é renda domiciliar. Em 2022–2023, somente "
                        "PIB/PIB per capita; denominadores populacionais censitários "
                        "e revisões descritos no PDF do pacote."
                    ),
                    "source_id": record["id"],
                    "selecionada_para_modelo": False,
                }
            )
        for year, code, raw in frame[["ano_dado", "codigo_ibge", column]].itertuples(
            index=False, name=None
        ):
            value, status = numeric_value(raw, source="pib")
            observations.append(
                {
                    "ano_dado": year,
                    "codigo_ibge": code,
                    "variavel": column,
                    "valor": value,
                    "valor_original": str(raw),
                    "status_valor": status,
                    "source_id": record["id"],
                }
            )
    return backbone, pd.DataFrame(observations), dictionary


def sidra_alias(table: int, var: str, categories: dict[str, str], source: dict) -> str:
    if table == 6579:
        return "populacao"
    if table == 1552 and var == "93" and categories.get("1") == "0":
        return "populacao"
    if table == 4714:
        return {"93": "populacao", "6318": "area_km2", "614": "densidade_hab_km2"}[var]
    if table == 1301:
        return {"615": "area_km2", "616": "densidade_hab_km2"}[var]
    if table == 9543:
        return "alfabetizacao_15mais_censo2022_pct"
    if table == 10295:
        return {
            "13431": "renda_domiciliar_per_capita_censo2022_reais",
            "13534": "renda_domiciliar_per_capita_mediana_censo2022_reais",
        }[var]
    if table in {1685, 9528}:
        label = {
            "706": "unidades_locais",
            "707": "pessoal_ocupado",
            "708": "pessoal_assalariado",
            "662": "remuneracoes_mil_reais",
            "1606": "salario_medio_salarios_minimos",
        }[var]
        regime = "ate2021" if table == 1685 else "desde2022"
        return f"cempre_{label}_{regime}"
    suffix = "".join(
        f"_c{k}_{v}"
        for k, v in categories.items()
        if len(source.get("categories", {}).get(k, [])) > 1
    )
    return f"sidra_{table}_v{var}{suffix}"


def read_sidra(source: dict) -> tuple[pd.DataFrame, list[dict]]:
    table = source["table"]
    metadata = json.loads(
        (RAW / f"municipal/metadata/sidra_{table}.json").read_text(encoding="utf-8-sig")
    )
    response = json.loads((RAW / source["path"]).read_text(encoding="utf-8-sig"))
    header = response[0]
    fields = {label: key for key, label in header.items()}
    territory = fields["Município (Código)"]
    variable = fields["Variável (Código)"]
    period = fields["Ano (Código)"]
    variables = {str(v["id"]): v for v in metadata["variaveis"]}
    dim_fields = {
        str(c["id"]): fields[c["nome"] + " (Código)"]
        for c in metadata["classificacoes"]
    }
    category_names = {
        str(c["id"]): {str(v["id"]): v["nome"] for v in c["categorias"]}
        for c in metadata["classificacoes"]
    }
    observations = []
    dictionary = {}
    for row in response[1:]:
        if row["NC"] != "6":
            raise ValueError("Unexpected geographic level")
        year = int(row[period])
        if year != source["year"]:
            raise ValueError("Unexpected source period")
        var = row[variable]
        categories = {dim: row[field] for dim, field in dim_fields.items()}
        alias = sidra_alias(table, var, categories, source)
        value, status = numeric_value(row["V"])
        observations.append(
            {
                "ano_dado": year,
                "codigo_ibge": row[territory],
                "variavel": alias,
                "valor": value,
                "valor_original": row["V"],
                "status_valor": status,
                "source_id": source["id"],
            }
        )
        if alias not in dictionary:
            labels = {dim: category_names[dim][cat] for dim, cat in categories.items()}
            dictionary[alias] = {
                "variavel": alias,
                "descricao": variables[var]["nome"],
                "fonte": "IBGE — " + metadata["pesquisa"],
                "link_fonte": source["url"],
                "ano_dado": year,
                "unidade": row["MN"],
                "nivel_geografico": "Município",
                "forma_calculo": "Valor publicado pelo SIDRA, sem cálculo adicional.",
                "categorias_codigo": categories,
                "categorias_descricao": labels,
                "limitacoes": source["acquisition_reason"]
                + " Apenas ano de referência; sem interpolação. CEMPRE tem quebra "
                "de série em 2022. As definições censitárias são próprias "
                "de cada edição.",
                "source_id": source["id"],
                "selecionada_para_modelo": False,
            }
    return pd.DataFrame(observations), list(dictionary.values())


def read_ipea(source: dict) -> tuple[pd.DataFrame, list[dict], dict]:
    response = json.loads((RAW / source["path"]).read_text(encoding="utf-8-sig"))
    if "@odata.nextLink" in response:
        raise ValueError("Unconsumed IPEA pagination")
    observations = []
    outside_period = outside_level = 0
    for row in response["value"]:
        year = int(row["VALDATA"][:4])
        if not 2010 <= year <= 2023:
            outside_period += 1
            continue
        if row["NIVNOME"] != "Municípios":
            outside_level += 1
            continue
        value, status = numeric_value(row["VALVALOR"], source="ipea")
        observations.append(
            {
                "ano_dado": year,
                "codigo_ibge": str(row["TERCODIGO"]),
                "variavel": IPEA_ALIASES[source["series"]],
                "valor": value,
                "valor_original": str(row["VALVALOR"])
                if row["VALVALOR"] is not None
                else "",
                "status_valor": status,
                "source_id": source["id"],
            }
        )
    frame = pd.DataFrame(observations)
    if frame.empty:
        raise ValueError(f"No municipal observations within scope: {source['id']}")
    meta = source["metadata"]
    dictionary = [
        {
            "variavel": IPEA_ALIASES[source["series"]],
            "descricao": meta["SERNOME"],
            "fonte": "IPEA/Ipeadata — " + meta["FNTNOME"],
            "link_fonte": source["url"],
            "ano_dado": int(year),
            "unidade": meta["UNINOME"],
            "nivel_geografico": "Município",
            "forma_calculo": plain_html(meta["SERCOMENTARIO"]),
            "limitacoes": (
                "Valores censitários: não anuais. Cortes e universos são os "
                "publicados pela fonte, não parâmetros escolhidos para o ENEM. "
                "IDHM é índice composto e Gini é índice de desigualdade. "
                "Ausências e mudanças de definição preservadas."
            ),
            "source_id": source["id"],
            "selecionada_para_modelo": False,
        }
        for year in sorted(frame.ano_dado.unique())
    ]
    return (
        frame,
        dictionary,
        {
            "source_id": source["id"],
            "raw_rows": len(response["value"]),
            "outside_2010_2023": outside_period,
            "nonmunicipal_within_period": outside_level,
            "municipal_rows_in_scope": len(frame),
            "raw_rows_deleted": 0,
        },
    )


def validate_panel(
    backbone: pd.DataFrame, observations: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    keys = ["codigo_ibge", "ano_dado"]
    if backbone.duplicated(keys).any():
        raise ValueError("Duplicate backbone keys")
    if observations.duplicated(keys + ["variavel"]).any():
        raise ValueError(
            "Duplicate variable/municipality/year; explicit resolution required"
        )
    linked = observations.merge(
        backbone[keys], on=keys, how="left", validate="many_to_one", indicator=True
    )
    matched = linked[linked["_merge"] == "both"].drop(columns="_merge")
    unmatched = linked[linked["_merge"] != "both"].drop(columns="_merge")
    wide = matched.pivot(index=keys, columns="variavel", values="valor").reset_index()
    panel = backbone.merge(wide, on=keys, how="left", validate="one_to_one")
    panel = panel.rename(columns={"ano_dado": "ano_enem"})
    return panel, unmatched


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    backbone, pib_values, dictionary = read_pib()
    parts = [pib_values]
    imports = []
    missing_sources = []
    for catalog_name in ["municipal_catalog.json", "supplement_catalog.json"]:
        catalog = json.loads(
            (ROOT / "docs/sources" / catalog_name).read_text(encoding="utf-8")
        )
        for source in catalog["sources"]:
            if not (
                source["id"].startswith("sidra_")
                or source["id"].startswith("ipeadata_ADH_")
            ):
                continue
            if not (RAW / source["path"]).exists():
                missing_sources.append(source["id"])
                continue
            if source["id"].startswith("sidra_"):
                frame, entries = read_sidra(source)
                imports.append({"source_id": source["id"], "rows": len(frame)})
            else:
                frame, entries, report = read_ipea(source)
                imports.append(report)
            parts.append(frame)
            dictionary.extend(entries)
    for year in range(2010, 2024):
        education_path = OUT / "education" / f"year={year}" / "totais_longos.parquet"
        education_meta = DOCS / "education" / f"{year}.json"
        if not education_path.exists() or not education_meta.exists():
            missing_sources.append(f"education_processed_{year}")
            continue
        frame = pd.read_parquet(education_path)
        parts.append(frame)
        metadata = json.loads(education_meta.read_text(encoding="utf-8"))
        dictionary.extend(metadata["dictionary"])
        imports.append({"source_id": metadata["source_id"], "rows": len(frame)})
    observations = pd.concat(parts, ignore_index=True)
    observations["ano_enem"] = observations["ano_dado"]
    observations["defasagem_anos"] = 0
    panel, unmatched = validate_panel(backbone, observations)
    # These fields are pending; missing residence is not replaced with school/exam site.
    for name in [
        "participantes_enem",
        "participantes_enem_validos",
        "media_matematica",
        "media_natureza",
        "media_humanas",
        "media_linguagens",
        "media_redacao",
    ]:
        panel[name] = pd.Series(pd.NA, index=panel.index, dtype="Float64")
    panel["status_integracao_enem"] = "pendente_residencia_e_amostra"
    panel.to_parquet(
        OUT / "base_municipio_ano.parquet", index=False, compression="zstd"
    )
    panel.to_csv(OUT / "base_municipio_ano.csv", index=False, encoding="utf-8-sig")
    observations.to_parquet(
        OUT / "indicadores_longos.parquet", index=False, compression="zstd"
    )
    unmatched.to_csv(
        OUT / "indicadores_sem_correspondencia.csv", index=False, encoding="utf-8-sig"
    )
    backbone.to_parquet(
        OUT / "referencia_municipal_anual.parquet", index=False, compression="zstd"
    )
    write_json(DOCS / "dicionario_variaveis.json", dictionary)
    flat_dictionary = pd.DataFrame(dictionary)
    for name in ["categorias_codigo", "categorias_descricao"]:
        flat_dictionary[name] = flat_dictionary[name].apply(
            lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, dict) else ""
        )
    flat_dictionary.to_csv(
        DOCS / "dicionario_variaveis.csv", index=False, encoding="utf-8-sig"
    )
    summary = observations.groupby(["ano_dado", "variavel"], as_index=False).agg(
        linhas=("valor", "size"),
        nao_ausentes=("valor", "count"),
        minimo=("valor", "min"),
        maximo=("valor", "max"),
    )
    summary["ausentes"] = summary["linhas"] - summary["nao_ausentes"]
    summary.to_csv(DOCS / "cobertura_variaveis.csv", index=False, encoding="utf-8-sig")
    negative = observations[observations["valor"] < 0]
    negative.to_csv(
        DOCS / "valores_negativos_para_revisao.csv", index=False, encoding="utf-8-sig"
    )
    bounds = value_bounds_audit(observations, dictionary)
    bounds.to_csv(
        DOCS / "valores_fora_limites_para_revisao.csv",
        index=False,
        encoding="utf-8-sig",
    )
    quality = {
        "panel_rows": len(panel),
        "columns": len(panel.columns),
        "municipalities_per_year": {
            str(k): int(v) for k, v in backbone.groupby("ano_dado").size().items()
        },
        "observations": len(observations),
        "missing_values": int(observations.valor.isna().sum()),
        "source_status_counts": observations.status_valor.value_counts().to_dict(),
        "duplicate_panel_keys": int(
            panel.duplicated(["ano_enem", "codigo_ibge"]).sum()
        ),
        "unmatched_observations": len(unmatched),
        "unmatched_nonmissing_values": int(unmatched.valor.notna().sum()),
        "negative_values_preserved": len(negative),
        "values_outside_semantic_bounds_preserved": len(bounds),
        "invalid_municipality_code_rows": int(
            (~observations.codigo_ibge.str.fullmatch(r"[0-9]{7}", na=False)).sum()
        ),
        "automatic_outlier_exclusions": 0,
        "imputations": 0,
        "raw_rows_deleted": 0,
        "sample_size": None,
        "analysis_parameters": None,
        "missing_sources": missing_sources,
        "imports": imports,
        "year_matching": "exact only; source values are never carried forward/backward",
        "enem_integration": "pending: residence and sample rules not resolved",
        "artifacts": {
            p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)}
            for p in OUT.glob("*.parquet")
        },
    }
    write_json(DOCS / "qualidade.json", quality)
    print(
        json.dumps(
            {
                k: quality[k]
                for k in [
                    "panel_rows",
                    "columns",
                    "observations",
                    "unmatched_nonmissing_values",
                    "missing_sources",
                ]
            },
            ensure_ascii=True,
        ),
        flush=True,
    )
    if missing_sources:
        raise SystemExit(1)


def value_bounds_audit(
    observations: pd.DataFrame, dictionary: list[dict]
) -> pd.DataFrame:
    """Flag semantic limits, not statistical cutoffs or automatic exclusions."""
    limits = []
    for entry in dictionary:
        alias = entry["variavel"]
        unit = entry["unidade"].lower()
        upper = None
        if "%" in unit or "percent" in unit:
            upper = 100
        elif alias in {"idhm", "idhm_educacao", "gini_atlas"}:
            upper = 1
        if upper is not None:
            limits.append(
                {
                    "variavel": alias,
                    "ano_dado": entry["ano_dado"],
                    "limite_inferior": 0,
                    "limite_superior": upper,
                }
            )
    joined = observations.merge(
        pd.DataFrame(
            limits,
            columns=["variavel", "ano_dado", "limite_inferior", "limite_superior"],
        ),
        on=["variavel", "ano_dado"],
        how="inner",
        validate="many_to_one",
    )
    return joined[
        (joined.valor < joined.limite_inferior)
        | (joined.valor > joined.limite_superior)
    ].copy()


if __name__ == "__main__":
    main()
