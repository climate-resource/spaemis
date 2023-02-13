import os

import click

from spaemis.constants import ROOT_DIR
from spaemis.inventory import load_inventory, write_inventory_csvs

TEST_DATA_DIR = os.path.join(ROOT_DIR, "tests", "test-data")


@click.command()
def downsample_inventory():
    """
    Downsample victoria Inventory data onto a coarser grid for testing
    """
    inventory = load_inventory("victoria", 2016)
    data = inventory.data.coarsen(
        {"lat": 10, "lon": 10},
        boundary="trim",
    ).sum()
    data = data.where(data > 0)

    out_dir = os.path.join(
        TEST_DATA_DIR,
        "inventory",
        "decimated",
    )
    os.makedirs(out_dir, exist_ok=True)

    data.to_netcdf(os.path.join(out_dir, "inventory_decimated.nc"))

    out_dir = os.path.join(TEST_DATA_DIR, "inventory", "decimated", "2016")
    os.makedirs(out_dir, exist_ok=True)
    write_inventory_csvs(data, out_dir)


if __name__ == "__main__":
    downsample_inventory()
