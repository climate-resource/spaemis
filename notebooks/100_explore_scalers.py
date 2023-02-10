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
import logging

import dotenv

dotenv.load_dotenv()
logging.basicConfig(level=logging.INFO)

# %%
import xarray as xr

from spaemis.input_data import SECTOR_MAP, database
from spaemis.inventory import load_inventory
from spaemis.scaling import RelativeChangeScaler

# %%
inventory = load_inventory("victoria", 2016)
inventory

# %%
inventory.data.sector

# %%
# What input4MIPs variables do we have available
# This isn't a complete set of data only what I have on my laptop
database.available_data["variable_id"].unique()

# %%
database.available_data

# %%
# Scale the transport sector as that is likely the most interesting

variable_mapping = [
    ("CO", "NOx-em-anthro"),
    ("NOx", "NOx-em-anthro"),
    ("SO2", "NOx-em-anthro"),
    ("PM10", "NOx-em-anthro"),
    ("VOC", "NOx-em-anthro"),
]

scenario = "CR-MESSAGE-GLOBIOM-ssp245-high"


# %%
# input4MIPs uses integer values to represent sectors
sector_id = SECTOR_MAP.index("Transportation Sector")

# %%
scaler = RelativeChangeScaler(
    variable_id="NOx-em-anthro", source_id=scenario, sector_id=sector_id
)
inv_data = inventory.data["NOx"].sel(sector="motor_vehicles")
inv_data.plot(robust=True)

# %%
# Fetch the data used for scaling
scaler_source = scaler.load_source(inventory)
scaler_source.plot(col="year", col_wrap=3, robust=True)

# %%
data = [
    scaler(inv_data, inventory=inventory, target_year=y)
    for y in [2015, 2020, 2040, 2060, 2080, 2100]
]
scaled_data = xr.concat(data, dim="year")

# %%
scaled_data.plot(robust=True, col="year", col_wrap=3)

# %%
scaled_data.max()

# %%
scaled_data.min()

# %%

for inv_variable, input4mips_variable in variable_mapping:
    scaler = RelativeChangeScaler(
        variable_id=input4mips_variable, source_id=scenario, sector_id=sector_id
    )
    data = inventory.data[inv_variable].sel(sector="motor_vehicles")

    da = scaler(data, inventory=inventory, target_year=2060)

# %%
