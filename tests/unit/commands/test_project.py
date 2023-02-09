import numpy as np
import numpy.testing as npt
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
        scale_inventory(config, inventory, 2040)


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
        scale_inventory(config, inventory, 2040)


def test_scale_inventory_constant(inventory):
    config = converter.structure(
        {
            "variable": "CO",
            "sector": "rail",
            "method": {"name": "constant"},
        },
        VariableConfig,
    )
    res = scale_inventory(config, inventory, 2040)
    assert isinstance(res, xr.DataArray)
    assert res.year == 2040

    # Check that data is constant
    inv_data = inventory.data[config.variable].sel(sector=config.sector)
    inv_data["year"] = 2040
    xr.testing.assert_allclose(inv_data, res)


def test_scale_inventory_relative(inventory):
    config = converter.structure(
        {
            "variable": "CO",
            "sector": "motor_vehicles",
            "method": {
                "name": "relative_change",
                "variable_id": "CH4-em-anthro",
                "source_id": "IAMC-MESSAGE-GLOBIOM-ssp245-1-1",
                "sector": "Transportation Sector",
            },
        },
        VariableConfig,
    )
    res = scale_inventory(config, inventory, 2040)
    assert isinstance(res, xr.DataArray)
    assert res.year == 2040

    inv_data = inventory.data[config.variable].sel(sector=config.sector)
    npt.assert_allclose(res.lat, inv_data.lat)
    npt.assert_allclose(res.lon, inv_data.lon)

    scale_factor = res / inv_data

    # Scale factors are all the same for a given country
    npt.assert_allclose(scale_factor.max(skipna=True), 1.209021, rtol=1e-5)
    npt.assert_allclose(scale_factor.min(skipna=True), 1.209021, rtol=1e-5)
