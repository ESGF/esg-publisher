import pytest

from unittest.mock import patch

from netCDF4 import Dataset

from esgcet.args import PublisherArgs
from esgcet.generic_netcdf import GenericPublisher
from esgcet.stac.stac_converter import ESGSTACConverter

import pathlib
import json
import shutil


def test_mapfile_get_args(test_map_cmip6, test_config_file):
    pub_args = PublisherArgs()
    test_argv = ["prog", "--map", str(test_map_cmip6)]
    with patch("sys.argv", test_argv):
        args = pub_args.get_args()

    # When ESG_CONFIG_FILE env var is set (by conftest auto-use fixture), args.cfg uses that
    # Otherwise it defaults to ~/.esg/esg.yaml
    import os
    if 'ESG_CONFIG_FILE' in os.environ:
        assert args.cfg == os.environ['ESG_CONFIG_FILE']
    else:
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


def test_cmip7_missing_parent_attributes_are_not_reused(data_dir, tmp_path, test_map_cmip7):
    """Test CMIP7 files without optional parent attrs do not reuse prior property values."""
    parent_attrs = [
        "parent_activity_id",
        "parent_experiment_id",
        "parent_mip_era",
        "parent_source_id",
        "parent_time_units",
        "parent_variant_label",
    ]

    map_parts = [p.strip() for p in test_map_cmip7.read_text().splitlines()[0].split("|")]
    source_file = pathlib.Path(map_parts[1].replace("$TEST_DATA", str(data_dir)))
    target_file = tmp_path / source_file.relative_to(data_dir)
    target_file.parent.mkdir(parents=True)
    shutil.copy2(source_file, target_file)

    with Dataset(target_file, "a") as dataset:
        for attr in parent_attrs:
            if attr in dataset.ncattrs():
                dataset.delncattr(attr)

    map_file = tmp_path / "cmip7_missing_parent_attrs.map"
    map_parts[1] = str(target_file)
    map_file.write_text(" | ".join(map_parts) + "\n")

    with patch("sys.argv", ["prog", "--map", str(map_file)]):
        argdict = PublisherArgs().get_dict("MIP-DRS7")

    argdict['fullmap'] = str(map_file)
    argdict['mountpoints'] = {}
    argdict['data_roots'] = {str(tmp_path): 'test_esg_dataroot'}
    argdict['data_node'] = 'test.data.node'
    argdict['index_node'] = 'test.index.node'

    generic_pub = GenericPublisher(argdict)
    map_json = generic_pub.mapfile()
    generic_pub.extract_method(map_json)
    out_json = generic_pub.mk_dataset(map_json)

    dataset_doc = out_json[-1]
    pid = "hdl:21.14107/2a9350a4-57bf-3642-a25f-a1b76b106cd4"
    dataset_doc["pid"] = pid
    item = ESGSTACConverter({"stac_api": "https://esgf-stac.llnl.gov/api"}).convert2stac(out_json)

    assert item is not None
    assert item["properties"]["cmip7:pid"] == pid
    for attr in parent_attrs:
        assert attr not in dataset_doc
        assert f"cmip7:{attr}" not in item["properties"]


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
def test_kerchunk_generate(data_dir, tmp_path, test_map_cmip6, backend, inline_threshold, esgvoc_available):
    if not esgvoc_available:
        pytest.skip("esgvoc not initialized - run 'esgvoc use cmip6@latest' first")
    test_map = test_map_cmip6
    
    pub_args = PublisherArgs()
    test_argv = ["prog", "--map", str(test_map)]
    with patch("sys.argv", test_argv):
        argdict = pub_args.get_dict('CMIP6')

    argdict['fullmap'] = str(test_map)
    argdict['mountpoints'] = {"$TEST_DATA": str(data_dir)}

    # New integration branch requirements
    # data_roots maps local path prefix to relative URL path
    # The local files are in .../data/CMIP6/DCPP/...
    # We want URLs like https://node/thredds/fileServer/CMIP6/DCPP/...
    # So map data_dir to empty string (the CMIP6 is already in the file path)
    argdict['data_roots'] = {str(data_dir) + "/": ""}
    argdict['data_node'] = "esgf-node.ornl.gov"

    argdict['kerchunk'] = {}
    argdict['kerchunk']['generation'] = True
    argdict['kerchunk']['backend'] = backend
    argdict['kerchunk']['inline_threshold'] = inline_threshold
    argdict['kerchunk']['data_dir'] = {str(tmp_path): "https://test.data.node/kerchunk"}
    argdict['kerchunk']['filter_frequency'] = "mon"


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

