import os

import pytest
import scmdata
from click.testing import CliRunner

from spaemis.config import DownscalingScenarioConfig, load_config
from spaemis.constants import TEST_DATA_DIR
from spaemis.input_data import database
from spaemis.inventory import EmissionsInventory, TestInventory


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
    return TestInventory.load_from_directory()


@pytest.fixture(autouse=True, scope="session")
def setup_database():
    database.register_path(os.path.join(TEST_DATA_DIR, "input4MIPs"))


@pytest.fixture()
def loaded_timeseries() -> dict[str, scmdata.ScmRun]:
    return {
        "emissions": scmdata.ScmRun(
            os.path.join(TEST_DATA_DIR, "config", "emissions_country.csv")
        ).filter(region="AUS")
    }


@pytest.fixture()
def selected_timeseries(loaded_timeseries) -> scmdata.ScmRun:
    res = loaded_timeseries["emissions"].filter(
        variable="Emissions|H2|Transportation Sector"
    )
    assert res.shape == (1, 1)
    return res
