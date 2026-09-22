import numpy as np
import pandas as pd

from enem_analysis.data.sampling_plan import SCORES
from enem_analysis.data.temporal_municipal_correlations import (
    aggregate_year,
    association_rows,
    normalize_municipality_code,
)


def test_normalize_municipality_code_preserves_only_seven_digits():
    result = normalize_municipality_code(
        pd.Series(["1100015", "1100023.0", "", None, "123"])
    )
    assert result.iloc[:2].tolist() == ["1100015", "1100023"]
    assert result.iloc[2:].isna().all()


def test_aggregate_year_computes_municipal_score_means_and_keeps_zero():
    frame = pd.DataFrame(
        {
            "CO_MUNICIPIO_ESC": ["1100015", "1100015", "1100023", None],
            **{score: [0.0, 100.0, 300.0, 900.0] for score in SCORES},
        }
    )
    result = aggregate_year(frame, 2010).set_index("codigo_ibge")
    assert result.loc["1100015", "n"] == 2
    assert result.loc["1100015", "media_NU_NOTA_MT"] == 50.0
    assert result.loc["1100023", "media_NU_NOTA_REDACAO"] == 300.0


def test_association_rows_uses_municipal_pairs_and_candidate_weight_sensitivity():
    municipal = pd.DataFrame(
        {
            "ano": [2010, 2010, 2010],
            "n": [30, 40, 50],
            "indicador": [1.0, 2.0, 3.0],
            **{f"media_{score}": np.array([10.0, 20.0, 30.0]) for score in SCORES},
        }
    )
    rows = association_rows(municipal, {"indicador": "Indicador"}, "teste")
    principal = [
        row for row in rows if row["n_min"] == 30 and row["nota"] == "NU_NOTA_MT"
    ][0]
    assert principal["n_pares"] == 3
    assert np.isclose(principal["pearson"], 1.0)
    assert np.isclose(principal["spearman"], 1.0)
    assert np.isclose(principal["pearson_ponderado_n"], 1.0)
