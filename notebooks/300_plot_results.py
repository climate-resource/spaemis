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
# # Run Projection
#
# From a set of config, generate the projected data set for all of the desired timeslices

# %%
# Load environment variables
# Used to determine where input4MIPs data is stored
import dotenv

dotenv.load_dotenv()

# %%
import logging
import os

import matplotlib.pyplot as plt
import pandas as pd
import scmdata
import seaborn as sns
import xarray as xr

from spaemis.constants import OUTPUT_VERSION, RUNS_DIR
from spaemis.input_data import SECTOR_MAP, database
from spaemis.inventory import clip_region, load_inventory
from spaemis.scaling.proxy import get_proxy
from spaemis.utils import area_grid

logger = logging.getLogger("200_run_projection")
logging.basicConfig(level=logging.INFO)

# %%
out_dir = os.path.join(RUNS_DIR, "plots")
os.makedirs(out_dir, exist_ok=True)

# %%
ds = database.load("NOx-em-anthro", "CR-IMAGE-ssp119-low")

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

plt.savefig(os.path.join(out_dir, "country_growth_rate.png"))


# %% [markdown]
# # Compare growth rates


# %%
def calc_growth_rate(variable, scenario, ds) -> scmdata.ScmRun:
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

        res.append(calc_growth_rate(variable, scenario, ds))


for scenario in [
    "CR-IMAGE-ssp119-low",
    "CR-REMIND-MAGPIE-ssp226-med",
    "CR-MESSAGE-GLOBIOM-ssp245-high",
]:
    ds = database.load("NOx-em-anthro", scenario)

    res.append(calc_growth_rate("NOx-em-anthro", scenario, ds))

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
plt.savefig(os.path.join(out_dir, "growth_rates_by_variable.png"))

# %%
sectors = sorted(growth_rates.get_unique_meta("sector"))

palette = {variable: sns.color_palette()[i] for i, variable in enumerate(variables)}

fig, axs = plt.subplots(len(sectors), figsize=(12, 30), sharex=True)

for i, sector in enumerate(sectors):
    growth_rates.filter(sector=sector).lineplot(
        ax=axs[i], hue="variable", style="scenario", time_axis="year", palette=palette
    )
    axs[i].set_title(sector)
    legend = axs[i].get_legend()
    if legend:
        plt.setp(legend.get_title(), fontsize="8")
        plt.setp(legend.get_texts(), fontsize="8")

plt.tight_layout()
axs[-1].set_xlim(2016, 2100)

plt.savefig(os.path.join(out_dir, "growth_rates_by_sector.png"))

# %%

sectors = sorted(growth_rates.get_unique_meta("sector"))


for variable in growth_rates.get_unique_meta("variable"):
    fig, axs = plt.subplots(len(sectors), figsize=(12, 20), sharex=True)

    for i, sector in enumerate(sectors):
        growth_rates.filter(sector=sector, variable=variable).lineplot(
            ax=axs[i], hue="scenario", time_axis="year", lw=2
        )
        axs[i].set_title(sector, fontsize="14")

    plt.tight_layout()
    axs[-1].set_xlim(2016, 2100)

    plt.savefig(os.path.join(out_dir, f"growth_rates_by_sector_by_gas_{variable}.png"))

# %%

# %% [markdown]
# # H2 rates

# %%
res = []
for scenario in [
    "CR-IMAGE-ssp119-low",
    "CR-REMIND-MAGPIE-ssp226-med",
    "CR-MESSAGE-GLOBIOM-ssp245-high",
]:
    ds = database.load("H2-em-anthro", scenario)

    res.append(calc_growth_rate("H2-em-anthro", scenario, ds))
h2_growth_rates = scmdata.run_append(res)

palette = {sector: sns.color_palette()[i] for i, sector in enumerate(SECTOR_MAP)}
fig, axs = plt.subplots(len(SECTOR_MAP), figsize=(12, 20))

for i, sector in enumerate(SECTOR_MAP):
    h2_growth_rates.filter(sector=sector).lineplot(
        hue="scenario", time_axis="year", ax=axs[i]
    )
    axs[i].set_title(sector, fontsize=14)

plt.gca().set_xlim(2016, 2100)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "growth_rates_H2.png"))

# %%
all_rates = scmdata.run_append([growth_rates, h2_growth_rates])
all_rates.timeseries(time_axis="year").to_csv(os.path.join(out_dir, "growth_rates.csv"))

