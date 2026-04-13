import pytest

from unittest.mock import patch

from esgcet.args import PublisherArgs
from esgcet.generic_netcdf import GenericPublisher

import pathlib


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
