from pathlib import Path
import pytest

@pytest.fixture
def data_dir():
    return Path(__file__).parent / "data"

@pytest.fixture
def test_map_cmip6(data_dir):
    test_map = (
        data_dir
        / "CMIP6/CMIP6.DCPP.MRI.MRI-ESM2-0.dcppA-hindcast.s2017-r1i1p1f1.Amon.psl.gn.v20210114.map"
    )
    return test_map

@pytest.fixture
def test_map_cmip7(data_dir):
    test_map = (
        data_dir
       #/ "MIP-DRS7/MIP-DRS7.CMIP7.CMIP.CCCma.CanESM6-MR.historical.r2i1p1f3.glb.mon.pr.tavg-u-hxy-u.g99.v20260114.map"
       / "MIP-DRS7/MIP-DRS7.CMIP7.CMIP.MOHC.UKESM1-0-LL.1pctCO2.r1i1p1f3.glb.mon.tas.tavg-h2m-hxy-u.g99.v20260123.map"
       #/ "MIP-DRS7/MIP-DRS7.CMIP7.CMIP.MOHC.UKESM1-0-LL.1pctCO2.r1i1p1f3.glb.mon.pr.tavg-u-hxy-u.g99.v20260123.map"
    )
    return test_map

