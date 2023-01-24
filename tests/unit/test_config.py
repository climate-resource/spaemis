import pkg_resources

from spaemis.config import DownscalingScenarioConfig, load_config


def test_load_config():
    res = load_config(
        pkg_resources.resource_filename("spaemis", "config/scenarios/ssp245.yaml")
    )

    assert isinstance(res, DownscalingScenarioConfig)
    assert res.inventory_name == "victoria"
    assert res.inventory_year == 2016
