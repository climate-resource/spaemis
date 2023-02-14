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

# %% [markdown]
# # Scalers
#
# A Scaler is used to project inventory data into the future.
#
# These scalers can be configured to use information from different sources to perform the projections.

# %%
import logging

import dotenv

dotenv.load_dotenv()
logging.basicConfig(level=logging.INFO)

# %%
import xarray as xr

from spaemis.commands.project_command import scale_inventory
from spaemis.config import RelativeChangeMethod, VariableScalerConfig
from spaemis.input_data import SECTOR_MAP, database
from spaemis.inventory import load_inventory
from spaemis.scaling import RelativeChangeScaler

# %%
inventory = load_inventory("victoria", 2016)
inventory

# %%
inventory.data.sector

# %%
inventory.data["CO"].plot(col="sector", col_wrap=3)

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

scenario = "IAMC-MESSAGE-GLOBIOM-ssp245-1-1"

scaler_config = VariableScalerConfig(
    variable="NOx",
    sector="motor_vehicles",
    method=RelativeChangeMethod(
        variable_id="NOx-em-anthro", source_id=scenario, sector="Transportation Sector"
    ),
)


# %%
inv_data = inventory.data[scaler_config.variable].sel(sector=scaler_config.sector)
inv_data.plot(robust=True)

# %%

# %%
# Fetch the data used for scaling
scaler = RelativeChangeScaler.create_from_config(scaler_config.method)

scaler_source = scaler.load_source(inventory)
scaler_source.plot(col="year", col_wrap=3, robust=True)


# %%
data = [
    scale_inventory(scaler_config, inventory=inventory, target_year=y)
    for y in [2015, 2020, 2040, 2060, 2080, 2100]
]
scaled_data = xr.concat(data, dim="year")
scaled_data

# %%
scaled_data[scaler_config.variable].plot(robust=True, col="year", col_wrap=3)

# %%
# Scale factors
scale_factor = (
    scaled_data[scaler_config.variable] / inventory.data[scaler_config.variable]
).sel(sector=scaler_config.sector)

scale_factor.plot(robust=True, col="year", col_wrap=3)

# %%
