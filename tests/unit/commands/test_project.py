import os

import numpy.testing as npt
import pytest
import xarray as xr

from spaemis.commands import cli
from spaemis.commands.project_command import calculate_projections, scale_inventory
from spaemis.config import (
    ConstantScaleMethod,
    VariableScalerConfig,
    converter,
    load_config,
)


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
    out_dir = tmpdir / "out"
    assert not out_dir.exists()

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
    assert (out_dir / "2040").exists()
    assert (out_dir / "2060").exists()

    assert len(os.listdir((out_dir / "2040"))) == len(exp_dataset["sector"])

    mocked_call.assert_called_with(exp_cfg, mocked_inv.return_value)


def test_scale_inventory_missing_variable(inventory):
    config = converter.structure(
        {
            "variable": "missing",
            "sector": "Industrial",
            "method": {"name": "constant"},
        },
        VariableScalerConfig,
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
        VariableScalerConfig,
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
        VariableScalerConfig,
    )
    res = scale_inventory(config, inventory, 2040)
    assert isinstance(res, xr.Dataset)
    assert res.year == 2040

    # Check that data is constant
    exp_data = inventory.data[config.variable].sel(sector=[config.sector])
    exp_data["year"] = 2040
    exp_data = exp_data.expand_dims("year", axis=1)

    xr.testing.assert_allclose(exp_data.to_dataset(name=config.variable), res)


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
        VariableScalerConfig,
    )
    res = scale_inventory(config, inventory, 2040)
    assert isinstance(res, xr.Dataset)
    assert res.year == 2040

    inv_data = inventory.data[config.variable].sel(sector=config.sector)
    npt.assert_allclose(res.lat, inv_data.lat)
    npt.assert_allclose(res.lon, inv_data.lon)

    scale_factor = res[config.variable] / inv_data

    # Scale factors are all the same for a given country
    npt.assert_allclose(scale_factor.max(skipna=True), 1.209021, rtol=1e-5)
    npt.assert_allclose(scale_factor.min(skipna=True), 1.209021, rtol=1e-5)


def test_calculate_projections(config, inventory):
    res = calculate_projections(config, inventory)

    assert isinstance(res, xr.Dataset)

    assert "NOx" in res.data_vars
    assert "CO" in res.data_vars
    assert res["NOx"].dims == ("sector", "year", "lat", "lon")

    assert res["year"].isin(config.timeslices).all()

    # CO|motor_vehicles should be all nans as it wasn't included in the downscaling config
    assert res["CO"].sel(sector="motor_vehicles").isnull().all()
    # but CO|industry should have data
    assert not res["CO"].sel(sector="industry").isnull().all()


def test_calculate_projections_with_default(config, inventory):
    config.default_scaler = ConstantScaleMethod()

    res = calculate_projections(config, inventory)

    assert (res["sector"] == inventory.data["sector"]).all()

    # CO|architect_coating should be held constant
    xr.testing.assert_allclose(
        res["CO"]
        .sel(sector="architect_coating", year=2040)
        .reset_coords("year", drop=True),
        inventory.data["CO"].sel(sector="architect_coating"),
    )
    # CO|industry should be scaled
    with pytest.raises(AssertionError):
        xr.testing.assert_allclose(
            res["CO"].sel(sector="industry", year=2040).reset_coords("year", drop=True),
            inventory.data["CO"].sel(sector="industry"),
        )
