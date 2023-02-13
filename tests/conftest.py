import os

import geopandas
import pytest
import xarray as xr
from click.testing import CliRunner

from spaemis.config import DownscalingScenarioConfig, load_config
from spaemis.constants import RAW_DATA_DIR, TEST_DATA_DIR
from spaemis.input_data import database
from spaemis.inventory import EmissionsInventory


@pytest.fixture()
def runner(tmp_path):
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        runner._temp_dir = td
        yield runner


@pytest.fixture()
def config_file():
    return os.path.join(TEST_DATA_DIR, "config", "test-config.yaml")


@pytest.fixture()
def config(config_file) -> DownscalingScenarioConfig:
    return load_config(config_file)


@pytest.fixture(scope="module")
def inventory() -> EmissionsInventory:
    # For testing we use a decimated version of the vic inventory generated using
    # scripts/downsample_inventory.py
    vic_border = geopandas.read_file(
        os.path.join(RAW_DATA_DIR, "masks", "victoria_border_mask.gpkg")
    )
    data = xr.load_dataset(
        os.path.join(
            TEST_DATA_DIR,
            "inventory",
            "decimated",
            "inventory_decimated.nc",
        )
    )

    return EmissionsInventory(data, border_mask=vic_border, year=2016)


@pytest.fixture(autouse=True, scope="session")
def setup_database():
    database.register_path(os.path.join(TEST_DATA_DIR, "input4MIPs"))
