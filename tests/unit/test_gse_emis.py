import glob

from spaemis.gse_emis import run_gse


def test_gse(tmpdir):
    run_gse(2000, 10, 10, "", str(tmpdir))

    assert len(glob.glob(str(tmpdir / "*.run"))) == 20
