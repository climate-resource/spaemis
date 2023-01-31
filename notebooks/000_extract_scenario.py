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

from typing import Optional

from spaemis.constants import PROCESSED_DATA_DIR
from spaemis.inventory import load_inventory

# %%
INPUT_DATA = os.path.join(PROCESSED_DATA_DIR, "v20221017")

# %%
xr.load_dataset(glob(os.path.join(INPUT_DATA, "**", "*.nc"), recursive=True)[0])

# %%
inventory = load_inventory("victoria", 2016)
inventory

# %%
inventory.border_mask

# %%


class InputDatabase:
    paths:


# %%
def load_existing_data(variable_id) -> Optional[xr.Dataset]:
    exp_dir = os.path.join(
        INPUT4MIPS_PATH,
        "CMIP6",
        "ScenarioMIP",
        "IAMC",
        f"IAMC-*-{config['scenario'].lower()}-1-1",
    )
    found_dirs = glob(exp_dir)
    if len(found_dirs) == 1 and not os.path.exists(found_dirs[0]):
        raise ValueError(
            f"Could not find: {exp_dir}. Download the data from input4MIPs"
        )
    matches = glob(
        os.path.join(
            exp_dir,
            f'**/{variable_id.replace("_", "-")}_*.nc',
        ),
        recursive=True,
    )

    if len(matches) > 1:
        raise ValueError(f"More than one match exists: {matches}")
    if matches:
        return xr.load_dataset(matches[0])

# %%
# !pip install netcdf4

# %%
