import numpy as np
import pytest

from enem_analysis.statistics.descriptive import (
    weighted_correlation,
    weighted_quantile,
    weighted_summary,
)


def test_known_weighted_moments_and_quantiles():
    result = weighted_summary([1, 3], [1, 3])
    assert result["media"] == 2.5
    assert result["variancia"] == 0.75
    assert result["dp"] == pytest.approx(np.sqrt(0.75))
    assert weighted_quantile([1, 3], [1, 3], [0, 0.25, 0.5, 1]).tolist() == [1, 1, 3, 3]


def test_missing_is_not_zero_and_extreme_is_not_removed():
    result = weighted_summary([1, 2, np.nan, 100], [1, 1, 10, 1])
    assert result["n"] == 3
    assert result["peso_total"] == 3
    assert result["media"] == pytest.approx(103 / 3)
    assert result["maximo"] == 100


def test_pairwise_weighted_correlation_and_constant():
    r, n, w = weighted_correlation([1, 2, 3, np.nan], [2, 4, 6, 8], [1, 2, 4, 8])
    assert r == pytest.approx(1)
    assert n == 3 and w == 7
    assert np.isnan(weighted_correlation([1, 1], [2, 4], [1, 1])[0])


def test_invalid_weight_rejected():
    with pytest.raises(ValueError):
        weighted_summary([1, 2], [1, 0])
    with pytest.raises(ValueError):
        weighted_quantile([1], [1], [1.1])


def test_weight_scale_does_not_change_distribution():
    a = weighted_summary([1, 3, 5], [1, 2, 3])
    b = weighted_summary([1, 3, 5], [10, 20, 30])
    for key in ["media", "variancia", "mediana", "q1", "q3"]:
        # Normalization is invariant mathematically, up to floating-point rounding.
        assert a[key] == pytest.approx(b[key], rel=1e-14)
