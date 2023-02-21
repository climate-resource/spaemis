import os

import xarray as xr

from spaemis.commands import cli
from spaemis.config import load_config


def test_cli_project(runner, config_file, tmpdir, mocker, inventory):
    exp_dataset = xr.concat(
        [
            inventory.data.assign_coords(year=2040).expand_dims("year", axis=1),
            inventory.data.assign_coords(year=2060).expand_dims("year", axis=1),
        ],
        dim="year",
    )
    exp_cfg = load_config(config_file)
    exp_cfg.timeslices = [2040, 2060]

    mocked_call = mocker.patch(
        "spaemis.commands.project_command.calculate_projections",
        return_value=exp_dataset,
    )
    mocked_inv = mocker.patch("spaemis.commands.project_command.load_inventory")
    mocker.patch(
        "spaemis.commands.project_command.load_config",
        return_value=exp_cfg,
    )
    mocked_timeseries = mocker.patch("spaemis.commands.project_command.load_timeseries")
    out_dir = tmpdir / "out"
    assert not out_dir.exists()

    result = runner.invoke(
        cli,
        [
            "project",
            "--config",
            config_file,
            "--out-dir",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    assert out_dir.exists()
    assert (out_dir / "2040").exists()
    assert (out_dir / "2060").exists()

    assert len(os.listdir((out_dir / "2040"))) == len(exp_dataset["sector"])

    mocked_call.assert_called_with(
        exp_cfg, mocked_inv.return_value, mocked_timeseries.return_value
    )
