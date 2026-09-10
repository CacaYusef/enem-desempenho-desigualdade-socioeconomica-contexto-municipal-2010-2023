"""Acquire documented social/educational candidate indicators from IPEA and INEP."""

from __future__ import annotations

import html
import json
import re
from urllib.parse import urlparse

from enem_analysis.data.acquire import RAW, ROOT, download, write_json

SERIES = {
    "ADH_IDHM": "Desenvolvimento humano: índice composto, não variável bruta.",
    "ADH_IDHM_E": "Dimensão educacional do índice composto IDHM.",
    "ADH_RDPC": "Renda domiciliar per capita: condição econômica estrutural.",
    "ADH_GINI": "Desigualdade de renda: índice de Gini publicado.",
    "ADH_PMPOB": "Pobreza segundo a definição e o corte preexistentes do Atlas.",
    "ADH_PIND": "Extrema pobreza segundo a definição preexistente do Atlas.",
    "ADH_T_ANALF15M": "Alfabetização da população adulta: analfabetismo oficial.",
    "ADH_T_MED25M": "Escolaridade adulta: ensino médio completo, definição do Atlas.",
    "ADH_T_SUPER25M": "Escolaridade adulta: ensino superior completo.",
    "ADH_T_FREQ6A14": "Atendimento escolar na faixa etária definida pelo Atlas.",
    "ADH_T_FREQ15A17": "Atendimento escolar na faixa etária definida pelo Atlas.",
    "ADH_T_FLMED": "Frequência líquida ao ensino médio na definição oficial.",
    "ADH_T_DES18M": "Desocupação da população economicamente ativa adulta.",
    "ADH_T_AGUA": "Condições domiciliares: água encanada.",
    "ADH_T_AGUA_ESGOTO": "Abastecimento de água e esgotamento inadequados.",
    "ADH_T_LIXO": "Coleta de lixo entre moradores de domicílios urbanos.",
    "ADH_P_AGRO": "Composição setorial da ocupação: agropecuária.",
    "ADH_P_COM": "Composição setorial da ocupação: comércio.",
    "ADH_P_SERV": "Composição setorial da ocupação: serviços.",
}


def main() -> None:
    metadata = json.loads(
        (RAW / "municipal/metadata/ipeadata_20260909.json").read_text(
            encoding="utf-8-sig"
        )
    )
    known = {s["SERCODIGO"]: s for s in metadata["value"]}
    sources = []
    for code, reason in SERIES.items():
        if code not in known:
            raise ValueError(f"Unknown IPEA series: {code}")
        sources.append(
            {
                "id": f"ipeadata_{code}",
                "provider": "IPEA",
                "series": code,
                "url": f"http://www.ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='{code}')",
                "path": f"municipal/ipeadata/{code}.json",
                "format": "json",
                "acquisition_reason": reason,
                "selected_for_model": False,
                "scope": (
                    "Raw response preserved; processed scope: "
                    "municipalities, 2010–2023."
                ),
                "metadata": known[code],
            }
        )
    errors = []
    for year in range(2010, 2024):
        page_url = (
            "https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/"
            f"indicadores-educacionais/taxas-de-rendimento-escolar/{year}"
        )
        page = {
            "id": f"inep_rendimento_page_{year}",
            "provider": "INEP",
            "url": page_url,
            "path": f"municipal/inep/pages/rendimento_{year}.html",
            "format": "html",
            "year": year,
        }
        try:
            download(page)
            content = (RAW / page["path"]).read_text(encoding="utf-8")
            links = [
                html.unescape(x)
                for x in re.findall(r'href=["\x27]([^"\x27]+)', content)
            ]
            links = list(
                dict.fromkeys(
                    x
                    for x in links
                    if urlparse(x).hostname == "download.inep.gov.br"
                    and "munic" in x.lower()
                    and str(year) in x
                    and x.lower().endswith((".zip", ".xlsx", ".xls"))
                )
            )
            if len(links) != 1:
                raise ValueError(f"Ambiguous official municipal download: {links}")
            url = links[0]
            extension = url.rsplit(".", 1)[-1]
            sources.append(
                {
                    "id": f"inep_rendimento_{year}",
                    "provider": "INEP",
                    "year": year,
                    "url": url,
                    "landing_page": page_url,
                    "path": f"municipal/inep/rendimento_{year}.{extension}",
                    "format": extension,
                    "selected_for_model": False,
                    "acquisition_reason": (
                        "Contexto educacional: aprovação, reprovação e abandono; "
                        "todas as redes e etapas preservadas."
                    ),
                }
            )
        except Exception as exc:
            errors.append({"id": page["id"], "error": str(exc)})
            print(f"FAILED {page['id']}: {exc}", flush=True)
    write_json(ROOT / "docs/sources/supplement_catalog.json", {"sources": sources})
    for source in sources:
        try:
            download(source)
        except Exception as exc:
            errors.append({"id": source["id"], "error": str(exc)})
            print(f"FAILED {source['id']}: {exc}", flush=True)
    write_json(
        ROOT / "data/processed/acquisition_supplement_status.json", {"errors": errors}
    )
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
