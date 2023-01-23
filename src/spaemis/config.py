from typing import Union

from attrs import define
from cattrs.preconf.pyyaml import make_converter

converter = make_converter()
converter.register_unstructure_hook(str, lambda u: str(u))


@define
class ConstantMethod:
    method: str = "constant"


@define
class HarmoniseMethod:
    method: str = "harmonise"


@define
class VariableConfig:
    name: str
    sector: str
    method: Union[ConstantMethod, HarmoniseMethod]


@define
class DownscalingScenarioConfig:
    inventory_name: str
    inventory_year: int
    timeslices: list[int]
    variables: list[VariableConfig]


def load_config(config_file: str) -> DownscalingScenarioConfig:

    return DownscalingScenarioConfig()
