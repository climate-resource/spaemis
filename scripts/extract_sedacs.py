"""
Extract the SEDACS population proxy
"""

import os

import rioxarray  # noqa
import xarray as xr

from spaemis.constants import PROCESSED_DATA_DIR, RAW_DATA_DIR
from spaemis.utils import load_australia_boundary


def extract_sedac():
    """
    Extract a SEDACS population file into an xarray object

    The SEDACS file should be downloaded manually from https://sedac.ciesin.columbia.edu/
    """
    da = xr.open_dataset(
        os.path.join(
            RAW_DATA_DIR,
            "sedacs",
            "BaseYear_1km/baseYr_total_2000.nc4",
        ),
    )["Band1"]
    da.name = "population"
    da.attrs["long_name"] = "Population"
    del da.attrs["grid_mapping"]

    aus_boundary = load_australia_boundary()
    da_clipped = da.rio.write_crs("EPSG:4326").rio.clip(aus_boundary.geometry)
    return da_clipped.rio.write_crs("EPSG:4326")


if __name__ == "__main__":
    da = extract_sedac()

    root_dir = os.environ.get(
        "SPAEMIS_PROXY_DIRECTORY", os.path.join(PROCESSED_DATA_DIR, "proxies")
    )

    out_name = os.path.join(
        root_dir,
        "sedacs",
        "popdynamics-base_year-2000-rev01-byr.nc",
    )
    os.makedirs(os.path.dirname(out_name), exist_ok=True)
    da.to_netcdf(out_name)
