import numpy as np
import pandas as pd
import pytest

from enem_analysis.data.calibrate_sample import benchmark_se, broad_age
from enem_analysis.statistics.sampling import allocate, rake, size_for_proportion


def test_finite_population_size_and_deff():
    assert size_for_proportion(100000000, 0.02, 1) == 2401
    assert size_for_proportion(100000000, 0.01, 1) == 9603
    assert size_for_proportion(100, 0.01, 2) <= 100
    assert size_for_proportion(100000, 0.01, 2) > size_for_proportion(100000, 0.01, 1)


def test_small_strata_capacity_and_exact_total():
    result = allocate(np.array([1, 2, 97]), 20)
    assert result.tolist() == [1, 2, 17]
    assert allocate(np.array([10, 20, 30]), 12).tolist() == [2, 4, 6]
    with pytest.raises(ValueError):
        allocate(np.array([10, 20, 30]), 4)


def test_raking_matches_margins_and_is_not_joint_calibration():
    frame = pd.DataFrame({"a": ["x", "x", "y", "y"], "b": ["u", "v", "u", "v"]})
    targets = {"a": {"x": 60.0, "y": 40.0}, "b": {"u": 50.0, "v": 50.0}}
    weights, report = rake(frame, np.array([9.0, 1.0, 1.0, 9.0]), targets)
    assert np.allclose([weights[:2].sum(), weights[[0, 2]].sum()], [60, 50])
    assert report["max_error_fraction"] < 1e-9
    assert not np.allclose(weights, [30.0, 30.0, 20.0, 20.0])


def test_raking_does_not_invent_missing_support():
    with pytest.raises(ValueError, match="Support"):
        rake(pd.DataFrame({"a": ["x"]}), np.array([1.0]), {"a": {"x": 1.0, "y": 1.0}})
    with pytest.raises(ValueError, match="common total"):
        rake(
            pd.DataFrame({"a": ["x"], "b": ["y"]}),
            np.array([1.0]),
            {"a": {"x": 1.0}, "b": {"y": 2.0}},
        )


def test_raking_leaves_original_weights_unchanged():
    base = np.array([1.0, 1.0])
    result, _ = rake(pd.DataFrame({"a": ["x", "y"]}), base, {"a": {"x": 3.0, "y": 1.0}})
    assert np.array_equal(base, [1.0, 1.0])
    assert np.allclose(result, [3.0, 1.0])


def test_domain_variance_retains_empty_psus():
    frame = pd.DataFrame(
        {"Estrato": ["a", "a"], "UPA": ["1", "2"], "weight": [1.0, 1.0]}
    )
    inventory = pd.DataFrame({"Estrato": ["a", "a", "a"], "UPA": ["1", "2", "3"]})
    # z=(0.5,-0.5,0); variance=3/2 * .5 / 2**2 = .1875.
    assert benchmark_se(
        frame, inventory, pd.Series([True, False], dtype="bool[pyarrow]")
    ) == pytest.approx(np.sqrt(0.1875))


def test_nonzero_lonely_psu_variance_is_not_reported_as_zero():
    frame = pd.DataFrame(
        {"Estrato": ["a", "b", "b"], "UPA": ["1", "2", "3"], "weight": [1.0, 1.0, 1.0]}
    )
    assert (
        benchmark_se(frame, frame[["Estrato", "UPA"]], pd.Series([True, False, False]))
        is None
    )


def test_age_cutpoints_are_explicit():
    assert broad_age(pd.Series([16, 17, 18, 19, 20, 80])).tolist() == [
        "ate17",
        "ate17",
        "18a19",
        "18a19",
        "20mais",
        "20mais",
    ]
