"""Offline integrity and reconciliation checks; never selects an analytical sample."""

from __future__ import annotations

import csv
import io
import json
from datetime import UTC, datetime

import pandas as pd
import pyarrow.parquet as pq

from enem_analysis.data.acquire import MANIFESTS, RAW, ROOT, sha256, write_json
from enem_analysis.data.enem_import import package


def main() -> None:
    docs = ROOT / "docs/sources"
    processed = ROOT / "data/processed"
    checks = []

    def require(condition: bool, label: str) -> None:
        checks.append({"check": label, "passed": bool(condition)})
        if not condition:
            raise ValueError(label)

    manifests = sorted(MANIFESTS.glob("*.json"))
    for path in manifests:
        record = json.loads(path.read_text(encoding="utf-8"))
        target = RAW / record["path"]
        require(sha256(target) == record["sha256"], f"raw_sha256:{record['id']}")
    print(f"OK {len(manifests)} registered raw checksums", flush=True)
    require(
        sha256(
            RAW
            / "microdados_enem_2023/microdados_enem_2023"
            / "DADOS/MICRODADOS_ENEM_2023.csv"
        )
        == "c8b1fae0a97b6ac826d950d16696efa3d89c133b0165128aadd2997c2315b666",
        "preexisting_2023_csv_unchanged",
    )
    inventories = []
    for year in range(2010, 2024):
        audit = json.loads((docs / f"enem/{year}.json").read_text(encoding="utf-8"))
        target = processed / f"enem/year={year}/participantes.parquet"
        require(sha256(target) == audit["parquet_sha256"], f"enem_sha256:{year}")
        parquet = pq.ParquetFile(target)
        require(parquet.metadata.num_rows == audit["rows"], f"enem_rows:{year}")
        require(parquet.schema_arrow.names == audit["columns"], f"enem_columns:{year}")
        with package(year) as (_, opener):
            with opener(audit["main_member"]) as stream:
                rows = csv.DictReader(
                    io.TextIOWrapper(stream, encoding="cp1252"), delimiter=";"
                )
                first = {
                    key: (value if value != "" else None)
                    for key, value in next(rows).items()
                }
        actual = next(parquet.iter_batches(batch_size=1)).to_pylist()[0]
        require(actual == first, f"first_record_all_fields_equal_raw:{year}")
        geography = pd.read_parquet(
            processed / f"enem/year={year}/codigos_municipais.parquet"
        )
        require(
            geography.groupby("campo_geografico")
            .registros.sum()
            .eq(audit["rows"])
            .all(),
            f"geography_record_conservation:{year}",
        )
        require(
            audit["sampling"] is None and audit["rows_excluded"] == 0,
            f"no_sampling_or_row_exclusion:{year}",
        )
        inventories.append(audit)
        print(
            f"OK ENEM {year}: integrity, rows, schema and source first record",
            flush=True,
        )

    municipal = processed / "municipal"
    panel = pd.read_parquet(municipal / "base_municipio_ano.parquet")
    long = pd.read_parquet(municipal / "indicadores_longos.parquet")
    reference = pd.read_parquet(municipal / "referencia_municipal_anual.parquet")
    require(
        not panel.duplicated(["ano_enem", "codigo_ibge"]).any(), "panel_unique_keys"
    )
    require(panel.codigo_ibge.str.fullmatch(r"[0-9]{7}").all(), "panel_ibge_format")
    require(len(panel) == len(reference), "reference_row_conservation")
    require(
        long.ano_dado.eq(long.ano_enem).all() and long.defasagem_anos.eq(0).all(),
        "exact_year_no_interpolation",
    )
    require(
        panel.filter(regex=r"^media_|^participantes_enem").isna().all().all(),
        "no_residence_or_sample_assumed_in_enem_statistics",
    )
    # Independently compare each imported variable against the wide context table.
    for variable, group in long.groupby("variavel"):
        compared = group.merge(
            panel[["ano_enem", "codigo_ibge", variable]],
            on=["ano_enem", "codigo_ibge"],
            how="inner",
            validate="one_to_one",
        )
        require(
            (
                compared.valor.eq(compared[variable])
                | (compared.valor.isna() & compared[variable].isna())
            ).all(),
            f"long_wide_values_equal:{variable}",
        )
    for year in range(2010, 2024):
        audit = json.loads(
            (docs / f"municipal/education/{year}.json").read_text(encoding="utf-8")
        )
        for name, expected in audit["processed_sha256"].items():
            require(
                sha256(municipal / f"education/year={year}" / name) == expected,
                f"education_sha256:{year}:{name}",
            )
        source = pd.read_parquet(
            municipal / f"education/year={year}/linhas_fonte.parquet"
        )
        require(len(source) == audit["source_rows"], f"education_rows:{year}")
        require(
            audit["extra_data_columns_all_empty"], f"education_no_lost_columns:{year}"
        )
    result = {
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "passed": True,
        "checks_count": len(checks),
        "checks": checks,
        "raw_manifests_verified": len(manifests),
        "enem_rows_imported_not_sample": sum(a["rows"] for a in inventories),
        "sample_size": None,
        "statistical_parameters": None,
        "scope": "Integrity and ingestion reconciliation, not inferential validity.",
        "first_record_check": "Deterministic engineering check, not a research sample.",
    }
    write_json(docs / "verification.json", result)
    print(f"PASS: {len(checks)} offline integrity/reconciliation checks", flush=True)


if __name__ == "__main__":
    main()
