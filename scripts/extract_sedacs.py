import os

import geopandas
import pooch
import rioxarray  # noqa
import xarray as xr

from spaemis.constants import PROCESSED_DATA_DIR, RAW_DATA_DIR


def extract_sedac():
    # This files has to be downloaded manually
    da = xr.open_dataarray(
        os.path.join(
            RAW_DATA_DIR,
            "sedacs",
            "gpw_v4_population_density_adjusted_to_2015_unwpp_country_totals_rev11_2020_2pt5_min.tif",
        ),
        engine="rasterio",
    ).sel(band=1)
    da.name = "population"

    aus_boundary_dir = pooch.retrieve(
        "https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files/AUS_2021_AUST_SHP_GDA2020.zip",
        known_hash="086752a6b0b3978247be201f02e02cd4e3c4f36d4f4ca74802e6831083b67129",
        processor=pooch.Unzip(),
    )

    aus_boundary = geopandas.read_file(sorted(aus_boundary_dir)[2])
    da_clipped = (
        da.rio.clip(aus_boundary.geometry)
        .rename(x="lon", y="lat")
        .dropna("lat", how="all")
        .dropna("lon", how="all")
    )
    return da_clipped.reset_coords(["band", "spatial_ref"], drop=True)


if __name__ == "__main__":
    da = extract_sedac()

    out_name = os.path.join(
        PROCESSED_DATA_DIR,
        "proxies",
        "sedacs",
        "gpw_v4_population_density_adjusted_to_2015_unwpp_country_totals_rev11_2020_2pt5_aus.nc",
    )
    os.makedirs(os.path.dirname(out_name), exist_ok=True)
    da.to_netcdf(out_name)
