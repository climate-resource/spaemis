import numpy as np

def area_grid(lat, lon):
    """
    Calculate the area of each grid cell
    Area is in square meters

    Input
    -----------
    lat: vector of latitude in degrees
    lon: vector of longitude in degrees

    Output
    -----------
    area: grid-cell area in square-meters with dimensions, [lat,lon]

    Notes
    -----------
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


def earth_radius(lat):
    """
    calculate radius of Earth assuming oblate spheroid
    defined by WGS84

    Input
    ---------
    lat: vector or latitudes in degrees

    Output
    ----------
    r: vector of radius in meters

    Notes
    -----------
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

def clip_region(ds, boundary):
    return     (ds.rio.set_spatial_dims("lon", "lat")
    .rio.write_crs("WGS84")
    .rio.clip(boundary.geometry.values)
                )