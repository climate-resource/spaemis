"""
Configuration.

The configuration is stored as YAML files and can be loaded and validated using
:func:`load_config`.
"""
import os.path
from typing import Any, ClassVar, Literal, Optional, Union, get_args

import pandas as pd
from attrs import define, field
from cattrs.preconf.pyyaml import make_converter

from spaemis.constants import RUNS_DIR
from spaemis.utils import chdir

converter = make_converter()
converter.register_unstructure_hook(str, lambda u: str(u))


@define
class ExcludeScaleMethod:
    """Configuration for an ExcludeScaler."""

    name: ClassVar[Literal["exclude"]] = "exclude"


@define
class ConstantScaleMethod:
    """Configuration for a ConstantScaler."""

    scale_factor: float = 1.0

    name: ClassVar[Literal["constant"]] = "constant"


@define
class RelativeChangeMethod:
    """Configuration for a RelativeChangeScaler."""

    source_id: str
    variable_id: str
    sector: str

    name: ClassVar[Literal["relative_change"]] = "relative_change"


@define
class ProxyMethod:
    """Configuration for a ProxyScaler."""

    source_id: str
    variable_id: str
    sector: str
    proxy: str

    name: ClassVar[Literal["proxy"]] = "proxy"


@define
class TimeseriesMethod:
    """Configuration for a TimeseriesScaler."""

    proxy: str
    source_timeseries: str
    source_filters: list[dict[str, Any]]
    proxy_region: Optional[str] = None
    name: ClassVar[Literal["timeseries"]] = "timeseries"


@define
class PointSourceMethod:
    """Configuration for a PointSourceScaler."""

    point_sources: str
    source_timeseries: str
    source_filters: list[dict[str, Any]]
    name: ClassVar[Literal["point_source"]] = "point_source"


ScalerMethod = Union[
    ExcludeScaleMethod,
    ProxyMethod,
    RelativeChangeMethod,
    ConstantScaleMethod,
    TimeseriesMethod,
    PointSourceMethod,
]


def _unstructure_scaler(value: ScalerMethod) -> dict[str, Any]:
    res = converter.unstructure(value)
    res["name"] = value.name
    return res


def _discriminate_scaler(value: Any, _klass: type) -> ScalerMethod:
    name = value.pop("name")
    for Klass in get_args(_klass):
        if Klass.name == name:
            return converter.structure(value, Klass)
    raise ValueError(f"Could not determine scaler for {name}")


converter.register_unstructure_hook(ScalerMethod, _unstructure_scaler)
converter.register_structure_hook(ScalerMethod, _discriminate_scaler)


@define
class VariableScalerConfig:
    """
    Represents a mapping between a variable/sector and a scaler.

    In some cases, the target data may not exist in an inventory. In that case the
    scaler should be configured correctly to be able to handle that situation.

    Attributes
    ----------
    variable
        Name of the target variable in the inventory
    sector
        Name of the target sector in the inventory
    allow_missing
        If True, the data may not be present in an inventory
    """

    variable: str
    sector: str
    method: ScalerMethod
    allow_missing: bool = False


def _convert_filename_to_scalers(value: Union[dict, str]) -> list[VariableScalerConfig]:
    if isinstance(value, str):
        if value.endswith(".csv"):
            # load_config updates the current working directory to match the
            # directory of a loaded config files otherwise a absolute filename is required
            data = pd.read_csv(value).to_dict(orient="records")

            def extract_scaler_info(data_item: dict[str, Any]) -> dict[str, Any]:
                sector_info = {}
                for key, value in data_item.copy().items():
                    if key.startswith("scaler_"):
                        sector_info[key[7:]] = value
                        data_item.pop(key)
                return {**data_item, "method": sector_info}

            value = [extract_scaler_info(item) for item in data]
            value = converter.structure(value, list[VariableScalerConfig])
        elif value.endswith(".yaml") or value.endswith(".yml"):
            with open(value) as fh:
                value = converter.loads(fh.read(), list[VariableScalerConfig])
        else:
            raise ValueError(f"Cannot load scalers from {value}")

    return value


@define
class InputTimeseries:
    name: str
    path: str
    filters: list[dict[str, Any]]


@define
class PointSource:
    variable: str
    sector: str
    location: list[tuple[float, float]]  # Lat, lon
    quantity: float  # Total annual emissions spread evenly over sources
    unit: str = "kg"


@define
class PointSourceDefinition:
    sources: list[PointSource] = field(factory=list)
    source_files: Optional[list[str]] = None

    def __attrs_post_init__(self) -> None:
        def read_point_source(fname: str) -> list[PointSource]:
            with open(fname) as handle:
                return converter.loads(handle.read(), list[PointSource])

        if self.source_files:
            for fname in self.source_files:
                self.sources.extend(read_point_source(fname))
        self.source_files = None

        # TODO: Check and warn if duplicates exist


@define
class ScalerDefinition:
    default_scaler: ScalerMethod = ExcludeScaleMethod()
    scalers: list[VariableScalerConfig] = field(factory=list)
    source_files: Optional[list[str]] = None

    def __attrs_post_init__(self) -> None:
        if self.source_files:
            for fname in self.source_files:
                self.scalers.extend(_convert_filename_to_scalers(fname))
        self.source_files = None

        # TODO: Check and warn if duplicates exist


@define
class Inventory:
    """Define the inventory used for this scenario."""

    name: str
    year: int


@define
class DownscalingScenarioConfig:
    """Configuration for downscaling a scenario."""

    name: str
    inventory: Inventory
    timeslices: list[int]
    scalers: ScalerDefinition
    input_timeseries: Optional[list[InputTimeseries]] = None
    point_sources: Optional[PointSourceDefinition] = None


def load_config(config_file: str) -> DownscalingScenarioConfig:
    """
    Load and parse configuration from a file.

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
    with open(config_file) as handle:
        with chdir(os.path.dirname(config_file)):
            return converter.loads(handle.read(), DownscalingScenarioConfig)


def get_path(output_dir: str, rel_path: str | None = None) -> str:
    data_dir = output_dir

    if rel_path:
        data_dir = os.path.join(data_dir, rel_path)

    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_default_results_dir(config_path: str) -> str:
    """
    Get the default output path for a given configuration file.

    Defaults to ``data/runs/{OUTPUT_VERSION}/{CONFIG_FILE_NAME}``. This function
    does not create that directory if it doesn't already exist.

    Parameters
    ----------
    config_path

    Raises
    ------
    FileNotFoundError
        If config_path doesn't exist

    Returns
    -------
    Output directory for results
    """
    if not os.path.exists(config_path):
        FileNotFoundError(config_path)

    config_file_name = os.path.splitext(os.path.basename(config_path))[0]
    return os.path.join(RUNS_DIR, config_file_name)
