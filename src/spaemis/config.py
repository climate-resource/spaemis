"""
Description of the configuration
"""

from typing import Union

from attrs import define
from cattrs.preconf.pyyaml import make_converter

converter = make_converter()
converter.register_unstructure_hook(str, lambda u: str(u))


@define
class ConstantMethod:
    name: str = "constant"


@define
class HarmoniseMethod:
    source: str  # TODO add real options
    name: str = "harmonise"


@define
class VariableConfig:
    variable: str
    sector: str
    method: Union[ConstantMethod, HarmoniseMethod]


@define
class DownscalingScenarioConfig:
    """
    Configuration for downscaling a scenario
    """

    inventory_name: str
    inventory_year: int
    timeslices: list[int]
    variables: list[VariableConfig]


def load_config(config_file: str) -> DownscalingScenarioConfig:
    with open(config_file) as fh:
        return converter.loads(fh.read(), DownscalingScenarioConfig)
