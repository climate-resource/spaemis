# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       jupytext_version: 1.14.4
#   kernelspec:
#     display_name: Python 3 (ipykernel)
# ---

# %% [markdown]
# # Proxies
#
# For some species (e.g. H2) we use proxies to supply the spatial pattern of emissions.
# The quantity comes from other studies such as `h2-adjust`.

# %%

import geopandas
import matplotlib.pyplot as plt

from spaemis.inventory import load_inventory
from spaemis.scaling.proxy import get_proxy
from spaemis.utils import clip_region

# %%
inventory = load_inventory("victoria", 2016)

# %%
inventory.data

# %%
inventory.data.sel(sector="motor_vehicles")["NOx"].plot()

# %%
proxy = get_proxy("population")
proxy

# %%
proxy.plot(robust=True)

# %%
df = geopandas.read_file("~/Downloads/aus_border/geoBoundaries-AUS-ADM1.shp").to_crs(
    "EPSG:4326"
)

# %%
vic_boundary = df[df.shapeName == "Victoria"]

# %%
vic_boundary.plot()

# %%
ax = plt.gca()
vic_boundary.plot(ax=ax)
clip_region(proxy, vic_boundary).plot()


# %%
