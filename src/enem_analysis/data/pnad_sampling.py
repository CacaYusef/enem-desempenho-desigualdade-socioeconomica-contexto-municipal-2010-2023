"""Official PNADC benchmarks for final secondary-school grades, with provenance.

Grades 3/4 are an explicit proxy for prospective graduates, not observed diplomas.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd

from enem_analysis.data.acquire import RAW, ROOT, download, write_json

BASE = (
    "https://ftp.ibge.gov.br/Trabalho_e_Rendimento/"
    "Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/"
    "Anual/Microdados/Visita/"
)
OUT = ROOT / "data/processed/sampling"


def listing(visit: int, kind: str) -> list[str]:
    url = BASE + f"Visita_{visit}/{kind}/"
    path = f"sampling/pnad/list_v{visit}_{kind}.html"
    download(
        dict(
            id=f"pnadc_list_v{visit}_{kind}_20260920",
            url=url,
            path=path,
            format="html",
            provider="IBGE",
        )
    )
    text = (RAW / path).read_text(encoding="iso-8859-1")
    return [urljoin(url, html.unescape(x)) for x in re.findall(r'href="([^"]+)"', text)]


def choose(urls: list[str], year: int, prefix: str, extension: str) -> str:
    candidates = [
        u
        for u in urls
        if Path(u).name.startswith(prefix)
        and u.endswith(extension)
        and (f"_{year}_" in Path(u).name or (year <= 2014 and "2012_a_2014" in u))
    ]
    if len(candidates) != 1:
        raise ValueError(f"Ambiguous official file: {year}/{prefix}: {candidates}")
    return candidates[0]


def acquire(years: list[int]) -> None:
    indexes = {(v, k): listing(v, k) for v in [1, 5] for k in ["Dados", "Documentacao"]}
    sources = []
    for year in years:
        visit = 5 if year in [2020, 2021, 2022] else 1
        for kind, prefix, extension in [
            ("data", "PNADC_", ".zip"),
            ("input", "input_PNADC_", ".txt"),
            ("dictionary", "dicionario_PNADC_", ".xls"),
        ]:
            key = "Dados" if kind == "data" else "Documentacao"
            url = choose(indexes[visit, key], year, prefix, extension)
            identifier = f"pnadc{year}_{'v1' if kind == 'data' else kind}"
            # Preserve the already downloaded 2023 files at their registered paths.
            path = (
                f"sampling/pnad/{Path(url).name}"
                if kind == "data"
                else f"sampling/pnad/{year}_{kind}{extension}"
            )
            if year != 2023:
                identifier = f"pnadc_{year}_v{visit}_{kind}"
                path = f"sampling/pnad/{year}/{Path(url).name}"
            sources.append(
                dict(
                    id=identifier,
                    url=url,
                    path=path,
                    format=extension[1:],
                    provider="IBGE",
                    year=year,
                    visit=visit,
                    kind=kind,
                )
            )
    write_json(ROOT / "docs/sources/pnad_sampling_catalog.json", {"sources": sources})

    def get(source: dict) -> None:
        download(source)

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(get, sources))


def parse_input(path: Path) -> dict[str, tuple[int, int]]:
    text = path.read_text(encoding="iso-8859-1")
    return {
        name: (int(start) - 1, int(start) - 1 + int(width))
        for start, name, width in re.findall(r"@(\d+)\s+(\w+)\s+\$?(\d+)\.", text)
    }


def definitions(path: Path) -> dict:
    rows = pd.read_excel(path, engine="calamine", header=None, dtype=str).fillna("")
    result, current = {}, None
    for row in rows.itertuples(index=False, name=None):
        name = str(row[2]).strip()
        if re.fullmatch(r"(?:V\d+\w*|VD\d+|UF|UPA|Estrato|Ano|Trimestre)", name):
            current = name
            result[current] = {"description": row[4], "categories": {}}
        elif name:
            current = None
        if current and str(row[5]).strip():
            result[current]["categories"][str(row[5]).strip()] = str(row[6]).strip()
    return result


def process(year: int, sources: list[dict]) -> dict:
    files = {s["kind"]: RAW / s["path"] for s in sources if s["year"] == year}
    layout = parse_input(files["input"])
    meta = definitions(files["dictionary"])
    courses = {}
    for course in [c for c in ["V3003", "V3003A"] if c in layout]:
        codes = [
            c
            for c, label in meta[course]["categories"].items()
            if "regular do ensino médio" in label.lower()
        ]
        if len(codes) != 1:
            raise ValueError(f"Cannot resolve secondary school code {year}: {codes}")
        courses[course] = codes[0].zfill(layout[course][1] - layout[course][0])
    wanted = [
        "Ano",
        "Trimestre",
        "UF",
        "UPA",
        "Estrato",
        "V1032",
        "V2007",
        "V2009",
        "V2010",
        "V3002",
        *courses,
        "V3006",
        "VD5001",
    ]
    if "V3002A" in layout:
        wanted.append("V3002A")
    if not set(wanted).issubset(layout):
        raise ValueError(f"Missing fields {year}: {set(wanted) - set(layout)}")
    records, raw_rows, psus = [], 0, set()
    grades = {}
    with zipfile.ZipFile(files["data"]) as archive:
        members = [n for n in archive.namelist() if n.lower().endswith(".txt")]
        if len(members) != 1:
            raise ValueError("Ambiguous PNAD member")
        with archive.open(members[0]) as stream:
            for line in stream:
                raw_rows += 1

                def value(name: str) -> str:
                    start, stop = layout[name]
                    return line[start:stop].decode("ascii").strip()

                psus.add((value("Estrato"), value("UPA")))
                if value("V3002") != "1" or not any(
                    value(k) == c for k, c in courses.items()
                ):
                    continue
                grade = value("V3006")
                grades[grade] = grades.get(grade, 0) + 1
                if grade not in {"03", "04"}:
                    continue
                records.append({name: value(name) for name in wanted})
    frame = pd.DataFrame(records)
    frame["weight"] = pd.to_numeric(frame.V1032, errors="raise")
    if not frame.weight.gt(0).all():
        raise ValueError("Nonpositive official person weight")
    frame["raca"] = frame.V2010.map(
        {
            "1": "Branca",
            "2": "Preta",
            "3": "Amarela",
            "4": "Parda",
            "5": "Indigena",
            "9": "Ignorada",
        }
    )
    frame["sexo"] = frame.V2007.map({"1": "M", "2": "F"})
    frame["regiao"] = frame.UF.str[0].map(
        {"1": "Norte", "2": "Nordeste", "3": "Sudeste", "4": "Sul", "5": "Centro-Oeste"}
    )
    frame["escola"] = (
        frame.V3002A.map({"1": "Privada", "2": "Publica"})
        if "V3002A" in frame
        else "Nao_disponivel"
    )
    frame["idade"] = pd.to_numeric(frame.V2009, errors="raise")
    frame["faixa_idade"] = pd.cut(
        frame.idade,
        [-1, 16, 17, 18, 19, 24, 200],
        labels=["ate16", "17", "18", "19", "20a24", "25mais"],
    )
    frame["renda_domiciliar"] = pd.to_numeric(frame.VD5001, errors="coerce")
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(sorted(psus), columns=["Estrato", "UPA"]).to_parquet(
        OUT / f"pnad_psus_{year}.parquet", index=False
    )
    frame.to_parquet(OUT / f"pnad_proxy_{year}.parquet", index=False)
    audit = {
        "year": year,
        "raw_rows": raw_rows,
        "proxy_rows": len(frame),
        "population_proxy": float(frame.weight.sum()),
        "grade_counts": grades,
        "grade_filter": ["03", "04"],
        "course_codes": courses,
        "weight_field": "V1032",
        "visit": 5 if year in [2020, 2021, 2022] else 1,
        "definition": (
            "Matriculados no EM regular, 3a/4a serie; "
            "proxy, nao concluintes certificados."
        ),
        "dictionary": {k: meta.get(k) for k in wanted},
        "unobserved_graduation": True,
    }
    write_json(OUT / f"pnad_proxy_{year}.json", audit)
    print(
        f"PNAD {year}: {len(frame)} records; "
        f"population proxy {frame.weight.sum():,.1f}",
        flush=True,
    )
    return audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acquire", action="store_true")
    parser.add_argument("--years", nargs="+", type=int, default=list(range(2012, 2024)))
    args = parser.parse_args()
    if args.acquire:
        acquire(args.years)
    sources = json.loads(
        (ROOT / "docs/sources/pnad_sampling_catalog.json").read_text(encoding="utf-8")
    )["sources"]
    for year in args.years:
        process(year, sources)


if __name__ == "__main__":
    main()
