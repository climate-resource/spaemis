import pkg_resources
import pytest
from click.testing import CliRunner

from spaemis.constants import ROOT_DIR
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
