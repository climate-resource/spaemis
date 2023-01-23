import re

from spaemis.commands import cli


def test_cli_help(runner):
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert re.match(r"Usage: ", result.output)


def test_cli_gse_emis(runner):
    result = runner.invoke(cli, ["gse_emis"])
    assert result.exit_code == 0
    assert re.match(r"Usage: ", result.output)
