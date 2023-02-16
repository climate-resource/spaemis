import logging
import os

import pytest
import scmdata
import scmdata.testing
import xarray as xr

from spaemis.config import InputTimeseries
from spaemis.constants import TEST_DATA_DIR
from spaemis.input_data import (
    InputEmissionsDatabase,
    initialize_database,
    load_timeseries,
)

TEST_INPUT_DATA = os.path.join(TEST_DATA_DIR, "input4MIPs")


@pytest.mark.parametrize("inp", [[TEST_INPUT_DATA], TEST_INPUT_DATA])
def test_emissions_database(inp):
    database = InputEmissionsDatabase(inp)
    assert database.paths == [TEST_INPUT_DATA]
    assert len(database.available_data)

    ch4_data = database.load(
        variable_id="CH4-em-anthro", source_id="IAMC-MESSAGE-GLOBIOM-ssp245-1-1"
    )

    assert isinstance(ch4_data, xr.Dataset)
    assert "CH4_em_anthro" in ch4_data.data_vars


def test_database_register_overlapping(caplog):
    database = InputEmissionsDatabase(TEST_INPUT_DATA)
    assert database.paths == [TEST_INPUT_DATA]
    with caplog.at_level(logging.INFO):
        database.register_path(TEST_INPUT_DATA)

    assert "Found 0 new entries" in caplog.text
    assert database.paths == [TEST_INPUT_DATA]


def test_database_register_empty():
    database = InputEmissionsDatabase()
    database.register_path("no-data-here")
    assert not len(database.available_data)


@pytest.mark.parametrize(
    "paths",
    [
        (
            os.path.join(
                TEST_DATA_DIR,
                "input4MIPs/CMIP6/ScenarioMIP/IAMC/IAMC-MESSAGE-GLOBIOM-ssp245-1-1/atmos/mon/BC_em_anthro",
            ),
        ),
        (
            os.path.join(
                TEST_DATA_DIR,
                "input4MIPs/CMIP6/ScenarioMIP/IAMC/IAMC-MESSAGE-GLOBIOM-ssp245-1-1/atmos/mon/BC_em_anthro",
            ),
            os.path.join(
                TEST_DATA_DIR,
                "input4MIPs/CMIP6/ScenarioMIP/IAMC/IAMC-MESSAGE-GLOBIOM-ssp245-1-1/atmos/mon/CO2_em_anthro",
            ),
        ),
    ],
)
def test_initialize_data(monkeypatch, paths):
    monkeypatch.setenv(
        "SPAEMIS_INPUT_PATHS",
        ",".join(paths),
    )

    res = initialize_database()
    assert res.paths == list(paths)


def test_load_timeseries():
    res = load_timeseries(
        [
            InputTimeseries(name="test", path="emissions_country.csv", filters=[{}]),
            InputTimeseries(
                name="test2",
                path="emissions_country.csv",
                filters=[dict(variable="Emissions|H2|Transportation Sector")],
            ),
            InputTimeseries(
                name="test3",
                path="emissions_country.csv",
                filters=[
                    dict(variable="Emissions|H2|Industrial Sector"),
                    dict(region="World", keep=False),
                ],
            ),
        ],
        root_dir=os.path.join(TEST_DATA_DIR, "config"),
    )

    exp = scmdata.ScmRun(os.path.join(TEST_DATA_DIR, "config", "emissions_country.csv"))

    scmdata.testing.assert_scmdf_almost_equal(
        res["test"], exp, check_ts_names=False, allow_unordered=True
    )
    scmdata.testing.assert_scmdf_almost_equal(
        res["test2"],
        exp.filter(variable="Emissions|H2|Transportation Sector"),
        check_ts_names=False,
        allow_unordered=True,
    )

    scmdata.testing.assert_scmdf_almost_equal(
        res["test3"],
        exp.filter(variable="Emissions|H2|Industrial Sector").filter(
            region="World", keep=False
        ),
        check_ts_names=False,
        allow_unordered=True,
    )


def test_load_timeseries_duplicate():
    with pytest.raises(ValueError, match="Duplicate input timeseries found: test"):
        load_timeseries(
            [
                InputTimeseries(
                    name="test", path="emissions_country.csv", filters=[{}]
                ),
                InputTimeseries(
                    name="test", path="emissions_country.csv", filters=[{}]
                ),
            ],
            root_dir=os.path.join(TEST_DATA_DIR, "config"),
        )
