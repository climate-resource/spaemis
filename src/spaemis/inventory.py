"""
Loading emissions inventories
"""
from __future__ import annotations

import functools
import glob
import logging
import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar

import geopandas  # type: ignore
import pandas as pd
import xarray as xr
from attrs import define, field
from typing_extensions import Self

from spaemis.constants import RAW_DATA_DIR, TEST_DATA_DIR
from spaemis.utils import clip_region, load_australia_boundary

logger = logging.getLogger(__name__)


T = TypeVar("T", xr.Dataset, xr.DataArray)

if TYPE_CHECKING:
    import attr

    ValidatorType = Callable[[Any, attr.Attribute[T], Any], Any]


def has_dimensions(
    dimensions: str | list[str],
) -> ValidatorType[T]:
    """
    Check if a xarray Dataset or DataArray has the expected dimensions

    Parameters
    ----------
    dimensions
        Dimensions to checks

    Raises
    ------
    ValueError
        If any of the requested dimensions are not present in the data array
    """
    dims: list[str] = [dimensions] if isinstance(dimensions, str) else dimensions

    def _check(instance: Any, attribute: attr.Attribute[T], value: Any) -> None:
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
    def load_from_directory(cls, data_directory: str, year: int, **kwargs: Any) -> Self:
        """
        Load an emissions inventory from a directory
        """
        raise NotImplementedError()


class Grid:
    """
    Configuration for a regular lat/lon mesh
    """

    nx: int
    ny: int
    x0: float
    y0: float
    dx: float
    dy: float

    @property
    def lats(self) -> list[float]:
        """
        Latitudes of the grid
        """
        return [self.y0 + self.dy * i for i in range(self.ny)]

    @property
    def lons(self) -> list[float]:
        """
        Longitudes of the grid
        """
        return [self.x0 + self.dx * i for i in range(self.nx)]


class VictoriaGrid(Grid):
    """
    Information about the grid used in Victoria
    """

    nx: int = 903
    ny: int = 592
    x0: float = 140.6291
    y0: float = -39.5402
    dx: float = 0.01059988
    dy: float = 0.01059988


class AustraliaGrid(Grid):
    """
    Information about the grid used in Australia

    lat/lons represent the center of the cell
    """

    nx: int = 450
    ny: int = 400
    x0: float = 110.05
    y0: float = -10.05
    dx: float = 0.1
    dy: float = -0.1


@define
class VictoriaEPAInventory(EmissionsInventory):
    """
    Victorian EPA data

    CSV files of 1D datapoints. Each grid is slightly different so some post-processing
    is required to get all the variables and sectors on to the same grid.
    """

    @classmethod
    def load_from_directory(
        cls,
        data_directory: str,
        year: int,
        file_suffix: str = "_tif_to_csv3.csv",
        grid: Grid | None = None,
        **kwargs: Any,
    ) -> Self:
        """
        Load Victorian EPA inventory data

        Parameters
        ----------
        data_directory
            Folder containing CSV input files

        grid
            Object containing information about the target grid

        Returns
        -------
        Loaded data
        """
        fnames = sorted(glob.glob(os.path.join(data_directory, "*.csv")))
        if not fnames:
            raise ValueError("No inventory files found for Victoria")

        if grid is None:
            grid = VictoriaGrid()

        # Explicitly cast to grid
        _grid: Grid = grid

        def read_file(fname: str) -> xr.Dataset:
            dataframe = pd.read_csv(fname).set_index(["lat", "lon"])
            dataset = xr.Dataset.from_dataframe(dataframe)
            dataset["lat_new"] = _grid.lats
            dataset["lon_new"] = _grid.lons

            del dataset["lat"]
            del dataset["lon"]

            return dataset.rename({"lat_new": "lat", "lon_new": "lon"}).assign_coords(
                {"sector": os.path.basename(fname).replace(file_suffix, "")}
            )

        # Data should be nan outside of the region of interest, but zero if no emissions
        # present
        merged_data = xr.concat([read_file(f) for f in fnames], dim="sector").fillna(0)

        vic_border = load_australia_boundary()
        vic_border = vic_border[vic_border.shapeName == "Victoria"]
        return cls(
            data=clip_region(merged_data, vic_border), border_mask=vic_border, year=year
        )


