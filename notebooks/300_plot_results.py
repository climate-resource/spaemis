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
# # Plot results
#
# Generate figures

# %%
# Load environment variables
# Used to determine where input4MIPs data is stored
import dotenv

dotenv.load_dotenv()

# %%
import logging

import matplotlib.pyplot as plt
import scmdata
import seaborn as sns

from spaemis.input_data import SECTOR_MAP, database

logger = logging.getLogger("200_run_projection")
logging.basicConfig(level=logging.INFO)

# %%
ds = database.load("NOx-em-anthro", "CR-IMAGE-ssp119-med")

# %%
ds.sel(sector=1, time="2050").mean(dim="time")["NOx_em_anthro"] / ds.sel(
    sector=1, time="2015"
).mean(dim="time")["NOx_em_anthro"]

# %%
slice_1 = ds.sel(sector=1, time="2050").mean(dim="time")["NOx_em_anthro"]
slice_1 = slice_1.where(slice_1 > 0)
slice_2 = ds.sel(sector=1, time="2015").mean(dim="time")["NOx_em_anthro"]
slice_2 = slice_2.where(slice_1 > 0)

gr = slice_1 / slice_2
gr.name = "Growth Rate (dimensionless)"

# %%
fig, axs = plt.subplots(1, 3, figsize=(20, 6), sharey=True)

slice_1.plot(ax=axs[0], vmin=0, vmax=5e-11, add_colorbar=False)
axs[0].set_title("2015")
slice_2.name = "NOx Emissions (kg NOx m-2 s-1)"
slice_2.plot(ax=axs[1], vmin=0, vmax=5e-11)
axs[1].set_title("2050")
axs[1].set_ylabel("")
gr.plot(ax=axs[2], vmin=0.2, vmax=3)
axs[2].set_title("Growth Rate")
axs[2].set_ylabel("")

plt.tight_layout()

plt.savefig("growth_rate.png")


# %% [markdown]
# # Compare growth rates


# %%
def calc_growth_rate(scenario, variable, ds) -> scmdata.ScmRun:
    point = (-37, 145)
    source = (
        ds.sel(lat=point[0], lon=point[1], method="nearest")[variable.replace("-", "_")]
        .groupby("time.year")
        .mean()
    )
    growth_rate = source / source.interp(year=2016)

    return scmdata.ScmRun(
        growth_rate.values,
        columns={
            "variable": f"Growth Rate|{variable}",
            "unit": "dimensionless",
            "region": "AUS",
            "model": "",
            "scenario": scenario,
            "sector": SECTOR_MAP,
        },
        index=growth_rate["year"],
    )


# %%
res = []
for variable in ["CO-em-anthro", "SO2-em-anthro", "BC-em-anthro", "VOC-em-anthro"]:
    for scenario in [
        "IAMC-IMAGE-ssp119-1-1",
        "IAMC-IMAGE-ssp126-1-1",
        "IAMC-MESSAGE-GLOBIOM-ssp245-1-1",
    ]:
        ds = database.load(variable, scenario)

        res.append(calc_growth_rate(scenario, variable, ds))

for scenario in [
    "CR-IMAGE-ssp119-med",
    "CR-REMIND-MAGPIE-ssp226-med",
    "CR-MESSAGE-GLOBIOM-ssp245-med",
]:
    ds = database.load("NOx-em-anthro", scenario)

    res.append(calc_growth_rate(scenario, "NOx-em-anthro", ds))
growth_rates = scmdata.run_append(res)
growth_rates

# %%
variables = sorted(growth_rates.get_unique_meta("variable"))

palette = {sector: sns.color_palette()[i] for i, sector in enumerate(SECTOR_MAP)}

fig, axs = plt.subplots(len(variables), figsize=(12, 20), sharex=True)

for i, variable in enumerate(variables):
    growth_rates.filter(variable=variable).lineplot(
        ax=axs[i], hue="sector", style="scenario", time_axis="year", palette=palette
    )
    axs[i].set_title(variable)

plt.tight_layout()
axs[-1].set_xlim(2016, 2100)
plt.savefig("growth_rates_by_variable.png")

# %%
