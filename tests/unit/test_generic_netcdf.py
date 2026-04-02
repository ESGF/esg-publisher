import pytest

from unittest.mock import patch

from esgcet.args import PublisherArgs
from esgcet.generic_netcdf import GenericPublisher

import pathlib

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




def test_mapfile_get_args(test_map_cmip6):
    pub_args = PublisherArgs()
    test_argv = ["prog", "--map", str(test_map_cmip6)]
    with patch("sys.argv", test_argv):
        args = pub_args.get_args()

    assert args.cfg == str(pathlib.Path.home() / ".esg/esg.yaml")
    assert args.map[0] == str(test_map_cmip6)


def test_generic_publisher(data_dir, test_map_cmip6):

    pub_args = PublisherArgs()
    test_argv = ["prog", "--map", str(test_map_cmip6)]
    with patch("sys.argv", test_argv):
        argdict = pub_args.get_dict('CMIP6')

    argdict['fullmap'] = str(test_map_cmip6)
    argdict['mountpoints'] = {"$TEST_DATA": str(data_dir)}
    generic_pub = GenericPublisher(argdict)

    map_json = generic_pub.mapfile()

    generic_pub.extract_method(map_json)
    
    out_json = generic_pub.mk_dataset(map_json)


@pytest.mark.parametrize("test_map_fixture, project", [
    ("test_map_cmip6", "CMIP6"),
    ("test_map_cmip7", "MIP-DRS7"),
])
def test_compliance_check(data_dir, request, test_map_fixture, project):

    test_map = request.getfixturevalue(test_map_fixture)
    
    pub_args = PublisherArgs()
    test_argv = ["prog", "--map", str(test_map)]
    with patch("sys.argv", test_argv):
        argdict = pub_args.get_dict(project)

    argdict['fullmap'] = str(test_map)
    argdict['mountpoints'] = {"$TEST_DATA": str(data_dir)}
    generic_pub = GenericPublisher(argdict)
    map_json = generic_pub.mapfile()
    generic_pub.project = project.lower()
    
    ret, cc_report = generic_pub.compliance_check(map_json)

    assert ret == False
