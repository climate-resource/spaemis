# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -pycharm
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.14.5
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Run Projection
#
# From a set of config, generate the projected data set for all of the desired timeslices

# %%
# Load environment variables
# Used to determine where input4MIPs data is stored
import dotenv

dotenv.load_dotenv()

# %%
import logging
import os

import xarray as xr

from spaemis.config import get_default_results_dir, get_path, load_config
from spaemis.constants import OUTPUT_VERSION, RAW_DATA_DIR, TEST_DATA_DIR
from spaemis.input_data import load_timeseries
from spaemis.inventory import clip_region, load_inventory, write_inventory_csvs
from spaemis.project import calculate_point_sources, calculate_projections

logger = logging.getLogger("200_run_projection")
logging.basicConfig(level=logging.INFO)

# %% tags=["parameters"]
CONFIG_PATH = os.path.join(
    RAW_DATA_DIR, "configuration", "scenarios", "ssp119_australia.yaml"
)
RESULTS_PATH = get_default_results_dir(CONFIG_PATH)

# %%
# # Test configuration
# CONFIG_PATH = os.path.join(TEST_DATA_DIR, "config", "test-config.yaml")
# RESULTS_PATH = get_default_results_dir(CONFIG_PATH)

# %%
config = load_config(CONFIG_PATH)
config.timeslices

# %%
# Ensures that the output directory exists
output_dir = get_path(RESULTS_PATH, f"outputs/{config.inventory.name}")
output_dir

# %%
inventory = load_inventory(config.inventory.name, config.inventory.year)
inventory


# %%
def show_variable_sums(df, agg_over=("sector", "lat", "lon")):
    # Results are all in kg/cell/yr so can be summed like this
    totals = df.sum(dim=agg_over).to_dataframe() / 1000 / 1000

    return totals.round(3)  # kt / yr


show_variable_sums(inventory.data, ("lat", "lon"))

# %%
timeseries = load_timeseries(config.input_timeseries, get_path(RESULTS_PATH, "inputs"))
timeseries

# %%
dataset = calculate_projections(config, inventory, timeseries)
dataset


# %%
show_variable_sums(dataset, ("sector", "lat", "lon"))

# %%
point_sources = calculate_point_sources(config, inventory)
point_sources

# %%
if point_sources:
    show_variable_sums(point_sources, agg_over=("lat", "lon"))

# %%
# point_sources["H2"].sel(sector="industry").plot()

# %%
# Align and merge point sources
# dataset has nans outside of the clipped region. PointSources in those areas are ignored.
merged, temp = xr.align(dataset.fillna(0), point_sources, join="outer", fill_value=0)

for variable in temp.data_vars:
    if variable not in merged.data_vars:
        merged[variable] = temp[variable]
    else:
        merged[variable] += temp[variable]

del temp  # Save memory
merged = clip_region(merged, inventory.border_mask)

# %%
show_variable_sums(merged, ("sector", "lat", "lon"))

# %%
dataset["H2"].sum(dim="sector").plot(robust=True, col="year")

# %%
for variable in merged.data_vars:
    merged[variable].plot(robust=True, col="year", row="sector")

# %%
logger.info("Writing output dataset as netcdf")
merged.to_netcdf(
    os.path.join(output_dir, f"{OUTPUT_VERSION}_{config.inventory.name}_projections.nc")
)

# %%
logger.info("Writing CSV files")
for year in config.timeslices:
    target_dir = os.path.join(output_dir, str(year))
    data_to_write = merged.sel(year=year)

    os.makedirs(target_dir, exist_ok=True)

    write_inventory_csvs(data_to_write, target_dir)
