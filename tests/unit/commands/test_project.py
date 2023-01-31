import pytest
import xarray as xr

from spaemis.commands import cli
from spaemis.commands.project_command import scale_inventory
from spaemis.config import VariableConfig, converter, load_config


def test_cli_project(runner, config_file, tmpdir, mocker):
    mocked_call = mocker.patch("spaemis.commands.project_command.scale_inventory")
    mocked_inv = mocker.patch("spaemis.commands.project_command.load_inventory")
    out_dir = tmpdir / "out"
    assert not out_dir.exists()

    cfg = load_config(config_file)
    result = runner.invoke(
        cli,
        [
            "project",
            "--config",
            config_file,
            "--out_dir",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    assert out_dir.exists()
    mocked_call.assert_any_call(cfg.variables[0], mocked_inv.return_value)
    mocked_call.assert_any_call(cfg.variables[1], mocked_inv.return_value)


def test_scale_inventory_missing_variable(inventory):
    config = converter.structure(
        {
            "variable": "missing",
            "sector": "Industrial",
            "method": {"name": "constant"},
        },
        VariableConfig,
    )
    with pytest.raises(ValueError, match="Variable missing not available in inventory"):
        scale_inventory(config, inventory)


def test_scale_inventory_missing_sector(inventory):
    config = converter.structure(
        {
            "variable": "CO",
            "sector": "unknown",
            "method": {"name": "constant"},
        },
        VariableConfig,
    )
    with pytest.raises(ValueError, match="Sector unknown not available in inventory"):
        scale_inventory(config, inventory)


def test_scale_inventory(inventory):
    config = converter.structure(
        {
            "variable": "CO",
            "sector": "rail",
            "method": {"name": "constant"},
        },
        VariableConfig,
    )
    res = scale_inventory(config, inventory)
    assert isinstance(res, xr.DataArray)
