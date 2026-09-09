import enem_analysis


def test_package_version_is_exposed() -> None:
    assert enem_analysis.__version__ == "0.1.0"
