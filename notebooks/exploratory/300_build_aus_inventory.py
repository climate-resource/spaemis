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

# %% [md]

# # Recreate the Australian input files from raw EDGAR data

# %%

import glob
import os

import pandas as pd
import xarray as xr

from spaemis.constants import RAW_DATA_DIR
from spaemis.inventory import AustraliaGrid

# %%

input_dir = os.path.join(RAW_DATA_DIR, "EDGARv6.1")
output_dir = os.path.join(RAW_DATA_DIR, "inventories", "australia", "2018")

# %%


def parse_fname(fname):
    suffix = ".0.1x0.1.nc"
    toks = os.path.basename(fname[: -len(suffix)]).split("_")
    return {
        "gas": toks[1],
        "sector": "_".join(toks[3:]),
        "year": toks[2],
        "filename": fname,
    }


fnames = sorted(glob.glob(os.path.join(input_dir, "*", "*", "*.0.1x0.1.nc")))
available_data = pd.DataFrame([parse_fname(fname) for fname in fnames])
len(available_data)


# %%

grid = AustraliaGrid()


def extract_aus_subset(data):
    ds_trimmed = (
        xr.load_dataset(data["filename"])
        .sel(lat=grid.lats, lon=grid.lons)
        .assign_coords({"sector": data["sector"]})
    )

    return ds_trimmed


os.makedirs(output_dir, exist_ok=True)

for variable, variable_data in available_data.groupby("gas"):
    ds = xr.concat(
        [extract_aus_subset(row) for _, row in variable_data.iterrows()],
        dim="sector",
    )

    ds = ds.rename({list(ds.data_vars.keys())[0]: variable})

    print(f"Writing {variable} to disk")
    ds.to_netcdf(os.path.join(output_dir, f"{variable}.nc"))
