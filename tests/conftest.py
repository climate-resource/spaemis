import pkg_resources
import pytest
from click.testing import CliRunner


@pytest.fixture()
def runner(tmp_path):
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        runner._temp_dir = td
        yield runner


@pytest.fixture()
def config_file():
    return pkg_resources.resource_filename("spaemis", "config/scenarios/ssp245.yaml")