# %% [markdown]
# # Spatial patterns

# %%
aus_inv = load_inventory("australia", 2016)
vic_inv = load_inventory("victoria", 2016)


# %%
def from_cell_totals(da):
    areas = area_grid(da.lat, da.lon)

    return da / areas / (365 * 24 * 60 * 60)


# %%
sectors_aus = {
    "Agriculture": ["AGS", "AWB", "FOO_PAP", "MNM"],
    "Energy Sector": ["ENE", "FFF", "REF_TRF"],
    "Industrial Sector": ["IND", "IRO", "NFE", "NMM"],
    "Residential, Commercial, Other": ["RCO"],
    "Solvents production and application": ["CHE", "PRU_SOL"],
    "Transportation Sector": ["TNR_Other", "TRO_RES", "TRO_noRES"],
    "Waste": ["SWD_INC", "SWD_LDF", "WWT"],
    "International Shipping": ["TNR_Ship"],
}
sectors_vic = {
    "Agriculture": [],
    "Energy Sector": ["gas_leak"],
    "Industrial Sector": ["industry"],
    "Residential, Commercial, Other": [
        "architect_coating",
        "bakery",
        "crematoria",
        "dry_cleaning",
        "panel_beaters",
        "petcrematoria",
        "pizza",
        "printing",
        "servos",
        "vicbakery",
        "woodheater",
    ],
    "Solvents production and application": ["domestic_solvents"],
    "Transportation Sector": ["rail", "motor_vehicles", "cutback_bitumen"],
    "Waste": ["industry_diffuse"],
    "International Shipping": ["shipping"],
}

# %%
inverse_sectors_aus = {}
inverse_sectors_vic = {}

for sector in sectors_aus:
    for k in sectors_aus[sector]:
        inverse_sectors_aus[k] = sector

for sector in sectors_vic:
    for k in sectors_vic[sector]:
        inverse_sectors_vic[k] = sector

# %%
aus_inv.data = aus_inv.data.rename({"NMVOC": "VOC"})


# %%
def aggregate_inventory(inventory, sectors):
    coords = (
        xr.IndexVariable(data=list(sectors.keys()), dims="sector"),
        inventory.data.lat,
        inventory.data.lon,
    )

    data = xr.Dataset()

    for variable in inventory.data.data_vars:
        data[variable] = xr.DataArray(coords=coords)

        for sector_name, aggregates in sectors.items():
            data[variable].loc[sector_name] = (
                inventory.data[variable].sel(sector=aggregates).sum(dim="sector")
            )
    return data


vic_data = aggregate_inventory(vic_inv, sectors_vic)
aus_data = aggregate_inventory(aus_inv, sectors_aus)


# %%
for variable in vic_data.data_vars:
    fig, axs = plt.subplots(
        len(sectors_aus), 2, figsize=(15, 50), sharex=True, sharey=True, dpi=300
    )

    edgar_to_plot = from_cell_totals(
        clip_region(aus_data[variable], vic_inv.border_mask)
    )
    vic_to_plot = from_cell_totals(clip_region(vic_data[variable], vic_inv.border_mask))

    vmin = 0
    vmax = 5e-5

    for i, sector in enumerate(sectors_aus.keys()):
        edgar_to_plot.sel(sector=sector).plot(ax=axs[i, 0], robust=True)
        vic_to_plot.sel(sector=sector).plot(ax=axs[i, 1], robust=True, vmin=0)

    plt.savefig(os.path.join(out_dir, f"victoria_CEDS-mapping_{variable}.png"))
    plt.close()


# %% [markdown]
#
# # Load results


# %%
def load_result(scenario: str, grid: str) -> xr.Dataset:
    fname = os.path.join(
        RUNS_DIR,
        f"{scenario}_{grid}",
        "outputs",
        grid,
        f"{OUTPUT_VERSION}_{grid}_projections.nc",
    )
    ds = xr.load_dataset(fname)

    ds = from_cell_totals(clip_region(ds, vic_inv.border_mask))

    return ds.assign_coords(scenario=[scenario])


scenarios = ["ssp119", "ssp226", "ssp245"]
vic_results = xr.concat(
    [load_result(scenario, "victoria") for scenario in scenarios],
    dim="scenario",
)


# %%
aus_results = xr.concat(
    [load_result(scenario, "australia") for scenario in scenarios],
    dim="scenario",
).rename({"NMVOC": "VOC"})
aus_results = aus_results.reindex(lat=aus_results.lat[::-1])

