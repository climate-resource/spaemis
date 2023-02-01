import logging
import os
from glob import glob
from typing import Optional, Union

import pandas as pd
import xarray as xr

logger = logging.getLogger(__name__)


class InputEmissionsDatabase:
    """
    Database of Input4MIPs emissions data
    """

    def __init__(self, paths: Union[str, list[str]] = None):
        self.available_data = pd.DataFrame(
            columns=["variable_id", "institute_id" "source_id", "filename"]
        )
        self.paths = []

        if paths:
            if isinstance(paths, str):
                paths = [paths]

            for p in paths:
                self.register_path(p)

    def register_path(self, path: str):
        extra_options = self._find_options(path)

        already_existing = extra_options.filename.isin(self.available_data.filename)
        extra_options = extra_options.loc[~already_existing]
        logger.info(f"Found {len(extra_options)} new entries")

        if len(extra_options):
            self.available_data = pd.concat(
                [self.available_data, extra_options]
            ).sort_values(["variable_id", "institute_id" "source_id"])
            self.paths.append(path)

    def _find_options(self, root_dir) -> pd.DataFrame:
        files = glob(os.path.join(root_dir, "**", "*.nc"), recursive=True)

        def parse_filename(dataset_fname) -> Optional[dict]:
            toks = os.path.basename(dataset_fname).split("_")
            if len(toks) != 7:
                return None

            return {
                "variable_id": toks[0],
                "institute_id": toks[3],
                "source_id": toks[4],
                "filename": dataset_fname,
            }

        file_info = [parse_filename(fname) for fname in files]

        return pd.DataFrame(filter(lambda item: item is not None, file_info))

    def load(self, variable_id, source_id) -> Optional[xr.Dataset]:
        subset = self.available_data

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


database = InputEmissionsDatabase()
