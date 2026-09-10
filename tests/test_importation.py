import io

import pandas as pd
import pytest
from openpyxl import Workbook

from enem_analysis.data.acquire import validate_url
from enem_analysis.data.enem_import import classify_geography, dictionary_sheets
from enem_analysis.data.integration_audit import geographical_crosswalk, normalize_name
from enem_analysis.data.municipal_catalog import sidra_sources
from enem_analysis.data.municipal_import import (
    numeric_value,
    validate_panel,
    value_bounds_audit,
)


@pytest.mark.parametrize(
    "raw,status",
    [
        ("", "ausente"),
        ("...", "nao_disponivel"),
        ("..", "nao_aplicavel"),
        ("X", "sigilo"),
    ],
)
def test_sidra_missing_values_are_not_zero(raw, status):
    assert numeric_value(raw) == (None, status)


def test_official_absolute_zero_is_distinct_from_missing():
    assert numeric_value("-") == (0.0, "zero_absoluto_sidra")
    assert numeric_value("-", source="inep") == (None, "marcador_fonte")
    assert numeric_value("0") == (0.0, "observado")
    assert numeric_value("-19046.434", source="pib") == (-19046.434, "observado")


def test_context_years_are_not_carried_forward_and_unmatched_values_are_retained():
    backbone = pd.DataFrame(
        {"codigo_ibge": ["1100015", "1100015"], "ano_dado": [2010, 2011]}
    )
    observations = pd.DataFrame(
        {
            "codigo_ibge": ["1100015", "9999999"],
            "ano_dado": [2010, 2010],
            "variavel": ["idhm", "idhm"],
            "valor": [0.6, 0.7],
        }
    )
    panel, unmatched = validate_panel(backbone, observations)
    assert panel.loc[panel.ano_enem == 2011, "idhm"].isna().all()
    assert unmatched.valor.tolist() == [0.7]
    assert len(panel) == 2


def test_duplicate_indicator_keys_fail_instead_of_silently_aggregating():
    backbone = pd.DataFrame({"codigo_ibge": ["1100015"], "ano_dado": [2010]})
    observations = pd.DataFrame(
        {
            "codigo_ibge": ["1100015"] * 2,
            "ano_dado": [2010] * 2,
            "variavel": ["idhm"] * 2,
            "valor": [0.6, 0.7],
        }
    )
    with pytest.raises(ValueError, match="Duplicate"):
        validate_panel(backbone, observations)


def test_school_and_exam_are_never_classified_as_residence():
    assert (
        classify_geography("CO_MUNICIPIO_ESC", "Código do município da escola")
        == "escola"
    )
    assert (
        classify_geography("CO_MUNICIPIO_PROVA", "Código do município da prova")
        == "prova"
    )
    assert (
        classify_geography("CO_MUNICIPIO", "Município sem definição")
        == "nao_confirmado"
    )


def test_geographical_match_uses_code_and_year_not_name():
    reference = pd.DataFrame(
        {
            "codigo_ibge": ["1100015"],
            "ano_dado": [2010],
            "municipio": ["Nome oficial"],
            "uf": ["RO"],
        }
    )
    source = pd.DataFrame(
        {
            "codigo_original_ENEM": ["1100015", "9999999", "1100015"],
            "ano_enem": [2010, 2010, 2009],
            "nome_original_ENEM": ["Outra grafia", "Nome oficial", "Nome oficial"],
            "tipo_localizacao": ["prova"] * 3,
        }
    )
    result = geographical_crosswalk(source, reference)
    assert result.correspondencia_validada.tolist() == [True, False, False]
    assert not result.vinculo_residencial_validado.any()


def test_sidra_requests_are_split_and_categories_validated():
    meta = {
        "variaveis": [{"id": 1}, {"id": 2}],
        "classificacoes": [
            {"id": 9, "categorias": [{"id": n, "nome": str(n)} for n in range(6)]}
        ],
    }
    recipe = {
        "table": 123,
        "years": [2010],
        "variables": [1, 2],
        "categories": {9: list(range(6))},
        "reason": "test",
    }
    sources = sidra_sources(recipe, meta)
    assert len(sources) == 2
    assert len({s["path"] for s in sources}) == 2
    assert all(len(s["variables"]) == 1 for s in sources)
    with pytest.raises(ValueError, match="Unknown category"):
        sidra_sources({**recipe, "categories": {9: [999]}}, meta)


def test_official_dictionary_categories_are_preserved():
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["NOME DA VARIÁVEL", "Descrição", "Categoria", "Descrição"])
    sheet.append(["Q001", "Pergunta original", "A", "Categoria original"])
    sheet.append([None, None, "B", "Outra categoria"])
    content = io.BytesIO()
    workbook.save(content)
    parsed = dictionary_sheets(content.getvalue())
    assert parsed[sheet.title]["variables"]["Q001"]["categories"] == [
        {"code": "A", "label": "Categoria original"},
        {"code": "B", "label": "Outra categoria"},
    ]


def test_only_declared_official_download_hosts_are_allowed():
    validate_url("https://download.inep.gov.br/microdados/example.zip")
    with pytest.raises(ValueError):
        validate_url("https://inep.gov.br.attacker.example/data.zip")
    with pytest.raises(ValueError):
        validate_url("file:///etc/passwd")


def test_name_normalization_does_not_make_fuzzy_matches():
    assert normalize_name("São  João-d’Oeste") == "SAO JOAO D OESTE"
    assert normalize_name("São João") != normalize_name("São José")


def test_semantic_limits_flag_values_without_changing_observations():
    observations = pd.DataFrame(
        {
            "ano_dado": [2010] * 4,
            "variavel": ["idhm", "idhm", "taxa", "taxa"],
            "valor": [0.7, 1.1, -1.0, 100.0],
        }
    )
    original = observations.copy(deep=True)
    dictionary = [
        {"ano_dado": 2010, "variavel": "idhm", "unidade": "Índice"},
        {"ano_dado": 2010, "variavel": "taxa", "unidade": "%"},
    ]
    flagged = value_bounds_audit(observations, dictionary)
    assert flagged.valor.tolist() == [1.1, -1.0]
    pd.testing.assert_frame_equal(observations, original)
    assert value_bounds_audit(observations, []).empty


def test_geography_never_uses_residence_word_in_school_or_exam_description():
    assert (
        classify_geography(
            "CO_MUNICIPIO_PROVA", "Município de prova, não de residência"
        )
        == "prova"
    )
