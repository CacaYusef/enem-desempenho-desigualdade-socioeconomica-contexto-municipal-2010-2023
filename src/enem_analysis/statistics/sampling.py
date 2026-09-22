"""Finite-population stratified allocation and support-aware raking."""

from __future__ import annotations

import math
from statistics import NormalDist

import numpy as np
import pandas as pd


def size_for_proportion(
    population: int,
    margin: float,
    deff: float = 1,
    confidence: float = 0.95,
    proportion: float = 0.5,
) -> int:
    if population < 1 or not 0 < margin < 1 or deff <= 0:
        raise ValueError("Invalid sample-size inputs")
    z = NormalDist().inv_cdf((1 + confidence) / 2)
    a = deff * z * z * proportion * (1 - proportion)
    return min(
        population, math.ceil(population * a / ((population - 1) * margin**2 + a))
    )


def allocate(counts: np.ndarray, size: int, minimum: int = 2) -> np.ndarray:
    """Proportional allocation with small-stratum floor and capacity constraints."""
    counts = np.asarray(counts, dtype=int)
    floor = np.minimum(counts, minimum)
    if size < floor.sum() or size > counts.sum() or (counts <= 0).any():
        raise ValueError("Allocation infeasible")
    low, high = 0.0, 1.0
    for _ in range(80):
        fraction = (low + high) / 2
        target = np.minimum(counts, np.maximum(floor, counts * fraction))
        if target.sum() > size:
            high = fraction
        else:
            low = fraction
    target = np.minimum(counts, np.maximum(floor, counts * low))
    result = np.floor(target).astype(int)
    remaining = size - int(result.sum())
    order = np.argsort(-(target - result), kind="stable")
    eligible = order[result[order] < counts[order]]
    result[eligible[:remaining]] += 1
    if result.sum() != size:
        raise ValueError("Allocation rounding failed")
    return result


def rake(
    frame: pd.DataFrame,
    base: np.ndarray,
    targets: dict[str, dict],
    tolerance: float = 1e-9,
    max_iterations: int = 2000,
) -> tuple[np.ndarray, dict]:
    """Positive weights matching specified margins; no unreported trimming."""
    weights = np.array(base, dtype=float, copy=True)
    if not np.isfinite(weights).all() or not (weights > 0).all():
        raise ValueError("Positive finite base weights required")
    totals = [sum(t.values()) for t in targets.values()]
    if not totals or not np.allclose(totals, totals[0]):
        raise ValueError("Margins must have a common total")
    total = float(totals[0])
    codes = {}
    for name, target in targets.items():
        if frame[name].isna().any() or set(frame[name]) != set(target):
            raise ValueError(f"Support mismatch for {name}")
        if any(v <= 0 for v in target.values()):
            raise ValueError("Zero target requires explicit population restriction")
        codes[name] = {level: frame[name].eq(level).to_numpy() for level in target}
    for iteration in range(1, max_iterations + 1):
        for name, target in targets.items():
            for level, required in target.items():
                mask = codes[name][level]
                weights[mask] *= required / weights[mask].sum()
        error = max(
            abs(weights[codes[name][level]].sum() - required) / total
            for name, t in targets.items()
            for level, required in t.items()
        )
        if error < tolerance:
            return weights, {
                "iterations": iteration,
                "max_error_fraction": error,
                "kish_deff": float(
                    len(weights) * np.sum(weights**2) / weights.sum() ** 2
                ),
                "effective_size_kish": float(weights.sum() ** 2 / np.sum(weights**2)),
                "min_weight": float(weights.min()),
                "max_weight": float(weights.max()),
            }
    raise ValueError("Raking failed to converge; no weights released")