@define
class AustraliaInventory(EmissionsInventory):
    """
    Australian data

    CSV files of 1D datapoints. Each grid is slightly different so some post-processing
    is required to get all the variables and sectors on to the same grid.
    """

    @classmethod
    def load_from_directory(
        cls,
        data_directory: str,
        year: int,
        file_suffix: str = ".nc",
        **kwargs: Any,
    ) -> Self:
        """
        Load Australian EDGAR data

        Parameters
        ----------
        data_directory
            Folder containing CSV input files

        grid
            Object containing information about the target grid

        Returns
        -------
        Loaded data
        """
        fnames = sorted(glob.glob(os.path.join(data_directory, "*.nc")))
        if not fnames:
            raise ValueError("No inventory files found for Australia")

        australia_boundary = load_australia_boundary()

        # Data should be nan outside of the region of interest, but zero if no emissions
        # present
        merged_data = xr.merge([xr.load_dataset(f) for f in fnames], join="outer")
        merged_data = merged_data.where(merged_data > 0).fillna(0)

        clipped_data = clip_region(merged_data, australia_boundary)

        return cls(
            data=clipped_data,
            border_mask=australia_boundary,
            year=year,
        )


@define
class TestInventory(EmissionsInventory):
    """
    Test inventory using decimated Vic inventory data
    """

    @classmethod
    def load_from_directory(cls, data_directory: str, year: int, **kwargs: Any) -> Self:
        """
        Load test inventory data

        For testing we use a decimated version of the vic inventory generated using
        ``scripts/downsample_inventory.py``

        Parameters
        ----------
        data_directory
            Folder containing CSV input files

        grid
            Object containing information about the target grid

        Returns
        -------
        Loaded data
        """
        vic_border = load_australia_boundary()
        vic_border = vic_border[vic_border.shapeName == "Victoria"]
        data = xr.load_dataset(
            os.path.join(
                TEST_DATA_DIR,
                "inventory",
                "decimated",
                "inventory_decimated.nc",
            )
        ).drop_vars("spatial_ref")

        return cls(data, border_mask=vic_border, year=2016)


@functools.lru_cache(5)
def load_inventory(
    inventory: str, year: int, data_directory: str | None = None
) -> EmissionsInventory:
    """
    Load an emissions inventory

    Parameters
    ----------
    inventory
        Inventory name
    year
        Year of inventory to load

    data_directory
        If provided, override the default directory to load data from

        If not provided the data directory will be constructed from the
        `SPAEMIS_INVENTORY_DIRECTORY` environment variable, the inventory name
        and inventory year.

    Returns
    -------
        EmissionsInventory with loaded data

    Raises
    ------
    KeyError
        Could not determine the appropriate inventory to load

    """
    inventory_root_directory = os.environ.get(
        "SPAEMIS_INVENTORY_DIRECTORY", os.path.join(RAW_DATA_DIR, "inventories")
    )
    data_directory = data_directory or os.path.join(
        inventory_root_directory, inventory, str(year)
    )
    mapping = {
        ("test", 2016): TestInventory,
        ("victoria", 2016): VictoriaEPAInventory,
        ("australia", 2016): AustraliaInventory,
        ("australia", 2018): AustraliaInventory,
    }

    try:
        loader = mapping[(inventory, year)]
    except KeyError as exc:
        raise ValueError(f"No inventory matching {inventory}|{year}") from exc

    return loader.load_from_directory(data_directory=data_directory, year=year)


def write_inventory_csvs(ds: xr.Dataset, output_dir: str) -> None:
    """
    Serialize a Dataset to CSV files with the same  format as the input inventory data

    Each sector is written into a different file. The CSV file contains rows of data for
    each datapoint on a lat, lon grid. Each variable will be written as a separate column.

    The ordering of the datapoints are lat-major (i.e. iterate over latitude and then
    longitude)

    Parameters
    ----------
    ds
        Data to output

        This dataset should be similar to the format from :attr:`EmissionsInventory.data`.
        in that each data variable contains a sector, lat and lon dimension.
    output_dir
        Output directory for the
    """
    sectors = ds["sector"].values

    for sector in sectors:
        sector_data = ds.sel(sector=sector)
        sector_data = sector_data.reset_coords(
            [k for k in sector_data.coords.keys() if k not in ["lat", "lon"]], drop=True
        )

        output_fname = f"{sector}_projected.csv"

        logger.info(f"Writing output file: {os.path.join(output_dir, output_fname)}")

        df = sector_data.fillna(0).to_dataframe(["lon", "lat"]).reset_index()
        # Round to be similar to the input inventory files
        df["lat"] = df["lat"].round(4)
        df["lon"] = df["lon"].round(4)

        df.to_csv(os.path.join(output_dir, output_fname), index=False)
