import pkg_resources
import pytest

from spaemis.config import (
    ConstantScaleMethod,
    DownscalingScenarioConfig,
    ScalerMethod,
    converter,
    load_config,
)


def test_load_config():
    res = load_config(
        pkg_resources.resource_filename("spaemis", "config/scenarios/ssp245.yaml")
    )

    assert isinstance(res, DownscalingScenarioConfig)
    assert res.inventory_name == "victoria"
    assert res.inventory_year == 2016


def test_structuring_constant():
    res = converter.structure({"name": "constant"}, ScalerMethod)
    assert isinstance(res, ConstantScaleMethod)
    assert res.name == "constant"
    assert res.scale_factor == 1

    res = converter.structure(
        {"name": "constant", "scale_factor": 12.3, "extra": "not-included"},
        ScalerMethod,
    )
    assert isinstance(res, ConstantScaleMethod)
    assert res.name == "constant"
    assert res.scale_factor == 12.3
    assert not hasattr(res, "extra")


def test_structuring_invalid():
    with pytest.raises(ValueError):
        converter.structure({"name": "unknown"}, ScalerMethod)
