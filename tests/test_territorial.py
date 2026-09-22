import numpy as np
import pandas as pd
import pytest

from enem_analysis.data.territorial_analysis import eligibility_mask
from enem_analysis.data.territorial_context import canonical_region, merge_context
from enem_analysis.statistics.territorial import association, quintile_codes, summary


def test_eligibility_not_conditioned_on_other_scores_or_essay():
    f = pd.DataFrame(
        {
            "TP_ST_CONCLUSAO": ["2"] * 5,
            "TP_ENSINO": ["1"] * 5,
            "IN_TREINEIRO": ["0"] * 5,
            "TP_PRESENCA_MT": ["1"] * 5,
            "NU_NOTA_MT": [0, 1200, np.nan, -1, np.inf],
            "NU_NOTA_REDACAO": [np.nan] * 5,
        }
    )
    assert eligibility_mask(f).tolist() == [True, True, False, False, False]
    f.loc[0, "IN_TREINEIRO"] = "1"
    assert not eligibility_mask(f).iloc[0]


def test_left_join_preserves_missing_geography_and_rejects_duplicate_context():
    left = pd.DataFrame({"codigo_ibge": ["1", None, "1", "2"]})
    right = pd.DataFrame({"codigo_ibge": ["1"], "context": [7]})
    result = merge_context(left, right)
    assert len(result) == 4
    assert result.context.isna().sum() == 2
    with pytest.raises(ValueError):
        merge_context(left, pd.concat([right, right]))


def test_quintile_ties_and_missing_not_split():
    result = quintile_codes([1, 1, 2, 3, np.nan, 5], [1, 1, 2, 4])
    assert result.iloc[:4].tolist() == [1, 1, 3, 4]
    assert pd.isna(result.iloc[4]) and result.iloc[5] == 5


def test_rank_correlation_is_not_categorical_code_correlation():
    result = association([1, 2, 3, np.nan], [1, 4, 9, 10])
    assert result["spearman"] == pytest.approx(1)
    assert result["pearson"] < 1
    assert result["n_pares"] == 3
    assert np.isnan(association([1, 1, 1], [1, 2, 3])["pearson"])


def test_population_dispersion_and_inverse_edf():
    s = summary([1, 2, 3, 4, np.nan])
    assert s["n"] == 4
    assert s["media"] == 2.5 and s["mediana"] == 2
    assert s["variancia"] == 1.25
    assert summary([0, 1, 1, 1, 100])["max"] == 100


def test_region_labels_cannot_silently_drop_centro_oeste():
    result = canonical_region(pd.Series(["Centro-oeste", "Norte", None]))
    assert result.iloc[0] == "Centro-Oeste"
    assert pd.isna(result.iloc[2])
    with pytest.raises(ValueError):
        canonical_region(pd.Series(["Inexistente"]))
