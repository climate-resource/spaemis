import logging
import os

import pytest
import xarray as xr

from spaemis.constants import TEST_DATA_DIR
from spaemis.input_data import InputEmissionsDatabase, initialize_database

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
