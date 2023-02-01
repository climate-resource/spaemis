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
import os
from glob import glob

import xarray as xr

from spaemis.constants import TEST_DATA_DIR
from spaemis.input_data import InputEmissionsDatabase
from spaemis.inventory import load_inventory
from spaemis.utils import clip_region, weighted_annual_mean

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
inp_data = input_emissions.load(
    variable_id="OC-em-anthro", source_id="IAMC-MESSAGE-GLOBIOM-ssp245-1-1"
)
inp_data


# %%


annual_mean = weighted_annual_mean(inp_data, "OC_em_anthro")
annual_mean

# %%
clipped = clip_region(annual_mean, inventory.border_mask)
clipped

# %%
clipped.sel(time="2015", sector=0).plot()

# %%