# %%
sum_emms = aus_results.sum(dim=("lat", "lon", "year", "scenario"))["NOx"].to_dataframe()
sum_emms = sum_emms.squeeze().sort_values()
sum_emms = sum_emms[sum_emms > 0]
sum_emms.index.tolist()[::-1]

# %%
sectors

# %%
for variable in aus_results.data_vars:
    vals = clip_region(aus_results[variable].sum(dim="sector"), vic_inv.border_mask)

    ax = vals.plot(col="year", row="scenario", cmap="rocket", robust=True)
    ax.fig.suptitle(variable + " - AUS")

    os.makedirs(os.path.join(out_dir, "australia", "by_species"), exist_ok=True)
    plt.savefig(
        os.path.join(
            out_dir, "australia", "by_species", f"{variable}-total-australia.png"
        )
    )

# %%
for variable in vic_results.data_vars:
    vals = clip_region(vic_results[variable].sum(dim="sector"), vic_inv.border_mask)

    ax = vals.plot(col="year", row="scenario", cmap="rocket", robust=True, vmin=0)
    ax.fig.suptitle(variable + " - VIC")

    os.makedirs(os.path.join(out_dir, "victoria", "by_species"), exist_ok=True)
    plt.savefig(
        os.path.join(
            out_dir, "victoria", "by_species", f"{variable}-total-victoria.png"
        )
    )


# %% [markdown]
# # By species/sector

# %%
for variable in aus_results.data_vars:
    sum_emms = aus_results.sum(dim=("lat", "lon", "year", "scenario"))[
        variable
    ].to_dataframe()
    sum_emms = sum_emms.squeeze().sort_values()
    sum_emms = sum_emms[sum_emms > 0]
    sectors = sum_emms.index.tolist()[::-1]

    for sector in sectors:
        fig, axs = plt.subplots(1, figsize=(12, 2))
        vals = aus_results.sel(sector=sector)[variable]

        vmax = vals.max()
        vmin = vals.min()
        d = vmax - vmin
        vmax = vmax - d * 0.1
        vmin = vmin + d * 0.1
        ax = aus_results.sel(sector=sector)[variable].plot(
            col="year", row="scenario", cmap="rocket", vmax=vmax, vmin=vmin
        )
        fig.suptitle(f"{variable} - {sector}")

        all_rates.filter(
            variable=f"*|{variable}-*", sector=inverse_sectors_aus[sector]
        ).lineplot(ax=axs)
        os.makedirs(
            os.path.join(out_dir, "australia", "by_species_sector"), exist_ok=True
        )
        ax.fig.savefig(
            os.path.join(
                out_dir,
                "australia",
                "by_species_sector",
                f"{variable}-{sector}-australia.png",
            )
        )


# %%
float(vals.where(vals > 0).quantile(0.9).values.squeeze())


# %%
for variable in aus_results.data_vars:
    sum_emms = vic_results.sum(dim=("lat", "lon", "year", "scenario"))[
        variable
    ].to_dataframe()
    sum_emms = sum_emms.squeeze().sort_values()
    sum_emms = sum_emms[sum_emms > 0]
    sectors = sum_emms.index.tolist()[::-1]

    for sector in sectors:
        fig, axs = plt.subplots(1, figsize=(12, 2))
        vals = vic_results.sel(sector=sector)[variable]

        vmax = vals.max()
        vmin = vals.min()
        vmax = float(vals.where(vals > 0).quantile(0.9).values.squeeze())
        ax = vals.plot(col="year", row="scenario", cmap="rocket", vmax=vmax, vmin=0)
        ax = fig.suptitle(sector)

        try:
            all_rates.filter(
                variable=f"*|{variable}-*", sector=inverse_sectors_vic[sector]
            ).lineplot(ax=axs)
        except KeyError:
            pass
        fig.suptitle(sector)

        os.makedirs(
            os.path.join(out_dir, "victoria", "by_species_sector"), exist_ok=True
        )
        fig.savefig(
            os.path.join(
                out_dir,
                "victoria",
                "by_species_sector",
                f"{variable}-{sector}-victoria.png",
            )
        )

# %%
import warnings

warnings.simplefilter("ignore")

# %% [markdown]
# # Points

# %%
# Points to compare
melbourne = (-37.6, 145)
la_trobe = (-38.268, 146.4)

# %%
# %matplotlib widget
aus_results["NOx"].sel(scenario="ssp245", sector="IND", year=2020).plot(
    vmin=0, vmax=1e3
)


