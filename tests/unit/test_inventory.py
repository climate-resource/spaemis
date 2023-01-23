import pytest

from spaemis.inventory import load_inventory


def test_load_vic_inventory():
    inv = load_inventory("victoria", 2016)

    assert inv.data


@pytest.mark.parametrize("name,year", [("unknown", 2016), ("victoria", 2000)])
def test_load_unknown_inventory(name, year):
    with pytest.raises(ValueError, match=f"No inventory matching {name}|{year}"):
        load_inventory(name, year)
