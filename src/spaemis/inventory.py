import glob
import os
from typing import Optional, Union

import geopandas
import pandas as pd
import xarray as xr
from attrs import define, field

from spaemis.constants import RAW_DATA_DIR
from spaemis.utils import clip_region


def has_dimensions(dimensions: Union[str, list[str]]):
    dimensions: list[str] = [dimensions] if isinstance(dimensions, str) else dimensions

    def _check(instance, attribute, value):
        if value >= instance.y:
            raise ValueError("'x' has to be smaller than 'y'!")

    return _check


@define
class EmissionsInventory:
    """
    An emissions inventory is a set of bottom up
    """

    data: xr.Dataset = field(validator=[has_dimensions(["test"])])
    border_mask: geopandas.GeoDataFrame
    year: int

    @classmethod
    def load_from_directory(cls, data_directory) -> "EmissionsInventory":
        """
        Loads an emissions inventory from a directory
        """
        pass


@define
class VictoriaEPAInventory(EmissionsInventory):

    nx: int = 903
    ny: int = 592
    x0: float = 140.6291
    y0: float = -39.5402
    dx: float = 0.01059988
    dy: float = 0.01059988

    @classmethod
    def load_from_directory(cls, data_directory) -> "VictoriaEPAInventory":
        fnames = glob.glob(data_directory + "*.csv")
        if not fnames:
            raise ValueError("No data found for Victoria")
        lats = [
            VictoriaEPAInventory.y0 + VictoriaEPAInventory.dy * i
            for i in range(VictoriaEPAInventory.ny)
        ]
        lons = [
            VictoriaEPAInventory.x0 + VictoriaEPAInventory.dx * i
            for i in range(VictoriaEPAInventory.nx)
        ]

        def read_file(fname):

            df = pd.read_csv(fname).set_index(["lat", "lon"])
            ds = xr.Dataset.from_dataframe(df)
            ds["lat_new"] = lats
            ds["lon_new"] = lons

            del ds["lat"]
            del ds["lon"]

            return ds.rename({"lat_new": "lat", "lon_new": "lon"}).assign_coords(
                {"sector": os.path.basename(fname).replace("_tif_to_csv3.csv", "")}
            )

        merged_data = xr.concat([read_file(f) for f in fnames], dim="sector")
        merged_data = merged_data.where(merged_data > 0)

        vic_border = geopandas.read_file(
            os.path.join(RAW_DATA_DIR, "masks", "victoria_border_mask.gpkg")
        )
        return VictoriaEPAInventory(
            data=clip_region(merged_data, vic_border), border_mask=vic_border, year=2016
        )


def load_inventory(
    inventory: str, year: Optional[int] = None, data_directory: Optional[str] = None
) -> EmissionsInventory:
    data_directory = data_directory or os.path.join(
        RAW_DATA_DIR, "inventories", inventory, str(year)
    )
    mapping = {("victoria", 2016): VictoriaEPAInventory}

    try:
        loader = mapping[(inventory, year)]
    except KeyError:
        raise ValueError(f"No inventory matching {inventory}|{year}")

    return loader.load_from_directory(data_directory=data_directory)
