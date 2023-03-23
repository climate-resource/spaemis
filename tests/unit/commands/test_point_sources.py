import os
import re

from spaemis.commands import cli
from spaemis.constants import RAW_DATA_DIR, TEST_DATA_DIR


def test_point_sources_help(runner):
    result = runner.invoke(cli, ["point-source", "--help"])
    assert result.exit_code == 0
    assert re.match(r"Usage: ", result.output)


def test_cli_point_sources(runner):
    with open(os.path.join(TEST_DATA_DIR, "config", "test_point_sources.yaml")) as fh:
        exp_result = fh.read()
    result = runner.invoke(
        cli,
        [
            "point-source",
            os.path.join(
                RAW_DATA_DIR,
                "configuration",
                "point_sources",
                "federal_locations.csv",
            ),
        ],
    )
    assert result.output.strip("\n") == exp_result.strip("\n")
    assert result.exit_code == 0


def test_cli_point_sources_directory(runner):
    result = runner.invoke(
        cli,
        [
            "point-source",
            RAW_DATA_DIR,
        ],
    )
    assert result.exit_code == 2

    assert f"File '{RAW_DATA_DIR}' is a directory" in result.output


def test_cli_point_sources_incorrect(runner):
    result = runner.invoke(
        cli,
        [
            "point-source",
            "unknown",
        ],
    )
    assert result.exit_code == 2

    assert "File 'unknown' does not exist" in result.output
