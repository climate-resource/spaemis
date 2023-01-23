import glob
import os
import pandas as pd
from attrs import define

import xarray as xr

def read_grid():
    nx = 903
    ny = 592
    x0 = 140.6291
    y0 = -39.5402
    dx = 0.01059988
    dy = 0.01059988

    lats = [y0 + dy * i for i in range(ny)]
    lons = [x0 + dx * i for i in range(nx)]



def read_vic_inventory():
    merged_data = xr.concat([read_input_file(f) for f in fnames], dim="sector")
    merged_data = merged_data.where(merged_data > 0)


@define
class VicEPAInventory:

    nx: int = 903
    ny: int = 592
    x0: float = 140.6291
    y0: float = -39.5402
    dx: float = 0.01059988
    dy: float = 0.01059988

    sectors: list[str] = [
    "aircraft",
    "rail",
    "shipping",
    "motor_vehicles",
    "crematoria",
    "petcrematoria",
    "industry_diffuse",
    "woodheater",
    "architect_coating",
    "bakery",
    "charcoal",
    "cutback_bitumen",
    "domestic_solvents",
    "dry_cleaning",
    "gas_leak",
    "panel_beaters",
    "printing",
    "servos",
        "pizza",
        "vicbakery",
    ]


    def read_file(self, fname):
        lats = [self.y0 + self.dy * i for i in range(self.ny)]
        lons = [self.x0 + self.dx * i for i in range(self.nx)]

        df = pd.read_csv(fname).set_index(["lat", "lon"])
        ds = xr.Dataset.from_dataframe(df)
        ds["lat_new"] = lats
        ds["lon_new"] = lons

        del ds["lat"]
        del ds["lon"]

        return ds.rename({"lat_new": "lat", "lon_new": "lon"}).assign_coords(
            {"sector": os.path.basename(fname).replace("_tif_to_csv3.csv", "")}
        )

    @classmethod
    def read_from_directory(cls, data_directory: str):
        fnames = glob.glob(data_directory + "*.csv")
        if not fnames:
            raise ValueError("No data found for Victoria")

        return
