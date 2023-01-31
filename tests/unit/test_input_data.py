import os

import xarray as xr

from spaemis.constants import TEST_DATA_DIR
from spaemis.input_data import InputEmissionsDatabase


def test_emissions_database():
    database = InputEmissionsDatabase([os.path.join(TEST_DATA_DIR, "input4MIPs")])

    assert len(database.available_data)

    ch4_data = database.load(
        variable_id="CH4-em-anthro", source_id="IAMC-MESSAGE-GLOBIOM-ssp245-1-1"
    )

    assert isinstance(ch4_data, xr.Dataset)
    assert "CH4_em_anthro" in ch4_data.data_vars
