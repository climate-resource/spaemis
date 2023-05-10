# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       jupytext_version: 1.14.4
#   kernelspec:
#     display_name: Python 3 (ipykernel)
# ---

# %%
import os

import xarray as xr

from spaemis.constants import PROCESSED_DATA_DIR

# %%
DATA_DIR = os.path.join(PROCESSED_DATA_DIR, "20230214b")

scenarios = ["ssp119", "ssp126", "ssp245"]


# %%
def _load_scenario(scenario: str) -> xr.Dataset:
    ds = xr.load_dataset(os.path.join(DATA_DIR, scenario, "projections.nc"))
    ds["scenario"] = scenario

    return ds


data = xr.concat([_load_scenario(sce) for sce in scenarios], dim="scenario")
data = data.where(data > 0)
data

# %%
for year in [2020, 2040, 2060]:
    data["NOx"].sel(year=year).sum(dim="sector").plot(
        col="scenario", vmin=0.0001, vmax=1000
    )

# %%
for year in [2020, 2040, 2060]:
    data["CO"].sel(year=year).sum(dim="sector").plot(
        col="scenario", vmin=0.0001, vmax=1000
    )

# %%