# %%
def extract_point(results, point, location, threshold=0.2):
    df = (
        results.sel(lat=slice(point[0] - threshold, point[0] + threshold))
        .sel(lon=slice(point[1] - threshold, point[1] + threshold))
        .mean(dim=("lat", "lon"))
        .to_dataframe()[results.data_vars]
    )
    df.columns.name = "variable"

    df = df.unstack("year").stack("variable").reset_index()
    df["region"] = location
    df["variable"] = "Emissions|" + df["variable"]
    df["unit"] = "kg m-2 s-1"
    df["model"] = ""

    return scmdata.ScmRun(df)


melbourne_vic = extract_point(vic_results, melbourne, "Melbourne")
melbourne_vic["grid"] = "victoria"
melbourne_aus = extract_point(aus_results, melbourne, "Melbourne")
melbourne_aus["grid"] = "australia"

latrobe_vic = extract_point(vic_results, la_trobe, "La Trobe")
latrobe_vic["grid"] = "victoria"
latrobe_aus = extract_point(aus_results, la_trobe, "La Trobe")
latrobe_aus["grid"] = "australia"

point_timeseries = scmdata.run_append(
    [melbourne_aus, melbourne_vic, latrobe_aus, latrobe_vic]
)
point_timeseries

# %%
point_timeseries.meta[["grid", "scenario"]].drop_duplicates()


# %%
def get_largest(run, n):
    values = run.timeseries().squeeze().sort_values()[-n:]

    return values.index.get_level_values("sector").to_list()


get_largest(
    latrobe_vic.filter(
        scenario="ssp119", region="La Trobe", variable="Emissions|CO", year=2020
    ),
    5,
)

# %%
# two points (Melbourne CBD and La Trobe) line plots by gas by 'input' sector
for grid in ["victoria", "australia"]:
    for by_variable in point_timeseries.filter(grid=grid).groupby("variable"):
        n_sectors = 5
        sectors = get_largest(
            by_variable.filter(scenario="ssp119", region="Melbourne", year=2020),
            n_sectors,
        )[::-1]

        fig, axs = plt.subplots(n_sectors + 1, figsize=(12, 18))
        fig.suptitle(by_variable.get_unique_meta("variable", True))

        for i, sector in enumerate(sectors):
            by_sector = by_variable.filter(sector=sector)
            by_sector.lineplot(hue="scenario", style="region", ax=axs[i + 1])
            axs[i + 1].set_title(by_sector.get_unique_meta("sector", True))

        by_variable.process_over("sector", "sum", as_run=True).lineplot(
            hue="scenario", style="region", ax=axs[0]
        )
        axs[0].set_title("Total")
        fig.tight_layout()

        variable = by_variable.get_unique_meta("variable", True)
        os.makedirs(
            os.path.join(out_dir, grid, "points_by_input_sector"), exist_ok=True
        )
        plt.savefig(
            os.path.join(
                out_dir,
                grid,
                "points_by_input_sector",
                f"{variable}-{grid}.png",
            )
        )

# %%
# two points (Melbourne CBD and La Trobe) line plots by gas by 'CEDs' sector

# Create CEDs sectors
point_timeseries_ceds = []
for sector in sectors_vic:
    point_timeseries_ceds.append(
        point_timeseries.filter(
            grid="victoria", sector=sectors_vic[sector], log_if_empty=False
        ).process_over("sector", "sum", op_cols={"sector": sector}, as_run=True)
    )
for sector in sectors_aus:
    point_timeseries_ceds.append(
        point_timeseries.filter(
            grid="australia", sector=sectors_aus[sector], log_if_empty=False
        ).process_over("sector", "sum", op_cols={"sector": sector}, as_run=True)
    )
point_timeseries_ceds = scmdata.run_append(point_timeseries_ceds)
point_timeseries_ceds = point_timeseries_ceds.append(
    point_timeseries_ceds.process_over("sector", "sum", op_cols={"sector": "Total"})
)


