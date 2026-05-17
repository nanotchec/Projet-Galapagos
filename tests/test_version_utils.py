from galapagos.utils.version import display_version, normalize_version


def test_normalize_version():
    assert normalize_version("v1.15.4") == "v1_15_4"
    assert normalize_version("v1_15_4") == "v1_15_4"
    assert normalize_version("1.15.4") == "v1_15_4"
    assert normalize_version("V1.15.4") == "v1_15_4"
    assert normalize_version("v1.12.2") == "v1_12_2"


def test_display_version():
    assert display_version("v1_15_4") == "V1.15.4"
    assert display_version("1.15.4") == "V1.15.4"
    assert display_version("V1.15.4") == "V1.15.4"
    assert display_version("v1.15.4") == "V1.15.4"
