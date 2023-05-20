"""
Downsample input4MIPS data

These downsampled values are used for testing because they are small and fast
to run
"""
import os
from glob import glob

import click
import xarray as xr

from spaemis.constants import ROOT_DIR

TEST_DATA_DIR = os.path.join(ROOT_DIR, "tests", "test-data")


def _downsample_file(fname, out_path):
    fname_toks = fname.split(os.sep)
    out_fname = os.path.join(out_path, *fname_toks[-11:])
    # Downsample spatial resolution by 10x
    ds = xr.load_dataset(fname)

    ds = ds.isel(lat=ds.lat < 0, lon=ds.lon > 100)  # noqa
    ds = ds.coarsen({"lat": 2, "lon": 2}).mean()

    os.makedirs(os.path.dirname(out_fname), exist_ok=True)
    ds.to_netcdf(out_fname)


@click.command()
@click.argument("root_dir")
def downsample_input4MIPs(root_dir):
    """
    Down sample input4MIPs to a coarser grid for testing purposes

    The selected files must be in the same file structure as
    """
    for f in glob(os.path.join(root_dir, "**", "*.nc"), recursive=True):
        _downsample_file(f, TEST_DATA_DIR)


if __name__ == "__main__":
    downsample_input4MIPs()
