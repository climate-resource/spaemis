# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -pycharm
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.14.4
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%

import logging
import os
import shutil

from spaemis.config import get_default_results_dir, get_path, load_config
from spaemis.constants import RAW_DATA_DIR

logger = logging.getLogger("100_copy_inputs")
logging.basicConfig(level=logging.INFO)

# %% tags=["parameters"]
CONFIG_PATH = os.path.join(RAW_DATA_DIR, "configuration", "scenarios", "ssp119.yaml")
OUTPUT_PATH = get_default_results_dir(CONFIG_PATH)

# %%
config = load_config(CONFIG_PATH)
config

# %%
# Ensures that the output directory exists
output_dir = get_path(OUTPUT_PATH, "inputs")
output_dir

# %%
# Copy input files
# Paths for input data are relative to the raw data directory
for timeseries in config.input_timeseries:
    output_file_path = os.path.join(output_dir, timeseries.path)
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    shutil.copy(
        os.path.join(RAW_DATA_DIR, timeseries.path),
        output_file_path,
    )
