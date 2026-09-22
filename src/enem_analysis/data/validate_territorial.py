"""Independent integrity checks for the ENEM 2023 territorial deliverables."""

from __future__ import annotations

import json
import platform

import numpy as np
import pandas as pd

from enem_analysis.data.acquire import sha256, write_json
from enem_analysis.data.territorial_context import OUT, REGIONS
from enem_analysis.statistics.territorial import association


def checked(checks: list[dict], name: str, condition: bool, detail: object) -> None:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    checks.append({"checagem": name, "resultado": "aprovada", "detalhe": detail})


def main() -> None:
    checks: list[dict] = []
    manifest = json.loads((OUT / "frame_manifest.json").read_text(encoding="utf-8"))
    columns = [
        "NU_INSCRICAO",
        "TP_ST_CONCLUSAO",
        "TP_ENSINO",
        "IN_TREINEIRO",
        "TP_PRESENCA_MT",
        "NU_NOTA_MT",
        "codigo_ibge",
        "regiao",
        "renda_grupo",
        "TP_COR_RACA",
        "TP_SEXO",
        "Q006",
    ]
    frame = pd.read_parquet(OUT / "candidatos_2023.parquet", columns=columns)
    municipal = pd.read_parquet(OUT / "municipios_2023.parquet")
    context = pd.read_parquet(OUT / "contexto_municipal.parquet")
    expected_codes = {
        "TP_ST_CONCLUSAO": "2",
        "TP_ENSINO": "1",
        "IN_TREINEIRO": "0",
        "TP_PRESENCA_MT": "1",
    }
    checked(
        checks, "contagem elegível", len(frame) == manifest["n_elegivel"], len(frame)
    )
    checked(
        checks,
        "identificador único",
        frame.NU_INSCRICAO.notna().all() and not frame.NU_INSCRICAO.duplicated().any(),
        f"{frame.NU_INSCRICAO.nunique()} identificadores",
    )
    for field, code in expected_codes.items():
        checked(checks, f"filtro {field}", frame[field].eq(code).all(), code)
    score = frame.NU_NOTA_MT.to_numpy(float)
    checked(
        checks,
        "desfecho finito e não negativo",
        np.isfinite(score).all() and (score >= 0).all(),
        {"min": float(score.min()), "max": float(score.max())},
    )
    checked(
        checks,
        "zeros preservados",
        int((score == 0).sum()) == manifest["n_mt_zero"],
        int((score == 0).sum()),
    )
    valid_regions = set(REGIONS) | {"Não identificada"}
    checked(
        checks,
        "rótulos regionais canônicos",
        set(frame.regiao.unique()) <= valid_regions
        and set(REGIONS) <= set(frame.regiao),
        sorted(frame.regiao.unique()),
    )
    known = frame.codigo_ibge.notna()
    checked(
        checks,
        "cobertura territorial conservada",
        int(known.sum()) == manifest["n_vinculado"]
        and int((~known).sum()) == manifest["n_sem_codigo_municipio"],
        {"vinculados": int(known.sum()), "sem_municipio": int((~known).sum())},
    )
    checked(
        checks,
        "chaves municipais únicas",
        not municipal.codigo_ibge.duplicated().any()
        and not context.codigo_ibge.duplicated().any(),
        {"agregados": len(municipal), "contexto": len(context)},
    )
    checked(
        checks,
        "agregação municipal conserva candidatos",
        int(municipal.n.sum()) == int(known.sum()),
        int(municipal.n.sum()),
    )
    recomputed = (
        frame.loc[known]
        .groupby("codigo_ibge", observed=True)
        .NU_NOTA_MT.agg(["size", "mean"])
        .rename(columns={"size": "n_check", "mean": "mean_check"})
    )
    merged = municipal.set_index("codigo_ibge").join(recomputed, how="left")
    checked(
        checks,
        "médias municipais reproduzidas",
        merged.n.eq(merged.n_check).all()
        and np.allclose(merged.media, merged.mean_check, rtol=0, atol=1e-10),
        f"{len(merged)} municípios",
    )
    for prefix in [
        "prop_Q006_",
        "prop_Q001_",
        "prop_Q002_",
        "prop_TP_COR_RACA_",
        "prop_TP_ESCOLA_",
        "prop_TP_SEXO_",
    ]:
        total = municipal.filter(like=prefix).sum(axis=1)
        checked(
            checks,
            f"composições {prefix.rstrip('_')}",
            np.allclose(total, 1, rtol=0, atol=2e-12),
            "soma por município = 1",
        )
    representation = pd.read_csv(OUT / "representacao_populacoes.csv")
    checked(
        checks,
        "inclusão condicional e peso",
        representation.pi_condicional.eq(1).all()
        and representation.peso.eq(1).all()
        and representation.base_elegivel_n.eq(representation.amostra_bruta_n).all()
        and representation.base_elegivel_n.eq(representation.amostra_ponderada_n).all(),
        "pi=1; peso=1; nenhuma subamostragem",
    )
    assoc_saved = pd.read_csv(OUT / "associacoes_municipais.csv")
    saved = assoc_saved[
        assoc_saved.n_min.eq(30)
        & assoc_saved.regiao.eq("Brasil")
        & assoc_saved.rede_candidatos.eq("Todas")
        & assoc_saved.indicador.eq("renda_pc_2022")
    ].iloc[0]
    recalculated = association(
        municipal.loc[municipal.n.ge(30), "renda_pc_2022"],
        municipal.loc[municipal.n.ge(30), "media"],
        municipal.loc[municipal.n.ge(30), "n"],
    )
    checked(
        checks,
        "associação municipal reproduzida",
        all(
            np.isclose(saved[name], recalculated[name], rtol=0, atol=1e-12)
            for name in ["pearson", "spearman", "pearson_ponderado_n"]
        ),
        {
            name: recalculated[name]
            for name in ["pearson", "spearman", "pearson_ponderado_n"]
        },
    )
    checked(
        checks,
        "modelagem econométrica ausente",
        manifest["econometric_models"] == 0,
        "0 modelos; etapa adiada",
    )
    raw_hashes = {
        "ideb": sha256(
            OUT.parents[1]
            / "raw/municipal/territorial_2023/ideb_municipios_em_v2025.zip"
        ),
        "nota_ideb": sha256(
            OUT.parents[1] / "raw/municipal/territorial_2023/nota_ideb_2023.pdf"
        ),
        "tdi": sha256(
            OUT.parents[1] / "raw/municipal/territorial_2023/tdi_municipios_2023.zip"
        ),
        "censo_escolar": sha256(
            OUT.parents[1] / "raw/municipal/territorial_2023/censo_escolar_2023.zip"
        ),
    }
    result = {
        "validacao": "aprovada",
        "checagens": len(checks),
        "detalhes": checks,
        "python": platform.python_version(),
        "hashes_fontes_novas": raw_hashes,
        "hash_candidatos": sha256(OUT / "candidatos_2023.parquet"),
        "hash_municipios": sha256(OUT / "municipios_2023.parquet"),
    }
    write_json(OUT / "validacao.json", result)
    print(f"Validação aprovada: {len(checks)} verificações", flush=True)


if __name__ == "__main__":
    main()
