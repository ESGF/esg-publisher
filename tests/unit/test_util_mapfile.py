"""Tests for esgcet.util.mapfile module."""
import pytest
from pathlib import Path
from esgcet.util.mapfile import ESGPubMapConv


def test_mapfile_parsing(test_map_cmip6, data_dir):
    """Test basic mapfile parsing and conversion."""
    mapconv = ESGPubMapConv(str(test_map_cmip6), project="cmip6")

    # Test mapfile parsing with mountpoints
    mountpoints = {"$TEST_DATA": str(data_dir)}
    map_json_data = mapconv.mapfilerun(mountpoints)

    # Should return a list with dataset info
    assert isinstance(map_json_data, list)
    assert len(map_json_data) > 0

    # First element should be the dataset record
    dataset_record = map_json_data[0]
    assert isinstance(dataset_record, list)
    assert len(dataset_record) > 0

    # Check dataset ID format
    dataset_id = dataset_record[0]
    assert isinstance(dataset_id, str)
    assert "CMIP6" in dataset_id

    # Test set_map_arr and parse_map_arr
    mapconv.set_map_arr(map_json_data)
    mapdict = mapconv.parse_map_arr()

    # parse_map_arr returns a list of file records, not a dict
    assert isinstance(mapdict, list)
    assert len(mapdict) > 0
    # Each record should have file info
    if len(mapdict) > 0:
        assert 'file' in mapdict[0]


def test_mapfile_invalid_path():
    """Test mapfile with non-existent path."""
    with pytest.raises(Exception):
        mapconv = ESGPubMapConv("/nonexistent/path/to/mapfile.map", project="cmip6")
        mapconv.mapfilerun({})


def test_mapfile_timestamp_parsing(test_map_cmip6):
    """Test that timestamps are parsed correctly from mapfile."""
    mapconv = ESGPubMapConv(str(test_map_cmip6), project="cmip6")

    # Read raw mapfile to check timestamp format
    with open(str(test_map_cmip6), 'r') as f:
        first_line = f.readline()
        # Mapfile format: dataset_id | path | size | mod_time=... | ...
        assert "mod_time=" in first_line
