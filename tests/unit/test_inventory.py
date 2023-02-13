import os

import pytest
import xarray.testing as xrt

from spaemis.inventory import VictoriaEPAInventory, load_inventory, write_inventory_csvs


def test_load_vic_inventory():
    inv = load_inventory("victoria", 2016)

    assert inv.data


@pytest.mark.parametrize("name,year", [("unknown", 2016), ("victoria", 2000)])
def test_load_unknown_inventory(name, year):
    with pytest.raises(ValueError, match=f"No inventory matching {name}|{year}"):
        load_inventory(name, year)


def test_write_inventory(inventory, tmpdir):
    # Decimate inventory for testing
    data = inventory.data.coarsen(
        {"lat": 10, "lon": 10},
        boundary="trim",
    ).sum()

    data = data.where(data > 0)

    class TestVicGrid:
        lats = data["lat"].values.tolist()
        lons = data["lon"].values.tolist()

    write_inventory_csvs(data, tmpdir)

    assert len(os.listdir(tmpdir)) == len(data["sector"])

    # We should be able to read these inventory files back as EmissionsInventory
    new_inv = VictoriaEPAInventory.load_from_directory(
        tmpdir,
        file_suffix="_projected.csv",
        grid=TestVicGrid(),
    )
    xrt.assert_allclose(new_inv.data, data)
