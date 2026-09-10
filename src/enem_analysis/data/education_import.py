"""Read all source rows, then expose published municipality totals as candidates."""

from __future__ import annotations

import io
import json
import zipfile

import pandas as pd

from enem_analysis.data.acquire import MANIFESTS, RAW, ROOT, sha256, write_json
from enem_analysis.data.municipal_import import numeric_value

OUT = ROOT / "data/processed/municipal/education"
DOCS = ROOT / "docs/sources/municipal/education"


def import_year(year: int) -> dict:
    meta = json.loads(
        (MANIFESTS / f"inep_rendimento_{year}.json").read_text(encoding="utf-8")
    )
    result_path = DOCS / f"{year}.json"
    outdir = OUT / f"year={year}"
    if result_path.exists() and (outdir / "totais_longos.parquet").exists():
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if result.get("import_version") == 2:
            for name, expected in result["processed_sha256"].items():
                if sha256(outdir / name) != expected:
                    raise ValueError(f"Processed checksum mismatch: {outdir / name}")
            print(f"EXISTS EDUCATION {year}: {result['source_rows']}", flush=True)
            return result
    print(f"IMPORT EDUCATION {year}", flush=True)
    with zipfile.ZipFile(RAW / meta["path"]) as archive:
        files = [n for n in archive.namelist() if n.lower().endswith(".xlsx")]
        if not files:
            files = [n for n in archive.namelist() if n.lower().endswith(".xls")]
        if len(files) != 1:
            raise ValueError(f"Ambiguous spreadsheet in {year}: {files}")
        workbook = pd.ExcelFile(io.BytesIO(archive.read(files[0])), engine="calamine")
        frames = []
        header_metadata = {}
        for sheet in workbook.sheet_names:
            raw = workbook.parse(sheet, header=None, dtype=str, keep_default_na=False)
            data_mask = raw[0].astype(str).str.strip().eq(str(year))
            first_data = int(raw.index[data_mask][0])
            header_metadata[sheet] = raw.iloc[:first_data].values.tolist()
            extras = raw.loc[data_mask].iloc[:, 61:]
            if extras.apply(lambda c: c.str.strip().ne("")).any().any():
                raise ValueError(f"Nonempty extra education columns: {year}/{sheet}")
            frame = raw.loc[data_mask].iloc[:, :61].copy()
            if frame.shape[1] != 61:
                raise ValueError(f"Unexpected education layout: {year}/{sheet}")
            frame.columns = [f"col_{i:02}" for i in range(61)]
            frame["source_sheet"] = sheet
            frame["source_excel_row"] = frame.index + 1
            frames.append(frame)
        workbook.close()
    all_rows = pd.concat(frames, ignore_index=True)
    keys = ["col_03", "col_05", "col_06"]
    duplicates = int(all_rows.duplicated(keys).sum())
    if duplicates:
        raise ValueError(
            f"Duplicate municipality/location/network keys in {year}: {duplicates}"
        )
    # Total is an explicit published category; no weighted average of networks.
    total = all_rows[
        all_rows.col_05.str.strip().eq("Total")
        & all_rows.col_06.str.strip().eq("Total")
    ]
    mappings = {}
    for offset, rate in [(0, "aprovacao"), (18, "reprovacao"), (36, "abandono")]:
        positions = (
            {
                "fundamental": 18,
                "fundamental_anos_iniciais": 16,
                "fundamental_anos_finais": 17,
                "medio": 24,
            }
            if year == 2010
            else {
                "fundamental": 7,
                "fundamental_anos_iniciais": 8,
                "fundamental_anos_finais": 9,
                "medio": 19,
            }
        )
        for level, base in positions.items():
            mappings[base + offset] = f"educ_{rate}_{level}_pct"
    dictionary = []
    observations = []
    for column, alias in mappings.items():
        original_labels = {
            sheet: [row[column] for row in rows if len(row) > column and row[column]]
            for sheet, rows in header_metadata.items()
        }
        dictionary.append(
            {
                "variavel": alias,
                "descricao": alias.replace("_", " "),
                "fonte": "INEP — Taxas de rendimento escolar",
                "link_fonte": meta["url"],
                "ano_dado": year,
                "unidade": "%",
                "nivel_geografico": "Município",
                "forma_calculo": (
                    "Taxa publicada para Localização=Total e Dependência/Rede=Total. "
                    "Nenhuma média calculada entre redes."
                ),
                "categorias_codigo": {"localizacao": "Total", "rede": "Total"},
                "categorias_descricao": original_labels,
                "limitacoes": (
                    "Taxas referem-se às escolas no município. Universo, ensino de "
                    "8/9 anos e pandemia exigem avaliação de comparabilidade. "
                    "'--' é preservado como marcador da fonte."
                ),
                "source_id": meta["id"],
                "selecionada_para_modelo": False,
                "source_column_index_zero_based": column,
            }
        )
        for code, raw in total[["col_03", f"col_{column:02}"]].itertuples(
            index=False, name=None
        ):
            value, status = numeric_value(raw, source="inep")
            if raw.strip() == "--":
                value, status = None, "marcador_inep_sem_taxa"
            observations.append(
                {
                    "ano_dado": year,
                    "codigo_ibge": str(code).strip(),
                    "variavel": alias,
                    "valor": value,
                    "valor_original": raw,
                    "status_valor": status,
                    "source_id": meta["id"],
                }
            )
    outdir.mkdir(parents=True, exist_ok=True)
    all_rows.to_parquet(
        outdir / "linhas_fonte.parquet", index=False, compression="zstd"
    )
    tidy = pd.DataFrame(observations)
    tidy.to_parquet(outdir / "totais_longos.parquet", index=False, compression="zstd")
    result = {
        "import_version": 2,
        "extra_data_columns_all_empty": True,
        "processed_sha256": {
            name: sha256(outdir / name)
            for name in ["linhas_fonte.parquet", "totais_longos.parquet"]
        },
        "year": year,
        "source_id": meta["id"],
        "source_member": files[0],
        "source_rows": len(all_rows),
        "source_rows_excluded": 0,
        "published_total_rows": len(total),
        "duplicate_keys": duplicates,
        "total_missing_values": int(tidy.valor.isna().sum()),
        "out_of_0_100_preserved": int(((tidy.valor < 0) | (tidy.valor > 100)).sum()),
        "headers": header_metadata,
        "dictionary": dictionary,
    }
    write_json(result_path, result)
    print(
        f"OK EDUCATION {year}: {len(all_rows):,} source rows, "
        f"{len(total):,} municipality totals",
        flush=True,
    )
    return result


def main() -> None:
    errors = []
    for year in range(2010, 2024):
        try:
            import_year(year)
        except Exception as exc:
            errors.append({"year": year, "error": str(exc)})
            print(f"FAILED EDUCATION {year}: {exc}", flush=True)
    write_json(ROOT / "data/processed/education_import_status.json", {"errors": errors})
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
