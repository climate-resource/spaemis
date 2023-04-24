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

# %%
import dotenv

dotenv.load_dotenv()

# %%
import os

import matplotlib.pyplot as plt
import pandas as pd
import rioxarray  # noqa
import seaborn as sns
import xarray as xr

from spaemis.constants import RAW_DATA_DIR
from spaemis.input_data import database
from spaemis.inventory import clip_region, load_inventory
from spaemis.utils import area_grid

vic_inventory = load_inventory("victoria", 2016)

# %%
# as expected ~1kmx1km
areas = area_grid(vic_inventory.data.lat, vic_inventory.data.lon)
areas

# %%

cm = sns.light_palette("red", as_cmap=True)


# %%
for v in vic_inventory.data.data_vars:
    da = vic_inventory.data[v]

    da.plot(col="sector", col_wrap=6, robust=True, vmin=0)


flattened_data = vic_inventory.data.sum() / 1e6

# %%
compare_data = [
    ["CO", "inventory", float(flattened_data["CO"].values.squeeze())],
    ["NOx", "inventory", float(flattened_data["NOx"].values.squeeze())],
    ["SO2", "inventory", float(flattened_data["SO2"].values.squeeze())],
    ["PM10", "inventory", float(flattened_data["PM10"].values.squeeze())],
    ["VOC", "inventory", float(flattened_data["VOC"].values.squeeze())],
]
compare_data


# %%
def process_edgar(variable, year):
    nox_fname = os.path.join(
        RAW_DATA_DIR,
        "EDGARv6.1",
        variable,
        f"TOTALS/EDGARv6.1_{variable}_{year}_TOTALS.0.1x0.1.nc",
    )
    edgar_ds = xr.load_dataset(nox_fname, decode_coords="all").rio.write_crs("WGS84")
    cropped_edgar = clip_region(edgar_ds, vic_inventory.border_mask)[
        f"emi_{variable.lower()}"
    ]

    cropped_edgar.plot(robust=True)
    return (
        (cropped_edgar * area_grid(cropped_edgar.lat, cropped_edgar.lon)).sum()
        * (365 * 24 * 60 * 60)
        / (1000 * 1000)
    )  # kt/yr


# %%
for v in ["NOx", "SO2", "CO", "PM10", "NMVOC"]:
    plt.figure()
    compare_data.append([v, "EDGAR", float(process_edgar(v, 2016).values.squeeze())])


# %% [markdown]
# # CEDS

# %%


def process_ceds(variable):
    ds = database.load(variable + "-em-anthro", "IAMC-IMAGE-ssp126-1-1")

    ceds_nox = (
        ds[variable + "_em_anthro"]
        .sel(time="2015")
        .mean(dim="time", keep_attrs=True)
        .rio.write_crs("WGS84")
    )
    ceds_nox = clip_region(ceds_nox, vic_inventory.border_mask)
    ceds_nox

    return (
        ceds_nox.mean()
        * area_grid(ceds_nox.lat, ceds_nox.lon).sum()
        * ((365 * 24 * 60 * 60) / 1e6)
    )


# %%

for v in ["NOx", "SO2", "CO", "VOC"]:
    plt.figure()
    compare_data.append([v, "CEDS", float(process_ceds(v).values.squeeze())])


# %%
pd.DataFrame(compare_data, columns=["species", "source", "value [kt / yr]"]).set_index(
    ["species", "source"]
).unstack("source").round(1)

# %%
