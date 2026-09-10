"""Explicit official-source recipes for candidate municipal indicators.

This catalog does not select variables, observations or parameters for a model.
"""

from __future__ import annotations

import json
import math

from enem_analysis.data.acquire import RAW, ROOT, download, write_json

# Category selections below are source-defined dimensions, not ENEM sample rules.
RECIPES = [
    {
        "table": 6579,
        "years": list(range(2011, 2022)),
        "variables": [9324],
        "reason": "Porte demográfico anual; estimativas oficiais entre censos.",
    },
    {
        "table": 1552,
        "years": [2010],
        "variables": [93, 1000093],
        "categories": {1: [0, 1, 2]},
        "reason": "População e distribuição urbana/rural no Censo 2010.",
    },
    {
        "table": 1301,
        "years": [2010],
        "variables": [615, 616],
        "reason": "Área e densidade na referência territorial do Censo 2010.",
    },
    {
        "table": 4714,
        "years": [2022],
        "variables": [93, 6318, 614],
        "reason": "População, área e densidade do Censo 2022.",
    },
    {
        "table": 9923,
        "years": [2022],
        "variables": [93, 1000093],
        "categories": {1: [6795, 1, 2]},
        "reason": "Distribuição urbana/rural na definição do Censo 2022.",
    },
    {
        "table": 9543,
        "years": [2022],
        "variables": [2513],
        "reason": "Alfabetização das pessoas de 15 anos ou mais; definição oficial.",
    },
    {
        "table": 10295,
        "years": [2022],
        "variables": [13431, 13534],
        "reason": (
            "Rendimento domiciliar per capita médio e mediano; universo censitário."
        ),
    },
    {
        "table": 3540,
        "years": [2010],
        "variables": [140, 1000140],
        "categories": {1568: [0, 9493, 9494, 9495, 99713, 11626]},
        "reason": "Composição por nível de instrução das pessoas de 10 anos ou mais.",
    },
    {
        "table": 6803,
        "years": [2022],
        "variables": [381, 1000381],
        "categories": {1821: [72129, 72144, 72145, 72153]},
        "reason": "Acesso domiciliar à rede de água, nas categorias publicadas.",
    },
    {
        "table": 6805,
        "years": [2022],
        "variables": [381, 1000381],
        "categories": {11558: [46292, 46290, 72112, 72113, 92861]},
        "reason": (
            "Esgotamento sanitário, preservando o universo e as categorias oficiais."
        ),
    },
    {
        "table": 10201,
        "years": [2022],
        "variables": [13436, 1013436],
        "categories": {2072: [77584, 77585, 77586]},
        "reason": (
            "Conexão domiciliar à internet entre moradores de 10 anos ou mais; "
            "religião no total."
        ),
    },
    {
        "table": 1685,
        "years": list(range(2010, 2022)),
        "variables": [706, 707, 708, 662, 1606],
        "reason": (
            "Estrutura empresarial e emprego formal local; série CEMPRE até 2021."
        ),
    },
    {
        "table": 9528,
        "years": [2022, 2023],
        "variables": [706, 707, 708, 662],
        "reason": "CEMPRE nova série desde 2022; manter quebra metodológica explícita.",
    },
]


def metadata_source(table: int) -> dict:
    return {
        "id": f"ibge_metadata_{table}",
        "provider": "IBGE",
        "url": f"https://servicodados.ibge.gov.br/api/v3/agregados/{table}/metadados",
        "path": f"municipal/metadata/sidra_{table}.json",
        "format": "json",
    }


