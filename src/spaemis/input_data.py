import logging
import os
from glob import glob
from typing import Optional

import pandas as pd
import xarray as xr

logger = logging.getLogger(__name__)


class InputEmissionsDatabase:
    """
    Database of Input4MIPs emissions data
    """

    def __init__(self, paths: list[str]):
        available_data = []

        for p in paths:
            available_data.extend(self._find_options(p))

        self.available_data = pd.DataFrame(available_data)

    def _find_options(self, root_dir) -> list[dict]:
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

        return list(filter(lambda item: item is not None, file_info))

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
