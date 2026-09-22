"""Selected contemporary municipal context, decision 006; no ENEM sampling."""

from __future__ import annotations

import json
import zipfile

import numpy as np
import pandas as pd

from enem_analysis.data.acquire import RAW, ROOT, sha256, write_json
from enem_analysis.data.municipal_import import numeric_value

OUT = ROOT / "data/processed/territorial_2023"
SOURCE = RAW / "municipal/territorial_2023"
REGIONS = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]


def canonical_region(values):
    """Normalize the observed IBGE spelling, not territorial membership."""
    result = values.replace({"Centro-oeste": "Centro-Oeste"})
    if not result.dropna().isin(REGIONS).all():
        raise ValueError("Unexpected region label; do not silently drop a region")
    return result


INDICATORS = {
    "ideb_2023": "IDEB EM público (2023)",
    "saeb_mt_2023": "Saeb matemática EM público (2023)",
    "saeb_lp_2023": "Saeb português EM público (2023)",
    "pib_pc_2023": "PIB per capita (R$, 2023)",
    "renda_pc_2022": "Renda domiciliar per capita (R$, 2022)",
    "abandono_2023": "Abandono EM total (%, 2023)",
    "aprovacao_2023": "Aprovação EM total (%, 2023)",
    "reprovacao_2023": "Reprovação EM total (%, 2023)",
    "distorcao_2023": "Distorção idade-série EM total (%, 2023)",
    "populacao_2022": "População (habitantes, 2022)",
    "urbanizacao_2022": "População urbana (%, 2022)",
    "internet_escolas_pct": "Escolas EM com internet para alunos (%, 2023)",
    "laboratorio_escolas_pct": "Escolas EM com laboratório de informática (%, 2023)",
}


def read_spreadsheet(filename: str, header: int) -> pd.DataFrame:
    with zipfile.ZipFile(SOURCE / filename) as archive:
        member = next(n for n in archive.namelist() if n.endswith(".xlsx"))
        return pd.read_excel(
            archive.open(member),
            header=header,
            engine="calamine",
            dtype=str,
            keep_default_na=False,
        )


def merge_context(left: pd.DataFrame, right: pd.DataFrame) -> pd.DataFrame:
    if right.codigo_ibge.isna().any() or right.codigo_ibge.duplicated().any():
        raise ValueError("Municipal context must have unique, nonmissing codes")
    n = len(left)
    result = left.merge(right, on="codigo_ibge", how="left", validate="many_to_one")
    if len(result) != n:
        raise AssertionError("Left join changed the observational universe")
    return result


def numeric_audit(frame, mappings, source, rows):
    for old, new in mappings.items():
        parsed = frame[old].map(lambda v: numeric_value(v, source="inep"))
        frame[new] = parsed.map(lambda x: x[0]).astype(float)
        statuses = parsed.map(lambda x: x[1])
        rows.extend(
            {
                "fonte": source,
                "coluna": old,
                "variavel": new,
                "valor_original": str(value),
                "status": status,
                "n": int(n),
            }
            for (value, status), n in pd.DataFrame(
                {"value": frame[old], "status": statuses}
            )
            .value_counts(dropna=False)
            .items()
        )


