import numpy.testing as npt
import pytest
import xarray as xr

from spaemis.config import (
    ConstantScaleMethod,
    PointSource,
    VariableScalerConfig,
    converter,
)
from spaemis.project import (
    _process_source,
    calculate_point_sources,
    calculate_projections,
    scale_inventory,
)


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
        scale_inventory(config, inventory, 2040, {})


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
        scale_inventory(config, inventory, 2040, {})


def test_scale_inventory_constant(inventory):
    config = converter.structure(
        {
            "variable": "CO",
            "sector": "rail",
            "method": {"name": "constant"},
        },
        VariableScalerConfig,
    )
    res = scale_inventory(config, inventory, 2040, {})
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
    res = scale_inventory(config, inventory, 2040, {})
    assert isinstance(res, xr.Dataset)
    assert res.year == 2040

    inv_data = inventory.data[config.variable].sel(sector=config.sector)
    npt.assert_allclose(res.lat, inv_data.lat)
    npt.assert_allclose(res.lon, inv_data.lon)

    scale_factor = res[config.variable] / inv_data

    # Scale factors are all the same for a given country
    npt.assert_allclose(scale_factor.max(skipna=True), 1.209021, rtol=1e-5)
    npt.assert_allclose(scale_factor.min(skipna=True), 1.209021, rtol=1e-5)


def test_calculate_projections(config, inventory, loaded_timeseries):
    res = calculate_projections(config, inventory, loaded_timeseries)

    assert isinstance(res, xr.Dataset)

    assert "NOx" in res.data_vars
    assert "CO" in res.data_vars
    assert res["NOx"].dims == ("sector", "year", "lat", "lon")

    assert res["year"].isin(config.timeslices).all()

    # CO|motor_vehicles should be all nans as it wasn't included in the
    # downscaling config
    assert res["CO"].sel(sector="motor_vehicles").isnull().all()
    # but CO|industry should have data
    assert not res["CO"].sel(sector="industry").isnull().all()

    assert "H2" in res.data_vars
    assert res["H2"].shape == res["CO"].shape


def test_calculate_projections_with_default(config, inventory, loaded_timeseries):
    config.scalers.default_scaler = ConstantScaleMethod()

    res = calculate_projections(config, inventory, loaded_timeseries)

    assert (res["sector"] == inventory.data["sector"]).all()

    exp = inventory.data["CO"]

    # CO|architect_coating should be held constant
    xr.testing.assert_allclose(
        res["CO"]
        .sel(sector="architect_coating", year=2040)
        .reset_coords("year", drop=True),
        exp.sel(sector="architect_coating"),
    )
    # CO|industry should be scaled
    with pytest.raises(AssertionError):
        xr.testing.assert_allclose(
            res["CO"].sel(sector="industry", year=2040).reset_coords("year", drop=True),
            exp.sel(sector="industry"),
        )


@pytest.mark.parametrize("sector", ["industry", "gas_leak"])
@pytest.mark.parametrize("variable", ["H2", "CO"])
def test_process_sources(inventory, variable, sector):
    point = PointSource(
        variable=variable,
        sector=sector,
        quantity=600,
        location=[
            (-37.56, 143.85),  # Ballarat
            (-38.21, 146.399),  # La Trobe Valley
            (-27.47, 153.03),  # Brisbane (out of domain)
        ],
    )
    res = _process_source(point, inventory.data.lat, inventory.data.lon)
    assert res.sum() == 400
    assert (
        res[variable].sel(sector=sector, lat=-38.21, lon=146.4, method="nearest") == 200
    )


def test_calculate_point_sources(inventory, config):
    config.point_sources.sources.append(
        PointSource(
            variable="H2",
            sector="gas_leak",
            quantity=600,
            location=[
                (-37.56, 143.85),  # Ballarat
                (-38.21, 146.399),  # La Trobe Valley
                (-27.47, 153.03),  # Brisbane (out of domain)
            ],
        )
    )
    config.point_sources.sources.append(
        PointSource(
            variable="NH3",
            sector="gas_leak",
            quantity=500,
            location=[
                (-37.56, 143.85),  # Ballarat
                (-38.21, 146.399),  # La Trobe Valley
            ],
        )
    )
    res = calculate_point_sources(config, inventory)

    assert res["sector"].values.tolist() == ["gas_leak", "industry"]
    assert "H2" in res.data_vars
    assert "NH3" in res.data_vars

    assert res["H2"].sel(sector="gas_leak").sum() == 600 * 2 / 3
    assert res["NH3"].sel(sector="gas_leak").sum() == 500
