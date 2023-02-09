import os

import pkg_resources
import pytest
from click.testing import CliRunner

from spaemis.constants import TEST_DATA_DIR
from spaemis.input_data import database
from spaemis.inventory import load_inventory


@pytest.fixture()
def runner(tmp_path):
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        runner._temp_dir = td
        yield runner


@pytest.fixture()
def config_file():
    return pkg_resources.resource_filename("spaemis", "config/scenarios/ssp245.yaml")


@pytest.fixture(scope="module")
def inventory():
    return load_inventory("victoria", 2016)


@pytest.fixture(autouse=True, scope="session")
def setup_database():
    database.register_path(os.path.join(TEST_DATA_DIR, "input4MIPs"))
