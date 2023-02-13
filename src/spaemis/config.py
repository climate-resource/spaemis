"""
Description of the configuration
"""
import os.path
from typing import Any, ClassVar, Literal, Optional, Type, Union, get_args

import pandas as pd
from attrs import define, field
from cattrs.preconf.pyyaml import make_converter

from spaemis.utils import chdir

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


def _discriminate_scaler(value: Any, _klass: Type) -> ScalerMethod:
    name = value.pop("name")
    for Klass in get_args(_klass):
        if Klass.name == name:
            return converter.structure(value, Klass)
    raise ValueError(f"Could not determine scaler for {name}")


converter.register_structure_hook(ScalerMethod, _discriminate_scaler)


@define
class VariableScalerConfig:
    variable: str
    sector: str
    method: ScalerMethod


def _convert_filename_to_scalers(filename):
    if not isinstance(filename, str):
        return filename

    # load_config updates the current working directory to match the
    # directory of a loaded config files otherwise a absolute filename is required
    data = pd.read_csv(filename).to_dict(orient="records")

    def extract_scaler_info(data_item):
        sector_info = {}
        for key, value in data_item.copy().items():
            if key.startswith("scaler_"):
                sector_info[key[7:]] = value
                data_item.pop(key)
        return {**data_item, "method": sector_info}

    return [extract_scaler_info(item) for item in data]


@define
class DownscalingScenarioConfig:
    """
    Configuration for downscaling a scenario
    """

    inventory_name: str
    inventory_year: int
    timeslices: list[int]
    scalers: Union[list[VariableScalerConfig], str] = field(
        converter=_convert_filename_to_scalers
    )
    default_scaler: Optional[ScalerMethod] = None


def load_config(config_file: str) -> DownscalingScenarioConfig:
    """
    Load and parse configuration from a file

    Any filenames referenced in the configuration are relative to the configuration file
    not the current directory.

    Parameters
    ----------
    config_file
        File to read

    Returns
    -------
        Validated configuration
    """
    with chdir(os.path.dirname(config_file)):
        with open(config_file) as handle:
            return converter.loads(handle.read(), DownscalingScenarioConfig)
