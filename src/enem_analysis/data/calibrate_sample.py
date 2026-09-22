"""Calibrate comparable margins to an explicitly approximate PNADC target."""

from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd

from enem_analysis.data.acquire import sha256, write_json
from enem_analysis.data.sampling_plan import OUT
from enem_analysis.statistics.sampling import rake

RACES = ["Branca", "Preta", "Parda", "Amarela", "Indigena"]
INCOME = ["ate1SM", "1a2SM", "2a5SM", "mais5SM"]


def income_scale(plan: dict) -> float:
    label = next(c["label"] for c in plan["income_categories"] if c["code"] == "B")
    value = re.search(r"R\$\s*([\d.,]+)", label).group(1).rstrip(".")
    return float(value.replace(".", "").replace(",", "."))


def broad_age(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="raise")
    return pd.cut(
        numeric, [-1, 17, 19, 200], labels=["ate17", "18a19", "20mais"]
    ).astype(str)


def benchmark_se(
    frame: pd.DataFrame, inventory: pd.DataFrame, indicator: pd.Series
) -> float | None:
    """WR Taylor ratio variance, all original PSUs including zero domain units."""
    total = frame.weight.sum()
    proportion = (frame.weight * indicator.astype(float)).sum() / total
    part = frame[["Estrato", "UPA"]].copy()
    part["z"] = frame.weight * (indicator.astype(float) - proportion)
    clusters = part.groupby(["Estrato", "UPA"], as_index=False).z.sum()
    complete = inventory.merge(
        clusters, on=["Estrato", "UPA"], how="left", validate="one_to_one"
    )
    complete["z"] = complete.z.fillna(0)
    variance = 0.0
    for _, group in complete.groupby("Estrato"):
        m = len(group)
        if m < 2:
            if group.z.abs().sum() > 0:
                return None
            continue
        variance += m / (m - 1) * float(((group.z - group.z.mean()) ** 2).sum())
    return float(np.sqrt(variance) / total)


