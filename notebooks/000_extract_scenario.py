# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -pycharm
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.14.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
import scmdata
import os
from glob import glob
import xarray as xr
import numpy as np
from typing import Optional

from spaemis.constants import TEST_DATA_DIR
from spaemis.inventory import load_inventory
from spaemis.input_data import InputEmissionsDatabase

from spaemis.utils import clip_region

# %%
INPUT_DATA = os.path.join(TEST_DATA_DIR, "input4MIPs")

# %%
xr.load_dataset(glob(os.path.join(INPUT_DATA, "**", "*.nc"), recursive=True)[0])

# %%
inventory = load_inventory("victoria", 2016)
inventory

# %%
input_emissions = InputEmissionsDatabase([INPUT_DATA])
input_emissions.available_data

# %%
inp_data = input_emissions.load(variable_id="OC-em-anthro", source_id="IAMC-MESSAGE-GLOBIOM-ssp245-1-1")
inp_data


# %%
def weighted_temporal_mean(ds, var):
    """
    weight by days in each month
    """
    # Determine the month length
    month_length = ds.time.dt.days_in_month
    wgts = month_length.groupby("time.year") / month_length.groupby("time.year").sum()

    # Make sure the weights in each year add up to 1
    np.testing.assert_allclose(wgts.groupby("time.year").sum(xr.ALL_DIMS), 1.0)

    # Subset our dataset for our variable
    obs = ds[var]

    # Setup our masking for nan values
    cond = obs.isnull()
    ones = xr.where(cond, 0.0, 1.0)

    # Calculate the numerator
    obs_sum = (obs * wgts).resample(time="AS").sum(dim="time")

    # Calculate the denominator
    ones_out = (ones * wgts).resample(time="AS").sum(dim="time")

    # Return the weighted average
    return obs_sum / ones_out

annual_mean = weighted_temporal_mean(inp_data, "OC_em_anthro")
annual_mean

# %%
clipped = clip_region(annual_mean, inventory.border_mask)
clipped

# %%
clipped.sel(time="2015", sector=0).plot()

# %%
