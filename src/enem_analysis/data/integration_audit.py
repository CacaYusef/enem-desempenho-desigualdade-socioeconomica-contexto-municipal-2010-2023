"""Validate geographical correspondences without selecting an ENEM location/cohort."""

from __future__ import annotations

import importlib.metadata
import json
import platform
import re
import unicodedata

import pandas as pd

from enem_analysis.data.acquire import ROOT, write_json

OUT = ROOT / "data/processed/municipal"
DOCS = ROOT / "docs/sources"


def normalize_name(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]+", " ", text.upper()).strip()


def geographical_crosswalk(
    frame: pd.DataFrame, reference: pd.DataFrame
) -> pd.DataFrame:
    reference = reference.rename(columns={"ano_dado": "ano_enem"})
    result = frame.merge(
        reference,
        left_on=["ano_enem", "codigo_original_ENEM"],
        right_on=["ano_enem", "codigo_ibge"],
        how="left",
        validate="many_to_one",
    )
    result["correspondencia_validada"] = result.codigo_ibge.notna()
    result["nome_equivalente_normalizado"] = (
        result.nome_original_ENEM.map(normalize_name)
        == result.municipio.map(normalize_name)
    ) & result.correspondencia_validada
    result["regra_correspondencia"] = "codigo_ibge_exato_no_ano"
    result.loc[~result.correspondencia_validada, "regra_correspondencia"] = (
        "sem_correspondencia"
    )
    result.loc[result.codigo_original_ENEM.isna(), "regra_correspondencia"] = (
        "codigo_ausente"
    )
    result["vinculo_residencial_validado"] = (
        result.correspondencia_validada & result.tipo_localizacao.eq("residencia")
    )
    return result


def main() -> None:
    reference = pd.read_parquet(OUT / "referencia_municipal_anual.parquet")
    files = sorted(
        (ROOT / "data/processed/enem").glob("year=*/codigos_municipais.parquet")
    )
    frames = [pd.read_parquet(path) for path in files]
    frame = pd.concat(frames, ignore_index=True)
    crosswalk = geographical_crosswalk(frame, reference)
    crosswalk.to_parquet(
        OUT / "correspondencia_enem_municipios.parquet", index=False, compression="zstd"
    )
    crosswalk.to_csv(
        OUT / "correspondencia_enem_municipios.csv", index=False, encoding="utf-8-sig"
    )
    unmatched = crosswalk[~crosswalk.correspondencia_validada]
    unmatched.to_csv(
        OUT / "municipios_enem_nao_correspondidos.csv",
        index=False,
        encoding="utf-8-sig",
    )
    # Suggestions use only exact normalized names; they are never applied.
    proposals = []
    for row in unmatched.itertuples(index=False):
        normalized = normalize_name(row.nome_original_ENEM)
        if not normalized:
            continue
        candidate = reference[
            (reference.ano_dado == row.ano_enem)
            & reference.municipio.map(normalize_name).eq(normalized)
        ]
        for item in candidate.itertuples(index=False):
            proposals.append(
                {
                    "ano_enem": row.ano_enem,
                    "codigo_original_ENEM": row.codigo_original_ENEM,
                    "nome_original_ENEM": row.nome_original_ENEM,
                    "codigo_candidato": item.codigo_ibge,
                    "municipio_candidato": item.municipio,
                    "uf_candidata": item.uf,
                    "aplicado": False,
                    "criterio": (
                        "nome_normalizado_exato; exige revisão, inclusive de UF"
                    ),
                }
            )
    pd.DataFrame(
        proposals,
        columns=[
            "ano_enem",
            "codigo_original_ENEM",
            "nome_original_ENEM",
            "codigo_candidato",
            "municipio_candidato",
            "uf_candidata",
            "aplicado",
            "criterio",
        ],
    ).to_csv(
        OUT / "possiveis_correspondencias_para_revisao.csv",
        index=False,
        encoding="utf-8-sig",
    )
    totals = []
    for (year, geography), group in crosswalk.groupby(["ano_enem", "tipo_localizacao"]):
        matched = group[group.correspondencia_validada]
        failed = group[
            ~group.correspondencia_validada & group.codigo_original_ENEM.notna()
        ]
        totals.append(
            {
                "ano_enem": int(year),
                "tipo_localizacao": geography,
                "municipios_integrados_automaticamente": int(
                    matched.codigo_ibge.nunique()
                ),
                "municipios_integrados_apos_tratamento": 0,
                "codigos_nao_integrados": int(failed.codigo_original_ENEM.nunique()),
                "registros_com_codigo_integrado": int(matched.registros.sum()),
                "registros_sem_codigo": int(
                    group.loc[group.codigo_original_ENEM.isna(), "registros"].sum()
                ),
                "registros_com_codigo_nao_integrado": int(failed.registros.sum()),
                "registros_descartados": 0,
            }
        )
    pd.DataFrame(totals).to_csv(
        DOCS / "municipal/correspondencia_resumo.csv", index=False, encoding="utf-8-sig"
    )
    audits = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((DOCS / "enem").glob("[0-9][0-9][0-9][0-9].json"))
    ]
    inventories = []
    schema = []
    for audit in audits:
        inventories.append(
            {
                "ano": audit["year"],
                "linhas_fonte": audit["rows"],
                "colunas": len(audit["columns"]),
                "residencia_disponivel": audit["residence_available"],
                "duplicidades_inscricao_excedentes": audit.get(
                    "duplicate_registration_excess"
                ),
                "linhas_excluidas": audit["rows_excluded"],
            }
        )
        for column in audit["columns"]:
            schema.append(
                {
                    "ano": audit["year"],
                    "variavel_original": column,
                    "ausentes": audit["missing_by_column"][column],
                    "linhas_fonte": audit["rows"],
                    "tipo_armazenamento": "string",
                }
            )
    pd.DataFrame(inventories).to_csv(
        DOCS / "enem/inventario_anual.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(schema).to_csv(
        DOCS / "enem/disponibilidade_variaveis.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(schema).assign(presente=True).pivot(
        index="variavel_original", columns="ano", values="presente"
    ).fillna(False).to_csv(
        DOCS / "enem/matriz_disponibilidade.csv", encoding="utf-8-sig"
    )
    environment = {"python": platform.python_version(), "platform": platform.platform()}
    for package in [
        "duckdb",
        "pandas",
        "pyarrow",
        "openpyxl",
        "python-calamine",
        "pypdf",
    ]:
        environment[package] = importlib.metadata.version(package)
    write_json(DOCS / "runtime_versions.json", environment)
    result = {
        "years_processed": [a["year"] for a in audits],
        "source_rows": sum(a["rows"] for a in audits),
        "years_with_residence": [a["year"] for a in audits if a["residence_available"]],
        "crosswalk_rows": len(crosswalk),
        "suggestions_for_review": len(proposals),
        "final_sample_size": None,
        "statistical_parameters": None,
        "residence_context_join_performed": False,
    }
    write_json(DOCS / "integration_status.json", result)
    print(json.dumps(result, ensure_ascii=True), flush=True)


if __name__ == "__main__":
    main()
