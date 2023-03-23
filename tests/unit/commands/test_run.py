import os.path
import re

import dotenv
import pytest

from spaemis.commands import cli
from spaemis.constants import TEST_DATA_DIR


def test_cli_help(runner):
    result = runner.invoke(cli, ["run", "--help"])
    assert result.exit_code == 0
    assert re.match(r"Usage: ", result.output)


@pytest.mark.xfail(reason="No INPUT4MIPS data on server")
def test_cli_run(runner, tmpdir):
    dotenv.load_dotenv()
    # Run the test configuration with a decimated inventory
    result = runner.invoke(
        cli,
        [
            "run",
            "--config",
            os.path.join(TEST_DATA_DIR, "config", "test-config.yaml"),
            "--output-dir",
            os.path.join(tmpdir, "results"),
        ],
    )
    assert result.exit_code == 0
    expected_files = [
        "inputs",
        "inputs/config.yaml",
        "outputs",
        "outputs/test/v20230317_1_test_projections.nc",
    ]
    for fname in expected_files:
        assert os.path.exists(os.path.join(tmpdir, "results", fname))