def sidra_sources(recipe: dict, metadata: dict) -> list[dict]:
    """Resolve and validate every category against the saved official dictionary."""
    table = recipe["table"]
    known_vars = {v["id"] for v in metadata["variaveis"]}
    if not set(recipe["variables"]).issubset(known_vars):
        raise ValueError(f"Unknown variable in table {table}")
    suffix = ""
    selections = {}
    for dimension in metadata["classificacoes"]:
        dim_id = dimension["id"]
        selected = recipe.get("categories", {}).get(dim_id)
        if selected is None:
            totals = [c["id"] for c in dimension["categorias"] if c["nome"] == "Total"]
            if len(totals) != 1:
                raise ValueError(f"No unambiguous total: {table}/{dim_id}")
            selected = totals
        known = {c["id"] for c in dimension["categorias"]}
        if not set(selected).issubset(known):
            raise ValueError(f"Unknown category: {table}/{dim_id}")
        selections[str(dim_id)] = selected
        suffix += f"/c{dim_id}/" + ",".join(map(str, selected))
    # The live service returned an explicit 50,000-value limit on 2026-09-09.
    # 6,000 is only a conservative request-sizing bound, never a sample size.
    combinations = math.prod(len(s) for s in selections.values())
    per_request = max(1, 50000 // (6000 * combinations))
    if len(recipe["variables"]) > per_request:
        parts = []
        for start in range(0, len(recipe["variables"]), per_request):
            subset = recipe["variables"][start : start + per_request]
            for part in sidra_sources({**recipe, "variables": subset}, metadata):
                marker = "_v" + "_".join(map(str, subset))
                part["id"] += marker
                part["path"] = part["path"].replace(".json", marker + ".json")
                parts.append(part)
        return parts
    sources = []
    for year in recipe["years"]:
        url = (
            f"https://apisidra.ibge.gov.br/values/t/{table}/n6/all/v/"
            + ",".join(map(str, recipe["variables"]))
            + f"/p/{year}{suffix}/u/y"
        )
        sources.append(
            {
                "id": f"sidra_{table}_{year}",
                "provider": "IBGE",
                "table": table,
                "year": year,
                "url": url,
                "landing_page": f"https://sidra.ibge.gov.br/tabela/{table}",
                "path": f"municipal/sidra/{table}/{year}.json",
                "format": "json",
                "variables": recipe["variables"],
                "categories": selections,
                "acquisition_reason": recipe["reason"],
                "selected_for_model": False,
            }
        )
    return sources


def main() -> None:
    sources = [
        {
            "id": "ibge_pib_2010_2023",
            "provider": "IBGE",
            "format": "zip",
            "url": "https://ftp.ibge.gov.br/Pib_Municipios/2022_2023/base/base_de_dados_2010_2023_txt.zip",
            "landing_page": "https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/9088-produto-interno-bruto-dos-municipios.html",
            "path": "municipal/pib/base_de_dados_2010_2023_txt.zip",
            "years": [2010, 2023],
        },
        {
            "id": "ibge_localidades_20260909",
            "provider": "IBGE",
            "format": "json",
            "url": "https://servicodados.ibge.gov.br/api/v1/localidades/municipios",
            "path": "municipal/territory/municipios_20260909.json",
            "limitation": (
                "Cadastro corrente, não substitui a geografia histórica anual."
            ),
        },
        {
            "id": "ipeadata_metadata_20260909",
            "provider": "IPEA",
            "format": "json",
            "url": "http://www.ipeadata.gov.br/api/odata4/Metadados",
            "path": "municipal/metadata/ipeadata_20260909.json",
        },
    ]
    errors = []
    for recipe in RECIPES:
        meta_source = metadata_source(recipe["table"])
        try:
            download(meta_source)
            metadata = json.loads(
                (RAW / meta_source["path"]).read_text(encoding="utf-8-sig")
            )
            sources.extend(sidra_sources(recipe, metadata))
        except Exception as exc:
            errors.append({"id": meta_source["id"], "error": str(exc)})
            print(f"FAILED {meta_source['id']}: {exc}", flush=True)
    write_json(
        ROOT / "docs" / "sources" / "municipal_catalog.json", {"sources": sources}
    )
    for source in sources:
        try:
            download(source)
        except Exception as exc:
            errors.append({"id": source["id"], "error": str(exc)})
            print(f"FAILED {source['id']}: {exc}", flush=True)
    write_json(
        ROOT / "data" / "processed" / "acquisition_municipal_status.json",
        {"errors": errors},
    )
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
