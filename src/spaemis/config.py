"""
Description of the configuration
"""

from typing import Any, ClassVar, Literal, Type, Union, get_args

from attrs import define
from cattrs.preconf.pyyaml import make_converter

converter = make_converter()
converter.register_unstructure_hook(str, lambda u: str(u))


@define
class ConstantScaleMethod:
    scale_factor: float = 1.0

    name: ClassVar[Literal["constant"]] = "constant"


@define
class RelativeChangeMethod:
    source_id: str
    variable_id: str
    sector: str

    name: ClassVar[Literal["relative_change"]] = "relative_change"


ScalerMethod = Union[ConstantScaleMethod, RelativeChangeMethod]


def discriminate_scaler(value: Any, _klass: Type) -> ScalerMethod:
    name = value.pop("name")
    for Klass in get_args(_klass):
        if Klass.name == name:
            return converter.structure(value, Klass)
    raise ValueError(f"Could not determine scaler for {name}")


converter.register_structure_hook(ScalerMethod, discriminate_scaler)


@define
class VariableConfig:
    variable: str
    sector: str
    method: ScalerMethod


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
