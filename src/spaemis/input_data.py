"""
Searching and loading of a local input4MIPs data archive
"""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from glob import glob
from os import PathLike
from typing import Any

import pandas as pd
import scmdata
import xarray as xr

from spaemis.config import InputTimeseries

logger = logging.getLogger(__name__)

# The sector map used for the input4MIPs emissions data
SECTOR_MAP = [
    "Agriculture",
    "Energy Sector",
    "Industrial Sector",
    "Transportation Sector",
    "Residential, Commercial, Other",
    "Solvents production and application",
    "Waste",
    "International Shipping",
    # CO2 also includes this additional sector, but we aren't dealing with that here
    # "Negative CO2 Emissions",
]


class InputEmissionsDatabase:
    """
    Database of Input4MIPs emissions data
    """

    def __init__(self, paths: str | list[str] | None = None):
        self.available_data = pd.DataFrame(
            columns=["variable_id", "institute_id" "source_id", "filename"]
        )
        self.paths: list[str] = []

        if paths:
            if isinstance(paths, str):
                paths = [paths]

            for path in paths:
                self.register_path(path)

    def register_path(self, path: str) -> None:
        """
        Load data from a given path

        Any data present in the given folder will be added to the set of available
        files.

        Parameters
        ----------
        path
            Path that contains input4MIPs data
        """
        extra_options = self._find_options(path)

        if not len(extra_options):
            logger.info(f"Did not find any files in {path}")
            return

        already_existing = extra_options.filename.isin(self.available_data.filename)
        extra_options = extra_options.loc[~already_existing]
        logger.info(f"Found {len(extra_options)} new entries")

        if len(extra_options):
            self.available_data = pd.concat(
                [self.available_data, extra_options]
            ).sort_values(["variable_id", "institute_id" "source_id"])
            self.paths.append(path)

    def _find_options(self, root_dir: str | PathLike[str]) -> pd.DataFrame:
        files = glob(os.path.join(root_dir, "**", "*.nc"), recursive=True)

        def parse_filename(dataset_fname: str) -> dict[str, str] | None:
            toks = os.path.basename(dataset_fname).split("_")
            if len(toks) != 7:  # noqa
                return None

            return {
                "variable_id": toks[0],
                "institute_id": toks[3],
                "source_id": toks[4],
                "filename": dataset_fname,
            }

        file_info = [parse_filename(fname) for fname in files]

        return pd.DataFrame(list(filter(lambda item: item is not None, file_info)))

    @lru_cache(maxsize=15)
    def load(self, variable_id: str, source_id: str) -> xr.Dataset:
        """
        Load the input4MIPs data according to the variable and source name

        Parameters
        ----------
        variable_id
            Variable identifier
        source_id
            Source identifier
        Returns
        -------
            All of the available data for the given variable and source identifiers
        """
        subset = self.available_data

        if not len(self.available_data):
            raise ValueError(
                "No input data has been found. "
                "Set the 'SPAEMIS_INPUT_PATHS' environment variable",
            )

        subset = subset[subset.source_id == source_id]
        subset = subset[subset.variable_id == variable_id]

        if len(subset) == 0:
            raise ValueError(
                f"Could not find any matching data for source_id={source_id} variable_id={variable_id}"
            )

        files_to_load = sorted(subset.filename.values)
        logger.info(f"Loading data from {len(files_to_load)} files: {files_to_load}")

        data = [xr.open_dataset(fname) for fname in files_to_load]
        return xr.concat(data, dim="time").sortby("time")


def initialize_database(options: list[str] | None = None) -> InputEmissionsDatabase:
    """
    Initialise the global database of input emissions

    Uses the `SPAEMIS_INPUT_PATHS` environment to provide a set of paths to search
    for input emissions. This environment can contain a comma-separated list of
    paths if multiple paths are used.

    Returns
    -------
        Emissions database initialised with a list of input directories

    """
    if not options:
        options_from_env: str = os.environ.get("SPAEMIS_INPUT_PATHS")  # type: ignore
        if options_from_env:
            options = [s.strip() for s in options_from_env.split(",")]
        else:
            options = None
    return InputEmissionsDatabase(options)


def _apply_filters(ts: scmdata.ScmRun, filters: list[dict[str, Any]]) -> scmdata.ScmRun:
    for f in filters:
        ts = ts.filter(**f)
    return ts


def load_timeseries(
    options: list[InputTimeseries], root_dir: str | None = None
) -> dict[str, scmdata.ScmRun]:
    """
    Load a set of input timeseries from disk

    Optionally, some additional filtering can be performed on these input timeseries

    Parameters
    ----------
    options
        List of timeseries to load
    root_dir
        Root directory used for relative timeseries file paths

        Defaults to the current directory if no path is provided

    Returns
    -------
        Collection of loaded data

        The keys are determined from the name of each ``InputTimeseries``
    """
    data = {}
    for ts_config in options:
        if ts_config.name in data:
            raise ValueError(f"Duplicate input timeseries found: {ts_config.name}")
        ts = _apply_filters(
            scmdata.ScmRun(os.path.join(root_dir or ".", ts_config.path)),
            ts_config.filters,
        )

        data[ts_config.name] = ts

    return data


database = initialize_database()
