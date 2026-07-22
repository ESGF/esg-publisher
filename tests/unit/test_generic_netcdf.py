import pytest

from unittest.mock import patch

from esgcet.args import PublisherArgs
from esgcet.generic_netcdf import GenericPublisher

import pathlib
import json


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

    # Add required fields that would normally come from config file
    if 'data_node' not in argdict or argdict['data_node'] is None:
        argdict['data_node'] = 'test.data.node'
    if 'index_node' not in argdict or argdict['index_node'] is None:
        argdict['index_node'] = 'test.index.node'
    # Override data_roots to point to test data directory
    argdict['data_roots'] = {str(data_dir): 'test_esg_dataroot'}

    generic_pub = GenericPublisher(argdict)

    map_json = generic_pub.mapfile()

    generic_pub.extract_method(map_json)

    out_json = generic_pub.mk_dataset(map_json)


@pytest.mark.skip(reason="Requires QAQC configuration and positive/negative test files - to be implemented")
@pytest.mark.parametrize("test_map_fixture, project, enable_qaqc", [
    ("test_map_cmip6", "CMIP6", True),
    ("test_map_cmip7", "MIP-DRS7", True),
    ("test_map_cmip6", "CMIP6", False),
    ("test_map_cmip7", "MIP-DRS7", False),
])
def test_compliance_check(data_dir, request, test_map_fixture, project, enable_qaqc):

    test_map = request.getfixturevalue(test_map_fixture)
    
    pub_args = PublisherArgs()
    test_argv = ["prog", "--map", str(test_map)]
    with patch("sys.argv", test_argv):
        argdict = pub_args.get_dict(project)

    argdict['fullmap'] = str(test_map)
    argdict['mountpoints'] = {"$TEST_DATA": str(data_dir)}

    if enable_qaqc:
        argdict['disable_qaqc'] = False
    else:
        argdict['disable_qaqc'] = True
    generic_pub = GenericPublisher(argdict)
    map_json = generic_pub.mapfile()
    generic_pub.project = project.lower()
    
    ret = generic_pub.compliance_check(map_json)

    # TODO: This test needs proper QAQC configuration and test files
    # When QAQC is disabled, it should pass (return True)
    # When QAQC is enabled but not configured for the project, it warns and passes (return True)
    # When QAQC is enabled and configured, it runs checks (can pass or fail based on data)
    if enable_qaqc:
        # Need positive and negative example files to properly test QAQC
        assert ret == False  # Expected behavior with proper QAQC config
    else:
        assert ret == True


@pytest.mark.parametrize(
    "backend, inline_threshold", [
        ("kerchunk", 0),
        pytest.param("kerchunk", 500, marks=pytest.mark.xfail(strict=True),),
        ("virtualizarr",0),
    ]
)
def test_kerchunk_generate(data_dir, tmp_path, test_map_cmip6, backend, inline_threshold):
    test_map = test_map_cmip6
    
    pub_args = PublisherArgs()
    test_argv = ["prog", "--map", str(test_map)]
    with patch("sys.argv", test_argv):
        argdict = pub_args.get_dict('CMIP6')

    argdict['fullmap'] = str(test_map)
    argdict['mountpoints'] = {"$TEST_DATA": str(data_dir)}


    argdict['kerchunk'] = {}
    argdict['kerchunk']['generation'] = True
    argdict['kerchunk']['old_uri'] = str(data_dir)
    argdict['kerchunk']['new_uri'] = "https://esgf-node.ornl.gov/thredds/fileServer/"
    argdict['kerchunk']['backend'] = backend
    argdict['kerchunk']['inline_threshold'] = inline_threshold
    argdict['kerchunk']['data_dir'] = tmp_path


    generic_pub = GenericPublisher(argdict)
    map_json = generic_pub.mapfile()
    generic_pub.project = "cmip6"

    generic_pub.kerchunk_generate()

    expected_file = (data_dir / 
        f"kerchunk/CMIP6.DCPP.MRI.MRI-ESM2-0.dcppA-hindcast.s2017-r1i1p1f1.Amon.psl.gn.v20210114.json.{backend}")

    json_files = list(tmp_path.glob("*.json"))

    assert len(json_files) == 1
    actual = json.loads(json_files[0].read_text())
    expected = json.loads(pathlib.Path(expected_file).read_text())

    assert actual == expected

