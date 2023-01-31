"""
Loading emissions inventories
"""
import glob
import os
from typing import Any, Callable, Optional, Union

import geopandas
import pandas as pd
import xarray as xr
from attrs import Attribute, define, field

from spaemis.constants import RAW_DATA_DIR
from spaemis.utils import clip_region


def has_dimensions(
    dimensions: Union[str, list[str]]
) -> Callable[[Any, Attribute, Union[xr.Dataset, xr.DataArray]], None]:
    dims: list[str] = [dimensions] if isinstance(dimensions, str) else dimensions

    def _check(instance, attribute, value: Union[xr.Dataset, xr.DataArray]) -> None:
        for exp_dim in dims:
            if exp_dim not in value.dims:
                raise ValueError(f"Missing dimension: {exp_dim}")

    return _check


@define
class EmissionsInventory:
    """
    An emissions inventory is a set of bottom up
    """

    data: xr.Dataset = field(
        validator=[
            has_dimensions(["lat", "lon", "sector"]),
        ]
    )
    border_mask: geopandas.GeoDataFrame
    year: int

    @classmethod
    def load_from_directory(cls, data_directory) -> "EmissionsInventory":
        """
        Load an emissions inventory from a directory
        """
        pass


class VictoriaGrid:
    """
    Information about the grid used in Victoria
    """

    nx: int = 903
    ny: int = 592
    x0: float = 140.6291
    y0: float = -39.5402
    dx: float = 0.01059988
    dy: float = 0.01059988

    @property
    def lats(self):
        return [self.y0 + self.dy * i for i in range(self.ny)]

    @property
    def lons(self):
        return [self.x0 + self.dx * i for i in range(self.nx)]


@define
class VictoriaEPAInventory(EmissionsInventory):
    """
    Victorian EPA data

    CSV files of 1D datapoints. Each grid is slightly different so some post-processing
    is required to get all the variables and sectors on to the same grid.
    """

    @classmethod
    def load_from_directory(cls, data_directory: str) -> "VictoriaEPAInventory":
        """
        Load Victorian EPA inventory data

        Parameters
        ----------
        data_directory
            Folder containing CSV input files

        Returns
        -------
        Loaded data
        """
        fnames = glob.glob(os.path.join(data_directory, "*.csv"))
        if not len(fnames):
            raise ValueError("No inventory files found for Victoria")

        grid = VictoriaGrid()

        def read_file(fname):
            df = pd.read_csv(fname).set_index(["lat", "lon"])
            ds = xr.Dataset.from_dataframe(df)
            ds["lat_new"] = grid.lats
            ds["lon_new"] = grid.lons

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
