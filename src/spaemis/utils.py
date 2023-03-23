"""
General utility functions
"""
import os
from contextlib import contextmanager
from typing import Union

import geopandas
import numpy as np
import pooch
import rioxarray  # noqa
import xarray as xr


def area_grid(lat, lon):  # pragma: no cover
    """
    Calculate the area of each grid cell

    Area is in square meters

    Parameters
    ----------
    lat
        Vector of latitude in degrees
    lon
        Vector of longitude in degrees

    Returns
    -------
    area: grid-cell area in square-meters with dimensions, [lat,lon]

    Notes
    -----
    Based on the function in
    https://github.com/chadagreene/CDT/blob/master/cdt/cdtarea.m
    """
    xlon, ylat = np.meshgrid(lon, lat)
    R = earth_radius(ylat)

    dlat = np.deg2rad(np.gradient(ylat, axis=0))
    dlon = np.deg2rad(np.gradient(xlon, axis=1))

    dy = dlat * R
    dx = dlon * R * np.cos(np.deg2rad(ylat))

    area = dy * dx

    xda = xr.DataArray(
        area,
        dims=["lat", "lon"],
        coords={"lat": lat, "lon": lon},
        attrs={
            "long_name": "area_per_cell",
            "description": "area per cell",
            "units": "m^2",
        },
    )
    return xda


def earth_radius(lat: np.ndarray) -> np.ndarray:  # pragma: no cover
    """
    Calculate radius of Earth assuming oblate spheroid
    defined by WGS84

    Parameters
    ----------
    lat: vector or latitudes in degrees

    Returns
    -------
    Vector of radius in meters

    Notes
    -----
    WGS84: https://earth-info.nga.mil/GandG/publications/tr8350.2/tr8350.2-a/Chapter%203.pdf
    """
    # define oblate spheroid from WGS84
    a = 6378137
    b = 6356752.3142
    e2 = 1 - (b**2 / a**2)

    # convert from geodecic to geocentric
    # see equation 3-110 in WGS84
    lat = np.deg2rad(lat)
    lat_gc = np.arctan((1 - e2) * np.tan(lat))

    # radius equation
    # see equation 3-107 in WGS84
    r = (a * (1 - e2) ** 0.5) / (1 - (e2 * np.cos(lat_gc) ** 2)) ** 0.5

    return r


def clip_region(
    da: Union[xr.DataArray, xr.Dataset], boundary: geopandas.GeoDataFrame
) -> Union[xr.DataArray, xr.Dataset]:
    """
    Clip a region out of a larger DS

    Parameters
    ----------
    da
    boundary
        Boundary to cut out

        GeoJSON is expected so it must have a geometry array

    Returns
    -------
        Dataset which only includes the selected area
    """
    return (
        da.rio.set_spatial_dims("lon", "lat")
        .rio.write_crs("WGS84")
        .rio.clip(boundary.geometry.values, all_touched=True)
        .drop("spatial_ref")
    )


def weighted_annual_mean(
    ds: xr.Dataset, variable: str
) -> xr.DataArray:  # pragma: no cover
    """
    Calculate a weighted temporal annual mean

    This method takes into account the different number of days in each month

    Parameters
    ----------
    ds
    variable
        Variable to calculate the weighted mean of

    Returns
    -------
    Weighted annual mean of the target variable
    """
    # Determine the month length
    month_length = ds.time.dt.days_in_month
    weights = (
        month_length.groupby("time.year") / month_length.groupby("time.year").sum()
    )

    # Make sure the weights in each year add up to 1
    np.testing.assert_allclose(weights.groupby("time.year").sum(xr.ALL_DIMS), 1.0)

    target = ds[variable]

    # Mask out any nan values
    ones = xr.where(target.isnull(), 0.0, 1.0)

    obs_sum = (target * weights).resample(time="AS").sum(dim="time")
    ones_out = (ones * weights).resample(time="AS").sum(dim="time")
    return obs_sum / ones_out


@contextmanager
def chdir(current_directory: str) -> None:
    """
    Context manager to temporarily change the current working directory

    Should not be used in async or parallel methods as it changes
    the global state

    Parameters
    ----------
    current_directory
    """
    previous = os.getcwd()
    try:
        os.chdir(current_directory)
        yield
    finally:
        os.chdir(previous)


def load_australia_boundary() -> geopandas.GeoDataFrame:
    """
    Load Australia boundary shapefile


    Returns
    -------
        GeoDataFrame containing borders for each state
    """
    aus_boundary_dir = pooch.retrieve(
        "https://www.github.com/wmgeolab/geoBoundaries/raw/c9c6efd0c2e035a5453fd8549bd1ca507a3910b4/releaseData/gbOpen/AUS/ADM1/geoBoundaries-AUS-ADM1-all.zip",
        known_hash="d531bbed14d9c98652b619cffa6bcdaa972ea49eff1f74b4650c0287deb5ffe9",
        processor=pooch.Unzip(),
    )

    aus_boundary = geopandas.read_file(
        os.path.join(os.path.dirname(aus_boundary_dir[0]), "geoBoundaries-AUS-ADM1.shp")
    ).to_crs("EPSG:4326")
    return aus_boundary
