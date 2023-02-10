import re

from spaemis.commands import cli


def test_cli_help(runner):
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert re.match(r"Usage: ", result.output)


def test_cli_gse_emis(runner, mocker, tmpdir):
    mocked_call = mocker.patch("spaemis.commands.gse_emis_command.run_gse")
    out_dir = tmpdir / "out"
    assert not out_dir.exists()
    result = runner.invoke(
        cli,
        [
            "gse_emis",
            "-i",
            "testing",
            "--out_dir",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0
    assert out_dir.exists()

    mocked_call.assert_called_with(2020, 1, 1, "testing", str(out_dir))
