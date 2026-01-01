import pytest
from unittest.mock import patch, MagicMock
from rpm_ring import (
    rpm_name_parser,
    load_csv_file,
    process_rpm_data,
    get_retired_ids,
    flatten,
    main,
)
import yaml


@pytest.fixture(scope="function")
def rpm_data():
    with open("tests/data/rpm_name_parts.yml", "r") as f:
        rpm_test_data = yaml.safe_load(f)
    yield rpm_test_data


@pytest.fixture(scope="function")
def input_data():
    import os

    os.environ["CSV_FILE"] = "tests/data/input_sample.csv"


@pytest.fixture(scope="function")
def input_data_with_duplicates():
    import os

    os.environ["CSV_FILE"] = "tests/data/input_with_duplicates.csv"


def test_rpm_name_parser_good(rpm_data):
    for entry in rpm_data:
        rpm_name = entry["name"]
        expected_result = tuple([v for k, v in entry["parts"].items()])

        result = rpm_name_parser(rpm_name)
        assert result == expected_result, f"Failed for RPM name: {rpm_name}"


bad_rpm_named = [
    "package-1.2.3-4.el7.x86_64",
    "package-1.2.3-4.x86_64",
    "package-1.2.3-4.el7",
    "package-1.2.3-4",
    "package-1.2.3",
    "package-1",
    "package",
    "package-1.2.3rc1-4.x86_64.rpm",
    "package-2:1.2.3-4.x86_64.rpm",
    "",
]


def test_rpm_name_parser_bad():
    for rpm_name in bad_rpm_named:
        assert rpm_name_parser(rpm_name) is None, f"Failed for RPM name: {rpm_name}"


@pytest.mark.parametrize(
    "version,release,expected_retire_list",
    [
        (
            5,
            1,
            [
                "38778815",
                "39188647",
                "39188667",
                "38778799",
                "39188631",
                "39188651",
                "38778806",
                "39188638",
                "39188658",
                "39188632",
                "39188652",
                "38778801",
                "39188633",
                "39188653",
                "38778802",
                "39188634",
                "39188654",
                "38778803",
                "39188635",
                "39188655",
                "38778804",
                "39188636",
                "39188656",
                "38778805",
                "39188637",
                "39188657",
                "38778811",
                "39188643",
                "39188663",
                "38778810",
                "39188642",
                "39188662",
                "38778809",
                "39188641",
                "39188661",
                "38778816",
                "39188648",
                "39188668",
                "38778807",
                "39188639",
                "39188659",
                "38778808",
                "39188640",
                "39188660",
                "38778817",
                "39188649",
                "39188669",
                "38778812",
                "39188644",
                "39188664",
                "38778813",
                "39188645",
                "39188665",
                "38778814",
                "39188646",
                "39188666",
                "38778818",
                "39188650",
                "39188670",
            ],
        ),
        (
            1,
            1,
            [
                "39655167",
                "39188687",
                "34609336",
                "38778815",
                "39188647",
                "39188667",
                "39655151",
                "39188671",
                "34609321",
                "38778799",
                "39188631",
                "39188651",
                "39655158",
                "39188678",
                "34609327",
                "38778806",
                "39188638",
                "39188658",
                "39655152",
                "39188672",
                "38778800",
                "39188632",
                "39188652",
                "39655153",
                "39188673",
                "34609322",
                "38778801",
                "39188633",
                "39188653",
                "39655154",
                "39188674",
                "34609323",
                "38778802",
                "39188634",
                "39188654",
                "39655155",
                "39188675",
                "34609324",
                "38778803",
                "39188635",
                "39188655",
                "39655156",
                "39188676",
                "34609325",
                "38778804",
                "39188636",
                "39188656",
                "39655157",
                "39188677",
                "34609326",
                "38778805",
                "39188637",
                "39188657",
                "39655163",
                "39188683",
                "34609332",
                "38778811",
                "39188643",
                "39188663",
                "39655162",
                "39188682",
                "34609331",
                "38778810",
                "39188642",
                "39188662",
                "39655161",
                "39188681",
                "34609330",
                "38778809",
                "39188641",
                "39188661",
                "39655168",
                "39188688",
                "34609337",
                "38778816",
                "39188648",
                "39188668",
                "39655159",
                "39188679",
                "34609328",
                "38778807",
                "39188639",
                "39188659",
                "39655160",
                "39188680",
                "34609329",
                "38778808",
                "39188640",
                "39188660",
                "39655169",
                "39188689",
                "34609338",
                "38778817",
                "39188649",
                "39188669",
                "39655164",
                "39188684",
                "34609333",
                "38778812",
                "39188644",
                "39188664",
                "39655165",
                "39188685",
                "34609334",
                "38778813",
                "39188645",
                "39188665",
                "39655166",
                "39188686",
                "34609335",
                "38778814",
                "39188646",
                "39188666",
                "39655170",
                "39188690",
                "34609339",
                "38778818",
                "39188650",
                "39188670",
            ],
        ),
    ],
)
@patch("rpm_ring.versions_to_keep")
@patch("rpm_ring.releases_per_version_to_keep")
def test_main(
    mocked_versions, mocked_releases, version, release, expected_retire_list, input_data
):
    mocked_versions = version
    mocked_releases = release
    r = main().split(",")
    assert r.sort() == expected_retire_list.sort()


@pytest.mark.parametrize(
    "expected_retire_list",
    [
        ["40243049", "39655172", "39372567", "39372565", "34355751"],
    ],
)
@patch("rpm_ring.versions_to_keep", 5)
@patch("rpm_ring.releases_per_version_to_keep", 1)
def test_main_with_duplicates(expected_retire_list, input_data_with_duplicates):
    r = main().split(",")
    assert r.sort() == expected_retire_list.sort()
