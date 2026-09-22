"""Publication-ready tabular assets kept separate from analytical inputs."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable


def save_table_csv(
    directory: Path,
    number: int,
    headers: Iterable[object],
    rows: Iterable[Iterable[object]],
) -> Path:
    """Export exactly the formatted cells displayed in a report table."""
    header = [str(value) for value in headers]
    data = [[str(value) for value in row] for row in rows]
    if any(len(row) != len(header) for row in data):
        raise ValueError("Report table rows must match the number of headers")

    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"tabela_{number:02d}.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream, delimiter=";")
        writer.writerow(header)
        writer.writerows(data)
    return path