# %%
for by_variable in point_timeseries_ceds.groupby("variable"):
    fig, axs = plt.subplots(len(SECTOR_MAP) + 1, 2, figsize=(12, 24), sharex=True)
    fig.suptitle(by_variable.get_unique_meta("variable", True))

    for i, sector in enumerate(["Total"] + SECTOR_MAP):
        by_sector = by_variable.filter(sector=sector, log_if_empty=False)
        if not len(by_sector):
            continue
        by_sector.filter(region="Melbourne", log_if_empty=False).lineplot(
            hue="scenario", style="grid", ax=axs[i, 0], legend=i == 0
        )
        by_sector.filter(region="La Trobe", log_if_empty=False).lineplot(
            hue="scenario", style="grid", ax=axs[i, 1], legend=False
        )
        axs[i, 0].set_title(by_sector.get_unique_meta("sector", True) + " - Melb")
        axs[i, 1].set_title(by_sector.get_unique_meta("sector", True) + " - La Trobe")
    fig.tight_layout()
    variable = by_variable.get_unique_meta("variable", True)

    os.makedirs(os.path.join(out_dir, "points_by_ceds_sector"), exist_ok=True)
    plt.savefig(os.path.join(out_dir, "points_by_ceds_sector", f"{variable}.png"))

# %%
# two points (Melbourne CBD and LaTrobe) line plots by gas
ts_to_plot = point_timeseries.process_over("sector", "sum", as_run=True)
variables = ts_to_plot.get_unique_meta("variable")

fig, axs = plt.subplots(len(variables), 2, figsize=(12, 18))

for i, variable in enumerate(variables):
    by_variable = ts_to_plot.filter(variable=variable)
    by_variable.filter(grid="australia").lineplot(
        hue="scenario", style="region", ax=axs[i, 0], legend=i == 0
    )
    by_variable.filter(grid="victoria").lineplot(
        hue="scenario", style="region", ax=axs[i, 1], legend=False
    )
    axs[i, 0].set_title(variable + " - AUS")
    axs[i, 1].set_title(variable + " - VIC")
fig.tight_layout()
os.makedirs(os.path.join(out_dir, "points_by_species"), exist_ok=True)
plt.savefig(os.path.join(out_dir, "points_by_species", f"points_by_species.png"))

# %%

# %% [markdown]
# ## Figure 1
#

# %%
ceds_nox = database.load("NOx-em-anthro", "CR-MESSAGE-GLOBIOM-ssp245-high")
proxy = (
    ceds_nox["NOx_em_anthro"]
    .sel(sector=SECTOR_MAP.index("Transportation Sector"))
    .groupby("time.year")
    .mean()
)
proxy = clip_region(proxy, vic_inv.border_mask)
proxy

# %%
vic_data_to_plot = vic_inv.data["NOx"].sel(sector="motor_vehicles")
vic_data_to_plot = from_cell_totals(vic_data_to_plot)

# %%
fig, axs = plt.subplots(2, 3, figsize=(20, 12))

from_cell_totals(vic_inv.data["NOx"].sel(sector="motor_vehicles")).plot(
    ax=axs[0, 0], robust=True, vmin=0
)

proxy.interp(year=2016).plot(ax=axs[0, 1], robust=True, vmin=0)
proxy.interp(year=2060).plot(ax=axs[1, 0], robust=True, vmin=0)
pd.Series(
    [
        vic_data_to_plot.mean().values.squeeze(),
        proxy.interp(year=2016).mean().values.squeeze(),
    ],
    dtype=float,
    index=["EPA", "CEDS"],
).plot.bar(ax=axs[0, 2])

(proxy.interp(year=2060) / proxy.interp(year=2016)).plot(ax=axs[1, 1], vmin=0, vmax=1)

vic_results["NOx"].sel(scenario="ssp245", year=2060, sector="motor_vehicles").plot(
    ax=axs[1, 2], robust=True, vmin=0
)

# %% [markdown]
#
# ## Figure 2

# %%
h2_emissions = scmdata.ScmRun(
    os.path.join(
        RUNS_DIR,
        "ssp245_victoria/inputs/scenarios/v20230324_1/MESSAGE-GLOBIOM_ssp245_med/emissions_country.csv",
    )
).filter(region="AUS", variable="Emissions|H2|Transportation Sector")
h2_emissions

# %%
get_proxy("australian_inventory|TRO_noRES", inventory=vic_inv).plot(robust=True)

# %%
fig, axs = plt.subplots(1, 3, figsize=(20, 8))

h2_emissions.line_plot(ax=axs[0])

clip_region(
    get_proxy("australian_inventory|TRO_noRES", inventory=vic_inv), vic_inv.border_mask
).plot(ax=axs[1])

vic_results["H2"].sel(scenario="ssp245", year=2060, sector="motor_vehicles").plot(
    ax=axs[2], robust=True
)

# %
