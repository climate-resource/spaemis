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

from spaemis.config import get_default_results_dir, get_path, load_config
from spaemis.constants import OUTPUT_VERSION, RAW_DATA_DIR
from spaemis.input_data import load_timeseries
from spaemis.inventory import load_inventory, write_inventory_csvs
from spaemis.project import calculate_projections

logger = logging.getLogger("200_run_victoria")
logging.basicConfig(level=logging.INFO)

# %% tags=["parameters"]
CONFIG_PATH = os.path.join(RAW_DATA_DIR, "configuration", "scenarios", "ssp119.yaml")
RESULTS_PATH = get_default_results_dir(CONFIG_PATH)

# %%
config = load_config(CONFIG_PATH)
config

# %%
# Ensures that the output directory exists
output_dir = get_path(RESULTS_PATH, "outputs/victoria")
output_dir

# %%
inventory = load_inventory("victoria", 2016)
timeseries = load_timeseries(config.input_timeseries, get_path(RESULTS_PATH, "inputs"))

dataset = calculate_projections(config, inventory, timeseries)

# %%
logger.info("Writing output dataset as netcdf")
logger.warning(dataset["CO"].sum())
dataset.to_netcdf(os.path.join(output_dir, f"{OUTPUT_VERSION}_victoria_projections.nc"))

# %%
logger.info("Writing CSV files")
for year in config.timeslices:
    target_dir = os.path.join(output_dir, str(year))
    data_to_write = dataset.sel(year=year)

    os.makedirs(target_dir, exist_ok=True)

    write_inventory_csvs(data_to_write, target_dir)
