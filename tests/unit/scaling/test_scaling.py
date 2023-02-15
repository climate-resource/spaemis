import pytest
import xarray as xr

from spaemis.config import ConstantScaleMethod, ProxyMethod, RelativeChangeMethod
from spaemis.scaling import (
    ConstantScaler,
    ProxyScaler,
    RelativeChangeScaler,
    get_scaler,
    get_scaler_by_config,
)


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
        assert res.sector_id == 2

    def test_create_missing_sector(self):
        with pytest.raises(ValueError, match="Unknown input4MIPs sector: not-a-sector"):
            RelativeChangeScaler.create_from_config(
                RelativeChangeMethod(
                    source_id="source", variable_id="variable", sector="not-a-sector"
                )
            )


class TestProxyScaler:
    def test_create(self):
        res = ProxyScaler.create_from_config(
            ProxyMethod(
                proxy="Population",
                source_timeseries="inputs",
                source_filters={"variable": "H2"},
            )
        )

        assert res.proxy == "source"
        assert res.source_timeseries == "variable"
        assert res.source_filters == {"variable": "H2"}

    def test_run(self, inventory):
        scaler = ProxyScaler(
            proxy="Population",
            source_timeseries="inputs",
            source_filters={"variable": "H2"},
        )

        data = xr.DataArray(0, coords=dict(lat=range()))

        res = scaler(data=data, inventory=inventory, target_year=2020, timeseries={})