def calibrate_year(year: int) -> dict:
    plan = json.loads((OUT / f"plano_{year}.json").read_text(encoding="utf-8"))
    frame = pd.read_parquet(OUT / f"cadastro_elegivel_{year}.parquet")
    sample = pd.read_parquet(OUT / f"amostra_estratificada_{year}.parquet")
    if year < 2012:
        sample["peso_calibrado_proxy"] = np.nan
        sample["status_calibracao"] = "sem_referencia_anual_pnadc"
        sample.to_parquet(OUT / f"amostra_com_pesos_{year}.parquet", index=False)
        result = {
            "year": year,
            "external_calibration": False,
            "reason": "PNADC starts in 2012; no borrowed target from later years",
        }
        write_json(OUT / f"calibracao_{year}.json", result)
        return result
    pnad = pd.read_parquet(OUT / f"pnad_proxy_{year}.parquet")
    inventory = pd.read_parquet(OUT / f"pnad_psus_{year}.parquet")
    pnad["idade_ampla"] = broad_age(pnad.idade)
    pnad["escola"] = pnad.escola.fillna("Nao_informada")
    scale = income_scale(plan)
    pnad["renda_faixa"] = (
        pd.cut(
            pnad.renda_domiciliar,
            [-0.01, scale, 2 * scale, 5 * scale, np.inf],
            labels=INCOME,
        )
        .astype("string")
        .fillna("Sem_renda_informada")
    )
    pnad["raca_sexo"] = pnad.raca.astype(str) + "|" + pnad.sexo.astype(str)
    margins = []
    for name in ["raca", "sexo", "regiao", "renda_faixa", "escola", "idade_ampla"]:
        for level in sorted(pnad[name].dropna().unique()):
            indicator = pnad[name].eq(level).fillna(False)
            count = float(pnad.loc[indicator, "weight"].sum())
            se = benchmark_se(pnad, inventory, indicator)
            margins.append(
                {
                    "ano": year,
                    "variavel": name,
                    "categoria": level,
                    "n_pnad": int(indicator.sum()),
                    "total_estimado": count,
                    "proporcao": count / pnad.weight.sum(),
                    "erro_padrao_proporcao_taylor_wr": se,
                    "cv_proporcao": se / (count / pnad.weight.sum())
                    if se is not None and count
                    else None,
                }
            )
    pd.DataFrame(margins).to_csv(
        OUT / f"margens_ibge_{year}.csv", index=False, encoding="utf-8-sig"
    )
    valid = pnad[pnad.raca.isin(RACES) & pnad.renda_faixa.isin(INCOME)]
    joint = valid.groupby(["raca", "regiao", "renda_faixa", "sexo"], observed=True).agg(
        n_pnad=("weight", "size"), total_estimado=("weight", "sum")
    )
    grid = pd.MultiIndex.from_product(
        [RACES, sorted(valid.regiao.unique()), INCOME, ["F", "M"]],
        names=joint.index.names,
    )
    joint = joint.reindex(grid, fill_value=0).reset_index()
    joint["proporcao_dominio_renda_conhecida"] = (
        joint.total_estimado / joint.total_estimado.sum()
    )
    joint.to_csv(OUT / f"conjunta_pnad_{year}.csv", index=False, encoding="utf-8-sig")
    for data in [frame, sample]:
        if data.TP_FAIXA_ETARIA.isna().any():
            raise ValueError("Missing ENEM age requires an explicit domain rule")
        data["idade_ampla"] = pd.to_numeric(data.TP_FAIXA_ETARIA).map(
            lambda x: "ate17" if x <= 2 else "18a19" if x <= 4 else "20mais"
        )
        data["raca_sexo"] = data.raca + "|" + data.sexo
        data["regiao_renda_enem"] = data.regiao_escola + "|" + data.renda_categoria
    ref = pnad[pnad.raca.isin(RACES) & pnad.sexo.isin(["F", "M"])].copy()
    domain = frame[frame.raca.isin(RACES) & frame.sexo.isin(["F", "M"])]
    selected = sample[sample.raca.isin(RACES) & sample.sexo.isin(["F", "M"])].copy()
    total = len(domain)
    targets = {
        name: (ref.groupby(name).weight.sum() / ref.weight.sum() * total).to_dict()
        for name in ["raca_sexo", "idade_ampla"]
    }
    # Geographic/income ENEM margins are INTERNAL: do not relabel school as residence.
    targets["regiao_renda_enem"] = (
        domain.regiao_renda_enem.value_counts().astype(float).to_dict()
    )
    weights, diagnostic = rake(selected, selected.peso_desenho.to_numpy(), targets)
    sample["peso_calibrado_proxy"] = np.nan
    sample.loc[selected.index, "peso_calibrado_proxy"] = weights
    sample["status_calibracao"] = np.where(
        sample.peso_calibrado_proxy.notna(),
        "experimental_proxy_pnad_demografica",
        "fora_dominio_calibracao_raca_sexo",
    )
    sample["peso_calibrado_proxy_normalizado"] = sample.peso_calibrado_proxy / np.mean(
        weights
    )
    selected["weight_cal"] = weights
    residuals = []
    for name, target in targets.items():
        for level, expected in target.items():
            got = selected.loc[selected[name].eq(level), "weight_cal"].sum()
            residuals.append(
                {
                    "ano": year,
                    "margem": name,
                    "categoria": level,
                    "alvo": expected,
                    "obtido": got,
                    "residuo": got - expected,
                }
            )
    pd.DataFrame(residuals).to_csv(
        OUT / f"residuos_calibracao_{year}.csv", index=False, encoding="utf-8-sig"
    )
    sample.to_parquet(
        OUT / f"amostra_com_pesos_{year}.parquet", index=False, compression="zstd"
    )
    result = {
        "year": year,
        "external_calibration": True,
        "experimental_proxy": True,
        "population_pnad_proxy": float(pnad.weight.sum()),
        "raw_pnad_domain_n": len(pnad),
        "calibration_target_scale": total,
        "sample_calibrated_n": len(selected),
        "sample_not_calibrated_n": len(sample) - len(selected),
        "population_unknown_race_sex_pnad_n": len(pnad) - len(ref),
        "external_margins": ["raca_sexo", "idade_ampla"],
        "internal_margins": ["regiao_escola_x_renda_enem"],
        "region_residence_calibrated": False,
        "income_external_calibrated": False,
        "school_type_external_calibrated": False,
        "joint_cells_total": len(joint),
        "joint_cells_zero": int(joint.n_pnad.eq(0).sum()),
        "joint_cells_under5": int(joint.n_pnad.lt(5).sum()),
        "joint_cells_under30": int(joint.n_pnad.lt(30).sum()),
        "income_scale_reais": scale,
        **diagnostic,
    }
    result["calibration_factor_min"] = float((weights / selected.peso_desenho).min())
    result["calibration_factor_max"] = float((weights / selected.peso_desenho).max())
    write_json(OUT / f"calibracao_{year}.json", result)
    print(
        f"CALIBRATED {year}: n={len(selected)}, "
        f"Kish DEFF={diagnostic['kish_deff']:.3f}",
        flush=True,
    )
    return result


def main() -> None:
    results = [calibrate_year(y) for y in range(2010, 2024)]
    combined = pd.concat(
        [
            pd.read_parquet(OUT / f"amostra_com_pesos_{y}.parquet")
            for y in range(2010, 2024)
        ],
        ignore_index=True,
    )
    combined.to_parquet(
        OUT / "amostra_enem_2010_2023.parquet", index=False, compression="zstd"
    )
    combined.to_csv(
        OUT / "amostra_enem_2010_2023.csv", index=False, encoding="utf-8-sig"
    )
    write_json(OUT / "calibracao_resumo.json", results)
    groups = pd.concat(
        [pd.read_csv(OUT / f"alocacao_{y}.csv") for y in range(2010, 2024)]
    )
    groups.to_csv(
        OUT / "alocacao_todos_estratos.csv", index=False, encoding="utf-8-sig"
    )
    plans = [
        json.loads((OUT / f"plano_{y}.json").read_text(encoding="utf-8"))
        for y in range(2010, 2024)
    ]
    pd.DataFrame([s for p in plans for s in p["scenarios"]]).to_csv(
        OUT / "cenarios_tamanho_amostral.csv", index=False
    )
    write_json(
        OUT / "sample_manifest.json",
        {
            "rows": len(combined),
            "seed_rule": "20260920 + year; numpy default_rng",
            "source": "annual eligible frames with complete valid scores",
            "parquet_sha256": sha256(OUT / "amostra_enem_2010_2023.parquet"),
            "base_probability": "n_h/N_h conditional on ENEM eligible frame",
            "external_weights": "experimental demographic calibration to PNADC proxy",
            "national_inclusion_probability": None,
        },
    )


if __name__ == "__main__":
    main()
