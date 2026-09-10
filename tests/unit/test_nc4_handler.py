"""Tests for NC4 handler (fast metadata-only scanning)."""
import pytest
from unittest.mock import patch

from esgcet.args import PublisherArgs
from esgcet.generic_netcdf import GenericPublisher


def test_nc4_handler_with_cordex_cmip6(data_dir, test_map_cordex_cmip6):
    """Test NC4 handler can scan CORDEX-CMIP6 data with --no-xarray."""
    pub_args = PublisherArgs()
    test_argv = ["prog", "--map", str(test_map_cordex_cmip6), "--no-xarray"]

    with patch("sys.argv", test_argv):
        argdict = pub_args.get_dict('CORDEX-CMIP6')

    # Verify skipxr is set
    assert argdict['skipxr'] is True

    # Setup publisher args
    argdict['fullmap'] = str(test_map_cordex_cmip6)
    argdict['mountpoints'] = {}
    argdict['data_roots'] = {str(data_dir / "CORDEX-CMIP6"): 'test_esg_dataroot'}
    argdict['data_node'] = 'test.data.node'
    argdict['index_node'] = 'test.index.node'

    # Create publisher with NC4 handler (via skipxr)
    generic_pub = GenericPublisher(argdict)
    map_json = generic_pub.mapfile()
    generic_pub.extract_method(map_json)
    records = generic_pub.mk_dataset(map_json)

    # Verify records were created
    assert len(records) > 0

    # Last record should be dataset
    dataset_record = records[-1]
    assert dataset_record["type"] == "Dataset"
    assert dataset_record["project"] == "CORDEX-CMIP6"

    # Verify NC4 handler extracted spatial bounds
    assert "west_degrees" in dataset_record
    assert "south_degrees" in dataset_record
    assert "east_degrees" in dataset_record
    assert "north_degrees" in dataset_record

    # Verify temporal bounds were extracted
    assert "datetime_start" in dataset_record
    assert "datetime_end" in dataset_record

    # Verify DRS facets were extracted
    assert dataset_record["domain_id"] == "NAM-25"
    assert dataset_record["institution_id"] == "CCCma"
    assert dataset_record["variable_id"] == "tas"


def test_nc4_handler_with_cmip6(data_dir, test_map_cmip6):
    """Test NC4 handler can scan CMIP6 data with --no-xarray."""
    pub_args = PublisherArgs()
    test_argv = ["prog", "--map", str(test_map_cmip6), "--no-xarray", "--project", "CMIP6"]

    with patch("sys.argv", test_argv):
        argdict = pub_args.get_dict('CMIP6')

    # Verify skipxr is set
    assert argdict['skipxr'] is True

    # Setup publisher args
    argdict['fullmap'] = str(test_map_cmip6)
    argdict['mountpoints'] = {"$TEST_DATA": str(data_dir)}
    argdict['data_roots'] = {str(data_dir): 'test_esg_dataroot'}
    argdict['data_node'] = 'test.data.node'
    argdict['index_node'] = 'test.index.node'
    argdict['proj'] = 'CMIP6'  # Ensure project is set

    # Create publisher with NC4 handler (via skipxr)
    generic_pub = GenericPublisher(argdict)
    map_json = generic_pub.mapfile()
    generic_pub.extract_method(map_json)
    records = generic_pub.mk_dataset(map_json)

    # Verify records were created
    assert len(records) > 0

    # Last record should be dataset
    dataset_record = records[-1]
    assert dataset_record["type"] == "Dataset"
    assert dataset_record["project"] == "CMIP6"

    # Verify NC4 handler extracted metadata
    assert "west_degrees" in dataset_record
    assert "datetime_start" in dataset_record

    # Verify CMIP6 facets
    assert dataset_record["variable_id"] == "psl"
    assert dataset_record["experiment_id"] == "dcppA-hindcast"


