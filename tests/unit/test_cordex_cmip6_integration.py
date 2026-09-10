"""Integration test for CORDEX-CMIP6: NetCDF → dataset record → STAC item."""
import pytest
from unittest.mock import patch


def test_cordex_cmip6_netcdf_to_stac_integration(data_dir):
    """Test full pipeline: CORDEX-CMIP6 NetCDF → xarray scan → STAC conversion.

    This test validates that the combined mk_dataset_xarray and stac_converter
    modules produce repeatable results with correct spatial bounds from
    rotated pole coordinates.
    """
    from esgcet.args import PublisherArgs
    from esgcet.generic_netcdf import GenericPublisher
    from esgcet.stac.stac_converter import ESGSTACConverter

    # Mapfile path
    mapfile = data_dir / "CORDEX-CMIP6/CORDEX-CMIP6.DD.NAM-25.CCCma.CanESM5-1.historical.r1i1p1f2.CanRCM5-SN.v1-r2.mon.tas.v20260903.map"

    # Setup args dict following test_generic_netcdf.py pattern
    with patch("sys.argv", ["prog", "--map", str(mapfile)]):
        argdict = PublisherArgs().get_dict("CORDEX-CMIP6")

    argdict['fullmap'] = str(mapfile)
    argdict['mountpoints'] = {}
    argdict['data_roots'] = {str(data_dir / "CORDEX-CMIP6"): 'test_esg_dataroot'}
    argdict['data_node'] = 'test.data.node'
    argdict['index_node'] = 'test.index.node'

    # Create publisher and generate records
    generic_pub = GenericPublisher(argdict)
    map_json = generic_pub.mapfile()
    generic_pub.extract_method(map_json)
    records = generic_pub.mk_dataset(map_json)

    # Last record is the dataset
    dataset_record = records[-1]
    assert dataset_record["type"] == "Dataset"
    assert dataset_record["project"] == "CORDEX-CMIP6"

    # Verify spatial bounds were extracted (ground truth from rotated pole coords)
    assert "west_degrees" in dataset_record
    assert "south_degrees" in dataset_record
    assert "east_degrees" in dataset_record
    assert "north_degrees" in dataset_record

    # Ground truth: spatial bounds from 5x5 CORDEX-CMIP6 fixture
    # These values come from the actual file's rotated pole coordinates
    # transformed to WGS84
    assert dataset_record["west_degrees"] == pytest.approx(-127.579, rel=1e-3)
    assert dataset_record["south_degrees"] == pytest.approx(12.398, rel=1e-3)
    assert dataset_record["east_degrees"] == pytest.approx(-126.478, rel=1e-3)
    assert dataset_record["north_degrees"] == pytest.approx(13.522, rel=1e-3)

    # Convert to STAC
    stac_config = {"stac_api": "https://esgf-stac.llnl.gov/api"}
    converter = ESGSTACConverter(stac_config)
    stac_item = converter.convert2stac(records)

    # Verify STAC item was created
    assert stac_item is not None, "STAC conversion returned None"
    assert stac_item["type"] == "Feature"
    assert stac_item["stac_version"] == "1.1.0"

    # Verify STAC bbox matches dataset bounds (reproducibility check)
    bbox = stac_item["bbox"]
    assert len(bbox) == 4
    assert bbox[0] == pytest.approx(dataset_record["west_degrees"], rel=1e-6)
    assert bbox[1] == pytest.approx(dataset_record["south_degrees"], rel=1e-6)
    assert bbox[2] == pytest.approx(dataset_record["east_degrees"], rel=1e-6)
    assert bbox[3] == pytest.approx(dataset_record["north_degrees"], rel=1e-6)

    # Verify geometry is valid GeoJSON
    geom = stac_item["geometry"]
    assert geom["type"] == "Polygon"
    coords = geom["coordinates"][0]
    assert len(coords) == 5  # Closed polygon
    assert coords[0] == coords[-1]  # First equals last

    # Verify CORDEX-CMIP6 properties are preserved
    # Note: properties may have various prefixes depending on STAC converter configuration
    props = stac_item["properties"]
    # Check that key CORDEX-CMIP6 facets are present somewhere in properties
    prop_keys = list(props.keys())
    assert any("domain_id" in k for k in prop_keys), f"domain_id not found in props: {prop_keys}"
    assert any("institution_id" in k for k in prop_keys), f"institution_id not found in props"
    assert any("driving_source_id" in k for k in prop_keys), f"driving_source_id not found in props"
    assert any("source_id" in k for k in prop_keys), f"source_id not found in props"
    assert any("variable_id" in k for k in prop_keys), f"variable_id not found in props"

    # Verify temporal extent
    assert "start_datetime" in props
    assert "end_datetime" in props

    # The critical assertion: spatial bounds from rotated pole coords match STAC output
    print(f"\n✓ CORDEX-CMIP6 rotated pole coords correctly transformed to WGS84 bbox")
    print(f"  Dataset: W={dataset_record['west_degrees']:.3f}, S={dataset_record['south_degrees']:.3f}, E={dataset_record['east_degrees']:.3f}, N={dataset_record['north_degrees']:.3f}")
    print(f"  STAC:    W={bbox[0]:.3f}, S={bbox[1]:.3f}, E={bbox[2]:.3f}, N={bbox[3]:.3f}")
