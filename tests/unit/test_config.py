import os

import pytest

from spaemis.config import (
    ConstantScaleMethod,
    DownscalingScenarioConfig,
    ScalerMethod,
    converter,
    load_config,
)
from spaemis.constants import TEST_DATA_DIR


@pytest.mark.parametrize("fname", ["test-config.yaml", "test-config-with-csv.yaml"])
def test_load_config(fname, config):
    res = load_config(os.path.join(TEST_DATA_DIR, "config", fname))

    assert isinstance(res, DownscalingScenarioConfig)
    assert res.inventory_name == "victoria"
    assert res.inventory_year == 2016
    # TODO: handle extra timeseries
    # Remove the last item temporarily
    if "-with-csv" in fname:
        config.scalers.scalers.pop(-1)

    # Check the scalers and the rest of the config separately as the form of the scalers
    # is different, but the loaded scalers should be the same
    assert res.scalers.get_scalers() == config.scalers.get_scalers()

    res.scalers = None
    config.scalers = None
    assert res == config


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
    with pytest.raises(ValueError, match="Could not determine scaler for unknown"):
        converter.structure({"name": "unknown"}, ScalerMethod)
