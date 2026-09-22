"""Report assets retain the visible table cells without moving analytical data."""

import csv

import pytest

from enem_analysis.visualization.report_assets import save_table_csv


def test_save_table_csv_uses_report_order_and_semicolon(tmp_path):
    path = save_table_csv(
        tmp_path / "tables",
        3,
        ["Região", "Média"],
        [["Norte", "502,9"], ["Sul", "568,5"]],
    )
    assert path.name == "tabela_03.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        assert list(csv.reader(stream, delimiter=";")) == [
            ["Região", "Média"],
            ["Norte", "502,9"],
            ["Sul", "568,5"],
        ]


def test_save_table_csv_rejects_malformed_rows(tmp_path):
    with pytest.raises(ValueError, match="number of headers"):
        save_table_csv(tmp_path / "tables", 1, ["A", "B"], [["only one"]])
    assert not (tmp_path / "tables").exists()
