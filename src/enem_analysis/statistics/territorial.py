"""Finite-frame descriptive functions; no model fitting or hypothesis tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import rankdata


def summary(values) -> dict:
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if not len(x):
        return {"n": 0}
    q1, median, q3 = np.quantile(x, [0.25, 0.5, 0.75], method="inverted_cdf")
    lower, upper = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
    outside = (x < lower) | (x > upper)
    return {
        "n": len(x),
        "media": float(x.mean()),
        "mediana": float(median),
        "variancia": float(x.var()),
        "dp": float(x.std()),
        "q1": float(q1),
        "q3": float(q3),
        "min": float(x.min()),
        "max": float(x.max()),
        "n_atipicos_iqr": int(outside.sum()),
        "pct_atipicos_iqr": 100 * float(outside.mean()),
    }


def association(x, y, weights=None) -> dict:
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.ndim != 1 or x.shape != y.shape:
        raise ValueError("Paired vectors required")
    w = np.ones(len(x)) if weights is None else np.asarray(weights, float)
    if w.shape != x.shape or not np.isfinite(w).all() or (w <= 0).any():
        raise ValueError("Finite positive weights required")
    keep = np.isfinite(x) & np.isfinite(y)
    x, y, w = x[keep], y[keep], w[keep]
    result = {
        "n_pares": len(x),
        "peso_pares": float(w.sum()),
        "pearson": np.nan,
        "spearman": np.nan,
        "pearson_ponderado_n": np.nan,
    }
    if len(x) < 3 or not x.std() or not y.std():
        return result
    result["pearson"] = float(np.corrcoef(x, y)[0, 1])
    result["spearman"] = float(np.corrcoef(rankdata(x), rankdata(y))[0, 1])
    dx, dy = x - np.average(x, weights=w), y - np.average(y, weights=w)
    result["pearson_ponderado_n"] = float(
        np.sum(w * dx * dy) / np.sqrt(np.sum(w * dx**2) * np.sum(w * dy**2))
    )
    return result


def quintile_codes(values, cuts) -> pd.Series:
    """National fixed cutpoints; keep all ties together, permit empty bins."""
    x = pd.to_numeric(pd.Series(values), errors="raise")
    edges = np.asarray(cuts, float)
    if (
        edges.shape != (4,)
        or not np.isfinite(edges).all()
        or (np.diff(edges) < 0).any()
    ):
        raise ValueError("Four nondecreasing finite cuts required")
    out = pd.Series(pd.NA, index=x.index, dtype="Int64")
    present = x.notna()
    out.loc[present] = np.searchsorted(edges, x.loc[present], side="left") + 1
    return out