def school_infrastructure() -> tuple[pd.DataFrame, dict]:
    fields = [
        "CO_ENTIDADE",
        "CO_MUNICIPIO",
        "TP_SITUACAO_FUNCIONAMENTO",
        "IN_MED",
        "QT_MAT_MED",
        "TP_DEPENDENCIA",
        "IN_INTERNET_ALUNOS",
        "IN_LABORATORIO_INFORMATICA",
    ]
    with zipfile.ZipFile(SOURCE / "censo_escolar_2023.zip") as archive:
        member = next(
            n for n in archive.namelist() if n.endswith("microdados_ed_basica_2023.csv")
        )
        data = pd.read_csv(
            archive.open(member),
            sep=";",
            encoding="cp1252",
            usecols=fields,
            dtype="string",
        )
        book = next(n for n in archive.namelist() if n.endswith(".xlsx"))
        d = pd.read_excel(
            archive.open(book),
            sheet_name="microdados_unidade_coleta",
            header=None,
            engine="calamine",
        ).fillna("")
        definitions = d[d.iloc[:, 1].isin(fields)].iloc[:, :6]
        write_json(
            OUT / "dicionario_censo_selecionado.json", definitions.values.tolist()
        )
    if data.CO_ENTIDADE.duplicated().any():
        raise ValueError("Duplicate school identifier")
    selected = data[data.TP_SITUACAO_FUNCIONAMENTO.eq("1") & data.IN_MED.eq("1")].copy()
    if selected.CO_MUNICIPIO.isna().any():
        raise ValueError("School geography missing; audit before aggregation")
    selected["matriculas"] = pd.to_numeric(selected.QT_MAT_MED, errors="raise")
    if not selected.matriculas.gt(0).all():
        raise ValueError("IN_MED and enrollment count disagree")
    aliases = {
        "IN_INTERNET_ALUNOS": "internet",
        "IN_LABORATORIO_INFORMATICA": "laboratorio",
    }
    for col in aliases:
        if not selected[col].dropna().isin(["0", "1"]).all():
            raise ValueError(f"Unexpected binary code: {col}")
        selected[col] = pd.to_numeric(selected[col], errors="raise")
    result = selected.groupby("CO_MUNICIPIO").agg(
        escolas_em=("CO_ENTIDADE", "size"), matriculas_em=("matriculas", "sum")
    )
    for col, alias in aliases.items():
        g = selected.groupby("CO_MUNICIPIO")[col]
        result[alias + "_escolas_pct"] = 100 * g.mean()
        result[alias + "_escolas_n_observado"] = g.count()
    result = result.reset_index().rename(columns={"CO_MUNICIPIO": "codigo_ibge"})
    return result, {
        "escolas_fonte": len(data),
        "escolas_em_ativas": len(selected),
        "municipios_em": len(result),
        "csv_member": member,
        "regra": (
            "Ativa=1, IN_MED=1; proporção entre escolas "
            "com item observado; redes todas"
        ),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    audits = []
    ideb = read_spreadsheet("ideb_municipios_em_v2025.zip", 9)
    ideb = ideb[ideb.CO_MUNICIPIO.str.fullmatch(r"\d{7}")].copy()
    mappings = {
        "VL_OBSERVADO_2023": "ideb_2023",
        "VL_NOTA_MATEMATICA_2023": "saeb_mt_2023",
        "VL_NOTA_PORTUGUES_2023": "saeb_lp_2023",
    }
    numeric_audit(ideb, mappings, "ideb_v2025_referencia2023", audits)
    ideb.to_parquet(OUT / "ideb_redes_fonte.parquet", index=False)
    public = ideb[ideb.REDE.eq("Pública")][["CO_MUNICIPIO", *mappings.values()]].rename(
        columns={"CO_MUNICIPIO": "codigo_ibge"}
    )
    if not public.ideb_2023.dropna().between(0, 10).all():
        raise ValueError("IDEB outside 0–10")
    tdi = read_spreadsheet("tdi_municipios_2023.zip", 8)
    tdi = tdi[tdi.NU_ANO_CENSO.eq("2023")].copy()
    numeric_audit(tdi, {"MED_CAT_0": "distorcao_2023"}, "tdi2023", audits)
    tdi.to_parquet(OUT / "tdi_redes_fonte.parquet", index=False)
    total = tdi[tdi.NO_DEPENDENCIA.eq("Total") & tdi.NO_CATEGORIA.eq("Total")]
    total = total[["CO_MUNICIPIO", "distorcao_2023"]].rename(
        columns={"CO_MUNICIPIO": "codigo_ibge"}
    )
    panel_file = ROOT / "data/processed/municipal/base_municipio_ano.parquet"
    panel = pd.read_parquet(panel_file)
    annual = {
        "pib_per_capita_reais": "pib_pc_2023",
        "educ_abandono_medio_pct": "abandono_2023",
        "educ_aprovacao_medio_pct": "aprovacao_2023",
        "educ_reprovacao_medio_pct": "reprovacao_2023",
    }
    census = {
        "renda_domiciliar_per_capita_censo2022_reais": "renda_pc_2022",
        "populacao": "populacao_2022",
        "sidra_9923_v1000093_c1_1": "urbanizacao_2022",
    }
    base = panel[panel.ano_enem.eq(2023)][
        ["codigo_ibge", "municipio", "uf", "regiao", *annual]
    ].rename(columns=annual)
    c22 = panel[panel.ano_enem.eq(2022)][["codigo_ibge", *census]].rename(
        columns=census
    )
    infra, infra_audit = school_infrastructure()
    for right in [c22, public, total, infra]:
        base = merge_context(base, right)
    base["regiao"] = canonical_region(base.regiao)
    for col in INDICATORS:
        if not np.isfinite(base[col].dropna().astype(float)).all():
            raise ValueError(f"Nonfinite municipal values: {col}")
        if col.endswith("pct") or col in [
            "abandono_2023",
            "aprovacao_2023",
            "reprovacao_2023",
            "distorcao_2023",
            "urbanizacao_2022",
        ]:
            if not base[col].dropna().between(0, 100).all():
                raise ValueError(f"Percentage outside domain: {col}")
    base.to_parquet(OUT / "contexto_municipal.parquet", index=False)
    base.to_csv(OUT / "contexto_municipal.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(audits).to_csv(
        OUT / "marcadores_fontes.csv", index=False, encoding="utf-8-sig"
    )
    old = pd.read_csv(ROOT / "docs/sources/municipal/dicionario_variaveis.csv")
    meta = []
    for mapping, year in [(annual, 2023), (census, 2022)]:
        for source, target in mapping.items():
            row = old[old.variavel.eq(source) & old.ano_dado.eq(year)].iloc[0].to_dict()
            meta.append(
                {
                    **row,
                    "variavel": target,
                    "coluna_origem": source,
                    "ano_enem": 2023,
                    "defasagem_anos": 2023 - year,
                }
            )
    catalog = json.loads(
        (ROOT / "docs/sources/territorial_2023_catalog.json").read_text(
            encoding="utf-8"
        )
    )
    source_by_id = {s["id"]: s for s in catalog["sources"]}
    for col in [
        *mappings.values(),
        "distorcao_2023",
        "internet_escolas_pct",
        "laboratorio_escolas_pct",
    ]:
        key = (
            "territorial_ideb_municipios_em_v2025"
            if col in mappings.values()
            else (
                "territorial_tdi_municipios_2023"
                if col == "distorcao_2023"
                else "territorial_censo_escolar_2023"
            )
        )
        meta.append(
            {
                "variavel": col,
                "descricao": INDICATORS[col],
                "fonte": "INEP",
                "link_fonte": source_by_id[key]["url"],
                "ano_dado": 2023,
                "ano_enem": 2023,
                "defasagem_anos": 0,
                "unidade": "0–10"
                if col == "ideb_2023"
                else "Pontos Saeb"
                if col.startswith("saeb")
                else "%",
                "rede": "Pública" if col in mappings.values() else "Todas",
                "limitacoes": (
                    "IDEB/Saeb público não identifica escola privada; "
                    "supressões preservadas; proporções de infraestrutura "
                    "por escola, não matrícula."
                ),
            }
        )
    write_json(OUT / "dicionario_contextual.json", meta)
    coverage = [
        {
            "variavel": col,
            "n_municipios": len(base),
            "n_observado": int(base[col].notna().sum()),
            "n_ausente": int(base[col].isna().sum()),
        }
        for col in INDICATORS
    ]
    pd.DataFrame(coverage).to_csv(OUT / "cobertura_fontes.csv", index=False)
    manifest = {
        "municipios": len(base),
        "ideb_publico_linhas": len(public),
        "ideb_publico_observado_2023": int(public.ideb_2023.notna().sum()),
        "ideb_vintage": 2025,
        "ideb_reference_year": 2023,
        "infraestrutura": infra_audit,
        "input_panel_sha256": sha256(panel_file),
        "sources": {s["id"]: sha256(RAW / s["path"]) for s in catalog["sources"]},
    }
    write_json(OUT / "contexto_manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
