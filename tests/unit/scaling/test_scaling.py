import logging
import os
import re

import numpy.testing as npt
import pytest
import scmdata
import xarray as xr

from spaemis.config import (
    ConstantScaleMethod,
    PointSourceMethod,
    RelativeChangeMethod,
    TimeseriesMethod,
)
from spaemis.constants import RAW_DATA_DIR
from spaemis.scaling import (
    ConstantScaler,
    PointSourceScaler,
    ProxyScaler,
    RelativeChangeScaler,
    TimeseriesScaler,
    get_scaler,
    get_scaler_by_config,
)
from spaemis.scaling.timeseries import get_timeseries
from spaemis.unit_registry import unit_registry as ur


def test_get_scaler_missing():
    with pytest.raises(ValueError, match="Unknown scaler: missing"):
        get_scaler("missing")


def test_get_scaler():
    cls = get_scaler("constant")
    assert cls == ConstantScaler


def test_get_scaler_by_config():
    res = get_scaler_by_config(ConstantScaleMethod(scale_factor=0.1))
    assert isinstance(res, ConstantScaler)

    assert res.scaling_factor == 0.1


class TestConstantScaler:
    def test_create_default(self):
        res = ConstantScaler.create_from_config(ConstantScaleMethod())
        assert res.scaling_factor == 1.0

    @pytest.mark.parametrize("scale_factor", [0, 0.1, 1.5])
    def test_create(self, scale_factor):
        res = ConstantScaler.create_from_config(
            ConstantScaleMethod(scale_factor=scale_factor)
        )
        assert res.scaling_factor == scale_factor


class TestRelativeScaler:
    def test_create(self):
        res = RelativeChangeScaler.create_from_config(
            RelativeChangeMethod(
                source_id="source", variable_id="variable", sector="Industrial Sector"
            )
        )

        assert res.source_id == "source"
        assert res.variable_id == "variable"
        assert res.sector == "Industrial Sector"

    def test_create_missing_sector(self):
        with pytest.raises(ValueError, match="Unknown input4MIPs sector: not-a-sector"):
            RelativeChangeScaler.create_from_config(
                RelativeChangeMethod(
                    source_id="source", variable_id="variable", sector="not-a-sector"
                )
            )

    def test_run(self, inventory):
        scaler = RelativeChangeScaler(
            source_id="IAMC-MESSAGE-GLOBIOM-ssp245-1-1",
            variable_id="NOx-em-anthro",
            sector="Industrial Sector",
        )

        data = xr.DataArray(
            0,
            coords=dict(lat=range(10), lon=range(10)),
            dims=("lat", "lon"),
            attrs={"units": "kg NOx / yr / cell"},
        )

        res = scaler(data=data, inventory=inventory, target_year=2040)

        assert res.shape == data.shape
        assert ur.Unit(res.attrs["units"]) == ur.Unit("kg NOx/yr/cell")


