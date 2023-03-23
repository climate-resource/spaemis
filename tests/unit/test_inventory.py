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


def test_write_inventory(
    inventory,
    tmpdir,
):
    write_inventory_csvs(inventory.data, tmpdir)

    class TestVicGrid:
        lats = inventory.data["lat"].values.tolist()
        lons = inventory.data["lon"].values.tolist()

    assert len(os.listdir(tmpdir)) == len(inventory.data["sector"])

    # We should be able to read these inventory files back as EmissionsInventory
    new_inv = VictoriaEPAInventory.load_from_directory(
        tmpdir,
        year=2016,
        file_suffix="_projected.csv",
        grid=TestVicGrid(),
    )
    xrt.assert_allclose(new_inv.data, inventory.data)
