import pytest

from spaemis.config import ConstantScaleMethod, RelativeChangeMethod
from spaemis.scaling import (
    ConstantScaler,
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

        assert res.sector_id == "source"
        assert res.variable_id == "variable"
        assert res.sector_id == 4

    def test_create_missing_sector(self):
        with pytest.raises(ValueError, match="Unknown input4MIPs sector: not-a-sector"):
            RelativeChangeScaler.create_from_config(
                RelativeChangeMethod(
                    source_id="source", variable_id="variable", sector="not-a-sector"
                )
            )
