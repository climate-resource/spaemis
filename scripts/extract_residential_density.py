import os

import rioxarray  # noqa
import xarray as xr

from spaemis.constants import PROCESSED_DATA_DIR, RAW_DATA_DIR
from spaemis.utils import load_australia_boundary


def extract() -> xr.DataArray:
    # This files has to be downloaded manually
    da = xr.open_dataarray(
        os.path.join(
            RAW_DATA_DIR,
            "ga",
            "NEXIS_Residential_Dwelling_Density.tiff",
        ),
        engine="rasterio",
    ).sel(band=1)
    da = da.where(da < 1e9)
    da.name = "residential_density"

    aus_boundary = load_australia_boundary()
    da_clipped = da.rio.clip(aus_boundary.geometry).rename(x="lon", y="lat")
    return da_clipped.rio.write_crs("EPSG:4326")


if __name__ == "__main__":
    da = extract()
    da.attrs = {}

    out_name = os.path.join(
        PROCESSED_DATA_DIR,
        "proxies",
        "ga",
        "NEXIS_Residential_Dwelling_Density.nc",
    )
    os.makedirs(os.path.dirname(out_name), exist_ok=True)
    da.to_netcdf(out_name)