def test_nc4_handler_with_cmip7(data_dir, test_map_cmip7_single):
    """Test NC4 handler can scan CMIP7 (MIP-DRS7) data with --no-xarray."""
    pub_args = PublisherArgs()
    test_argv = ["prog", "--map", str(test_map_cmip7_single), "--no-xarray"]

    with patch("sys.argv", test_argv):
        argdict = pub_args.get_dict('MIP-DRS7')

    # Verify skipxr is set
    assert argdict['skipxr'] is True

    # Setup publisher args
    argdict['fullmap'] = str(test_map_cmip7_single)
    argdict['mountpoints'] = {"$TEST_DATA": str(data_dir)}
    argdict['data_roots'] = {str(data_dir): 'test_esg_dataroot'}
    argdict['data_node'] = 'test.data.node'
    argdict['index_node'] = 'test.index.node'

    # Create publisher with NC4 handler (via skipxr)
    generic_pub = GenericPublisher(argdict)
    map_json = generic_pub.mapfile()
    generic_pub.extract_method(map_json)
    records = generic_pub.mk_dataset(map_json)

    # Verify records were created
    assert len(records) > 0

    # Last record should be dataset
    dataset_record = records[-1]
    assert dataset_record["type"] == "Dataset"
    assert dataset_record["project"] == "CMIP7"

    # Verify NC4 handler extracted metadata
    assert "west_degrees" in dataset_record
    assert "datetime_start" in dataset_record

    # Verify CMIP7 facets
    assert dataset_record["variable_id"] == "tas"
    assert dataset_record["experiment_id"] == "1pctCO2"


def test_nc4_handler_extracts_same_bounds_as_xarray(data_dir, test_map_cordex_cmip6):
    """Test that NC4 handler extracts same spatial bounds as Xarray handler."""
    # First run with Xarray (default)
    pub_args = PublisherArgs()
    test_argv_xr = ["prog", "--map", str(test_map_cordex_cmip6)]

    with patch("sys.argv", test_argv_xr):
        argdict_xr = pub_args.get_dict('CORDEX-CMIP6')

    argdict_xr['fullmap'] = str(test_map_cordex_cmip6)
    argdict_xr['mountpoints'] = {}
    argdict_xr['data_roots'] = {str(data_dir / "CORDEX-CMIP6"): 'test_esg_dataroot'}
    argdict_xr['data_node'] = 'test.data.node'
    argdict_xr['index_node'] = 'test.index.node'

    generic_pub_xr = GenericPublisher(argdict_xr)
    map_json_xr = generic_pub_xr.mapfile()
    generic_pub_xr.extract_method(map_json_xr)
    records_xr = generic_pub_xr.mk_dataset(map_json_xr)
    dataset_xr = records_xr[-1]

    # Now run with NC4 handler
    test_argv_nc4 = ["prog", "--map", str(test_map_cordex_cmip6), "--no-xarray"]

    with patch("sys.argv", test_argv_nc4):
        argdict_nc4 = pub_args.get_dict('CORDEX-CMIP6')

    argdict_nc4['fullmap'] = str(test_map_cordex_cmip6)
    argdict_nc4['mountpoints'] = {}
    argdict_nc4['data_roots'] = {str(data_dir / "CORDEX-CMIP6"): 'test_esg_dataroot'}
    argdict_nc4['data_node'] = 'test.data.node'
    argdict_nc4['index_node'] = 'test.index.node'

    generic_pub_nc4 = GenericPublisher(argdict_nc4)
    map_json_nc4 = generic_pub_nc4.mapfile()
    generic_pub_nc4.extract_method(map_json_nc4)
    records_nc4 = generic_pub_nc4.mk_dataset(map_json_nc4)
    dataset_nc4 = records_nc4[-1]

    # Compare spatial bounds - should be identical (or very close)
    assert dataset_xr["west_degrees"] == pytest.approx(dataset_nc4["west_degrees"], rel=1e-3)
    assert dataset_xr["south_degrees"] == pytest.approx(dataset_nc4["south_degrees"], rel=1e-3)
    assert dataset_xr["east_degrees"] == pytest.approx(dataset_nc4["east_degrees"], rel=1e-3)
    assert dataset_xr["north_degrees"] == pytest.approx(dataset_nc4["north_degrees"], rel=1e-3)

    # Compare temporal bounds
    assert dataset_xr["datetime_start"] == dataset_nc4["datetime_start"]
    assert dataset_xr["datetime_end"] == dataset_nc4["datetime_end"]