class TestTimeseriesScaler:
    def test_create(self):
        res = TimeseriesScaler.create_from_config(
            TimeseriesMethod(
                proxy="population",
                source_timeseries="inputs",
                source_filters=[{"variable": "H2"}],
            )
        )

        assert res.proxy == "population"
        assert res.source_timeseries == "inputs"
        assert res.source_filters == [{"variable": "H2"}]

    def test_run(self, inventory, loaded_timeseries):
        scaler = TimeseriesScaler(
            proxy="population",
            proxy_region="population",
            source_timeseries="emissions",
            source_filters=[
                {
                    "variable": "Emissions|H2|Transportation Sector",
                }
            ],
        )

        data = xr.DataArray(
            0, coords=dict(lat=range(10), lon=range(10)), dims=("lat", "lon")
        )

        res = scaler(
            data=data,
            inventory=inventory,
            target_year=2020,
            timeseries=loaded_timeseries,
        )

        assert res.shape == data.shape
        assert ur.Unit(res.attrs["units"]) == ur.Unit("kg H2/yr/cell")

    def test_run_inventory(self, inventory, loaded_timeseries):
        scaler = TimeseriesScaler(
            proxy="inventory|industry",
            proxy_region="australian_inventory|IND",
            source_timeseries="emissions",
            source_filters=[
                {
                    "variable": "Emissions|H2|Industrial Sector",
                }
            ],
        )

        data = xr.DataArray(
            0, coords=dict(lat=range(10), lon=range(10)), dims=("lat", "lon")
        )

        res = scaler(
            data=data,
            inventory=inventory,
            target_year=2020,
            timeseries=loaded_timeseries,
        )

        assert isinstance(res, xr.DataArray)
        assert res.shape == data.shape
        assert ur.Unit(res.attrs["units"]) == ur.Unit("kg H2 / yr / cell")

    def test_run_australian_inventory(self, inventory, loaded_timeseries):
        scaler = TimeseriesScaler(
            proxy="australian_inventory|ENE",
            proxy_region="australian_inventory|ENE",
            source_timeseries="emissions",
            source_filters=[
                {
                    "variable": "Emissions|H2|Industrial Sector",
                }
            ],
        )

        data = xr.DataArray(
            0, coords=dict(lat=range(10), lon=range(10)), dims=("lat", "lon")
        )

        res = scaler(
            data=data,
            inventory=inventory,
            target_year=2020,
            timeseries=loaded_timeseries,
        )

        assert isinstance(res, xr.DataArray)
        assert res.shape == data.shape
        assert ur.Unit(res.attrs["units"]) == ur.Unit("kg H2/yr/cell")

    def test_run_failed_too_many(self, loaded_timeseries):
        with pytest.raises(ValueError, match="More than one match was found for"):
            get_timeseries(
                loaded_timeseries,
                "emissions",
                [{"variable": "Emissions|H2|*"}],
                2020,
            )

    def test_run_failed_not_enough(self, loaded_timeseries):
        filters = [
            {"variable": "Emissions|H2|Transportation Sector", "region": "other"}
        ]
        with pytest.raises(
            ValueError,
            match=re.escape(
                f"No data matching {filters} was found in emissions input data"
            ),
        ):
            get_timeseries(
                loaded_timeseries,
                "emissions",
                filters,
                2020,
            )

    def test_no_source(self, loaded_timeseries):
        with pytest.raises(
            ValueError,
            match="Source dataset is not loaded: other",
        ):
            get_timeseries(
                loaded_timeseries,
                "other",
                [],
                2020,
            )

    def test_run_failed_extrapolation(self, loaded_timeseries):
        with pytest.raises(
            ValueError, match="No timeseries data for year=2000 available"
        ):
            loaded_timeseries["emissions"] = loaded_timeseries["emissions"].filter(
                year=range(2030, 2100)
            )
            get_timeseries(
                loaded_timeseries,
                "emissions",
                [
                    {
                        "variable": "Emissions|H2|Transportation Sector",
                    }
                ],
                2000,
            )


class TestProxyScaler:
    def test_run(self, inventory):
        scaler = ProxyScaler(
            proxy="australian_inventory|IND",
            source_id="IAMC-MESSAGE-GLOBIOM-ssp245-1-1",
            variable_id="NOx-em-anthro",
            sector="Industrial Sector",
        )

        data = xr.DataArray(
            0,
            coords=dict(lat=inventory.data.lat[:10], lon=inventory.data.lon[:10]),
            dims=("lat", "lon"),
        )

        res = scaler(data=data, inventory=inventory, target_year=2040)

        assert res.shape == data.shape
        assert ur.Unit(res.attrs["units"]) == ur.Unit("kg / yr / cell")


class TestPointSourceScaler:
    def test_run(self, inventory, caplog):
        caplog.set_level(logging.DEBUG)

        scaler = PointSourceScaler.create_from_config(
            PointSourceMethod(
                point_sources="point_sources/hysupply_locations.csv",
                source_timeseries="high_production",
                source_filters=[{"product": "H2"}],
            )
        )
        assert len(scaler.point_sources) == 41

        data = xr.DataArray(
            0,
            coords=dict(lat=inventory.data.lat, lon=inventory.data.lon),
            dims=("lat", "lon"),
        )

        extra_emissions = scmdata.ScmRun(
            os.path.join(
                RAW_DATA_DIR,
                "scenarios/v20230327_1/MESSAGE-GLOBIOM_ssp245_high/high-production-emissions.csv",
            )
        )

        res = scaler(
            data=data,
            inventory=inventory,
            target_year=2040,
            timeseries={"high_production": extra_emissions},
        )

        # Only 10 points present
        assert (res > 0).sum() == 10

        assert res.shape == data.shape
        portion_in_vic = 10 / 41
        exp_value = (
            extra_emissions.filter(year=2040, product="H2").values.squeeze()
            * portion_in_vic
            * 1e9
        )
        npt.assert_allclose(
            res.sum().values,
            exp_value,
            rtol=0.01,
        )
        raise ValueError
