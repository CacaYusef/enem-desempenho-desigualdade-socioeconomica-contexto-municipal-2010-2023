"""Weighted descriptive measures, not standard errors or causal estimators."""

from __future__ import annotations

import numpy as np


def valid_pairs(values, weights):
    x, w = np.asarray(values, dtype=float), np.asarray(weights, dtype=float)
    if x.shape != w.shape or x.ndim != 1:
        raise ValueError("Values and weights must be matching vectors")
    if not np.isfinite(w).all() or (w <= 0).any():
        raise ValueError("Weights must be finite and strictly positive")
    mask = np.isfinite(x)
    return x[mask], w[mask]


def weighted_quantile(values, weights, probabilities):
    """Inverse empirical weighted CDF (leftmost observed value at target mass)."""
    x, w = valid_pairs(values, weights)
    p = np.atleast_1d(np.asarray(probabilities, dtype=float))
    if not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("Probabilities must lie in [0, 1]")
    if not len(x):
        return np.full(len(p), np.nan)
    order = np.argsort(x, kind="stable")
    cumulative = np.cumsum(w[order])
    idx = np.searchsorted(cumulative, p * cumulative[-1], side="left")
    return x[order][np.minimum(idx, len(x) - 1)]


def weighted_summary(values, weights):
    x, w = valid_pairs(values, weights)
    if not len(x):
        return {"n": 0, "peso_total": 0.0}
    mean = np.average(x, weights=w)
    variance = np.average((x - mean) ** 2, weights=w)
    q1, med, q3 = weighted_quantile(x, w, [0.25, 0.5, 0.75])
    low, high = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
    atypical = (x < low) | (x > high)
    inside = ~atypical
    return {
        "n": len(x),
        "peso_total": float(w.sum()),
        "media": float(mean),
        "variancia": float(variance),
        "dp": float(np.sqrt(variance)),
        "q1": float(q1),
        "mediana": float(med),
        "q3": float(q3),
        "minimo": float(x.min()),
        "maximo": float(x.max()),
        "cerca_inferior": float(low),
        "cerca_superior": float(high),
        "bigode_inferior": float(x[inside].min()),
        "bigode_superior": float(x[inside].max()),
        "n_atipicos_iqr": int(atypical.sum()),
        "pct_atipicos_ponderada": float(100 * w[atypical].sum() / w.sum()),
    }


def weighted_correlation(x, y, weights):
    x, y, w = [np.asarray(a, dtype=float) for a in (x, y, weights)]
    if x.shape != y.shape or x.shape != w.shape:
        raise ValueError("Correlation vectors must share shape")
    valid_pairs(x, w)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y, w = x[mask], y[mask], w[mask]
    if len(x) < 2:
        return np.nan, int(len(x)), float(w.sum())
    dx, dy = x - np.average(x, weights=w), y - np.average(y, weights=w)
    denominator = np.sqrt(np.sum(w * dx**2) * np.sum(w * dy**2))
    value = np.sum(w * dx * dy) / denominator if denominator else np.nan
    return float(value), int(len(x)), float(w.sum())
