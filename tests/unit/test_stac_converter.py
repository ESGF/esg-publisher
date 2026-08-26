"""Tests for esgcet.stac.stac_converter module."""
import pytest
import json
from datetime import datetime
from esgcet.stac.stac_converter import ESGSTACConverter, ESGSTACItem


@pytest.fixture
def stac_config():
    """Basic STAC configuration."""
    return {"stac_api": "https://esgf-stac.llnl.gov/api"}


@pytest.fixture
def cmip6_dataset_doc():
    """Sample CMIP6 dataset document."""
    return {
        "type": "Dataset",
        "instance_id": "CMIP6.DCPP.MRI.MRI-ESM2-0.dcppA-hindcast.s2017-r1i1p1f1.Amon.psl.gn.v20210114",
        "project": "CMIP6",
        "data_node": "esgf-node.ornl.gov",
        "pid": "hdl:21.14100/test-pid",
        "access": ["HTTPServer", "Globus"],
        "west_degrees": 0.0,
        "south_degrees": -90.0,
        "east_degrees": 360.0,
        "north_degrees": 90.0,
        "datetime_start": "2017-01-01T00:00:00Z",
        "datetime_end": "2027-12-31T23:59:59Z",
        "master_id": "CMIP6.DCPP.MRI.MRI-ESM2-0.dcppA-hindcast.s2017-r1i1p1f1.Amon.psl.gn",
        "activity_id": "DCPP",
        "institution_id": "MRI",
        "source_id": "MRI-ESM2-0",
        "experiment_id": "dcppA-hindcast",
        "member_id": "r1i1p1f1",
        "table_id": "Amon",
        "variable_id": "psl",
        "grid_label": "gn",
        "version": "v20210114",
        "citation_url": "https://doi.org/10.22033/ESGF/TEST"
    }


@pytest.fixture
def cmip6_file_doc():
    """Sample CMIP6 file document."""
    return {
        "type": "File",
        "title": "psl_Amon_MRI-ESM2-0_dcppA-hindcast_s2017-r1i1p1f1_gn_201701-202712.nc",
        "url": [
            "https://esgf-node.ornl.gov/thredds/fileServer/css03_data/CMIP6/DCPP/MRI/MRI-ESM2-0/dcppA-hindcast/s2017-r1i1p1f1/Amon/psl/gn/v20210114/psl_Amon_MRI-ESM2-0_dcppA-hindcast_s2017-r1i1p1f1_gn_201701-202712.nc|application/netcdf|HTTPServer"
        ],
        "size": 12345678,
        "checksum": "abcdef1234567890",
        "checksum_type": "SHA256",
        "tracking_id": "hdl:21.14100/test-file-pid",
        "timestamp": "2021-01-14T12:00:00Z"
    }


@pytest.fixture
def globus_file_doc():
    """Sample file document with Globus URL."""
    return {
        "type": "File",
        "title": "test_file.nc",
        "url": [
            "globus:1234abcd-5678-90ef-ghij-klmnopqrstuv/test/path/test_file.nc"
        ],
        "size": 987654,
        "checksum": "fedcba0987654321",
        "checksum_type": "SHA256",
        "tracking_id": "hdl:21.14100/test-globus-file",
        "timestamp": "2021-01-14T12:00:00Z"
    }


@pytest.fixture
def mip_drs7_dataset_doc():
    """Sample MIP-DRS7 (CMIP7) dataset document."""
    return {
        "type": "Dataset",
        "instance_id": "MIP-DRS7.CMIP7.CMIP.MOHC.UKESM1-0-LL.1pctCO2.r1i1p1f3.glb.mon.tas.tavg-h2m-hxy-u.g99.v20260123",
        "project": "mip-drs7",
        "data_node": "esgf-test.ceda.ac.uk",
        "pid": "hdl:21.14100/cmip7-test-pid",
        "access": ["HTTPServer"],
        "west_degrees": 0.0,
        "south_degrees": -90.0,
        "east_degrees": 360.0,
        "north_degrees": 90.0,
        "datetime_start": "1850-01-01T00:00:00Z",
        "datetime_end": "2150-12-31T23:59:59Z",
        "master_id": "MIP-DRS7.CMIP7.CMIP.MOHC.UKESM1-0-LL.1pctCO2.r1i1p1f3.glb.mon.tas.tavg-h2m-hxy-u.g99",
        "version": "v20260123"
    }


class TestESGSTACConverter:
    """Tests for ESGSTACConverter class."""

    def test_converter_initialization(self, stac_config):
        """Test STAC converter initialization."""
        converter = ESGSTACConverter(stac_config)
        assert converter.stac_api == "https://esgf-stac.llnl.gov/api"

    def test_converter_empty_config(self):
        """Test converter with empty config."""
        converter = ESGSTACConverter({})
        assert converter.stac_api == ""

    def test_citation_link_generation(self, stac_config):
        """Test citation link dictionary generation."""
        converter = ESGSTACConverter(stac_config)
        url = "https://doi.org/10.22033/ESGF/TEST"
        link = converter.citation_link_d(url)

        assert link["rel"] == "cite-as"
        assert link["type"] == "application/json"
        assert link["href"] == url

    def test_convert_cmip6_basic(self, stac_config, cmip6_dataset_doc, cmip6_file_doc):
        """Test basic CMIP6 dataset to STAC item conversion."""
        converter = ESGSTACConverter(stac_config)
        json_data = [cmip6_dataset_doc, cmip6_file_doc]

        item = converter.convert2stac(json_data)

        assert item is not None
        assert item["type"] == "Feature"
        assert item["stac_version"] == "1.1.0"
        assert item["id"] == cmip6_dataset_doc["instance_id"]
        assert item["collection"] == "CMIP6"

    def test_convert_cmip6_properties(self, stac_config, cmip6_dataset_doc, cmip6_file_doc):
        """Test CMIP6 properties are correctly mapped."""
        converter = ESGSTACConverter(stac_config)
        json_data = [cmip6_dataset_doc, cmip6_file_doc]

        item = converter.convert2stac(json_data)
        props = item["properties"]

        # Check datetime properties
        assert props["datetime"] is None
        assert props["start_datetime"] == "2017-01-01T00:00:00Z"
        assert props["end_datetime"] == "2027-12-31T23:59:59Z"

        # Check size calculation
        assert props["size"] == 12345678

        # Check standard properties
        assert "created" in props
        assert "updated" in props
        assert props["retracted"] is False

        # Check CMIP6 namespaced properties
        assert "cmip6:activity_id" in props
        assert props["cmip6:activity_id"] == "DCPP"

    def test_convert_cmip6_geometry(self, stac_config, cmip6_dataset_doc, cmip6_file_doc):
        """Test CMIP6 geometry and bbox calculation."""
        converter = ESGSTACConverter(stac_config)
        json_data = [cmip6_dataset_doc, cmip6_file_doc]

        item = converter.convert2stac(json_data)

        # CMIP6 shifts longitude by -180
        assert item["bbox"] == [-180.0, -90.0, 180.0, 90.0]

        # Check polygon geometry
        geometry = item["geometry"]
        assert geometry["type"] == "Polygon"
        coords = geometry["coordinates"][0]
        assert coords[0] == [-180.0, -90.0]  # southwest corner
        assert coords[2] == [180.0, 90.0]     # northeast corner

    def test_convert_cmip6_assets_http(self, stac_config, cmip6_dataset_doc, cmip6_file_doc):
        """Test HTTPServer asset creation."""
        converter = ESGSTACConverter(stac_config)
        json_data = [cmip6_dataset_doc, cmip6_file_doc]

        item = converter.convert2stac(json_data)
        assets = item["assets"]

        # Should have one HTTP asset named by file title
        filename = cmip6_file_doc["title"]
        assert filename in assets

        asset = assets[filename]
        assert asset["type"] == "application/netcdf"
        assert "https://esgf-node.ornl.gov" in asset["href"]
        assert asset["file:size"] == 12345678
        assert asset["file:checksum"] == "1220abcdef1234567890"  # Prefixed with 1220
        assert asset["alternate:name"] == "esgf-node.ornl.gov"
        assert asset["protocol"] == "https"

    def test_convert_globus_asset(self, stac_config, cmip6_dataset_doc, globus_file_doc):
        """Test Globus asset creation."""
        # Modify dataset to only have Globus access
        dataset = cmip6_dataset_doc.copy()
        dataset["access"] = ["Globus"]

        converter = ESGSTACConverter(stac_config)
        json_data = [dataset, globus_file_doc]

        item = converter.convert2stac(json_data)
        assets = item["assets"]

        assert "globus" in assets
        globus_asset = assets["globus"]
        assert globus_asset["type"] == "text/html"
        assert "https://app.globus.org/file-manager" in globus_asset["href"]
        assert "origin_id=1234abcd-5678-90ef-ghij-klmnopqrstuv" in globus_asset["href"]
        assert globus_asset["protocol"] == "globus"

    def test_convert_mip_drs7_to_cmip7(self, stac_config, mip_drs7_dataset_doc):
        """Test MIP-DRS7 project is converted to cmip7 collection."""
        # Add a file doc
        file_doc = {
            "type": "File",
            "title": "test.nc",
            "url": ["https://test.com/test.nc|application/netcdf|HTTPServer"],
            "size": 1000,
            "checksum": "abc123",
            "checksum_type": "SHA256",
            "timestamp": "2026-01-23T00:00:00Z"
        }

        converter = ESGSTACConverter(stac_config)
        json_data = [mip_drs7_dataset_doc, file_doc]

        item = converter.convert2stac(json_data)

        # Collection should be cmip7, not mip-drs7
        assert item["collection"] == "cmip7"

    def test_convert_links(self, stac_config, cmip6_dataset_doc, cmip6_file_doc):
        """Test STAC item links are correctly generated."""
        converter = ESGSTACConverter(stac_config)
        json_data = [cmip6_dataset_doc, cmip6_file_doc]

        item = converter.convert2stac(json_data)
        links = item["links"]

        # Check for required link relations
        link_rels = [link["rel"] for link in links]
        assert "self" in link_rels
        assert "parent" in link_rels
        assert "collection" in link_rels
        assert "root" in link_rels
        assert "cite-as" in link_rels  # From citation_url

    def test_convert_citation_link(self, stac_config, cmip6_dataset_doc, cmip6_file_doc):
        """Test citation URL is added as cite-as link."""
        converter = ESGSTACConverter(stac_config)
        json_data = [cmip6_dataset_doc, cmip6_file_doc]

        item = converter.convert2stac(json_data)

        cite_links = [l for l in item["links"] if l["rel"] == "cite-as"]
        assert len(cite_links) == 1
        assert cite_links[0]["href"] == "https://doi.org/10.22033/ESGF/TEST"

    def test_convert_no_assets_returns_none(self, stac_config, cmip6_dataset_doc):
        """Test that conversion returns None if no assets can be created."""
        # Dataset with no file documents
        converter = ESGSTACConverter(stac_config)
        json_data = [cmip6_dataset_doc]

        item = converter.convert2stac(json_data)

        assert item is None

    def test_convert_rejects_non_sha256_checksum(self, stac_config, cmip6_dataset_doc, cmip6_file_doc):
        """Test that non-SHA256 file checksums are rejected."""
        file_doc = cmip6_file_doc.copy()
        file_doc["checksum_type"] = "MD5"

        converter = ESGSTACConverter(stac_config)

        with pytest.raises(RuntimeError, match="MD5 not supported"):
            converter.convert2stac([cmip6_dataset_doc, file_doc])

    def test_convert_omits_none_properties_and_collapses_lists(
        self, stac_config, cmip6_dataset_doc, cmip6_file_doc
    ):
        """Test list handling and None omission in STAC properties."""
        dataset = cmip6_dataset_doc.copy()
        dataset["institution_id"] = ["MRI"]
        dataset["nominal_resolution"] = None

        converter = ESGSTACConverter(stac_config)
        item = converter.convert2stac([dataset, cmip6_file_doc])
        props = item["properties"]

        assert props["cmip6:institution_id"] == "MRI"
        assert "cmip6:nominal_resolution" not in props

    def test_convert_wraps_longitudes_after_cmip_shift(
        self, stac_config, cmip6_dataset_doc, cmip6_file_doc
    ):
        """Test longitude normalization after CMIP coordinate shift."""
        dataset = cmip6_dataset_doc.copy()
        dataset["west_degrees"] = 400.0
        dataset["east_degrees"] = 500.0

        converter = ESGSTACConverter(stac_config)
        item = converter.convert2stac([dataset, cmip6_file_doc])

        assert item["bbox"] == [-140.0, -90.0, -40.0, 90.0]

    def test_convert_default_datetime(self, stac_config, cmip6_file_doc):
        """Test default datetime when start/end not provided."""
        # Dataset without datetime_start/datetime_end
        dataset = {
            "type": "Dataset",
            "instance_id": "test.dataset",
            "project": "CMIP6",
            "data_node": "test.node",
            "access": ["HTTPServer"],
            "west_degrees": 0.0,
            "south_degrees": -90.0,
            "east_degrees": 360.0,
            "north_degrees": 90.0
        }

        converter = ESGSTACConverter(stac_config)
        json_data = [dataset, cmip6_file_doc]

        item = converter.convert2stac(json_data)
        props = item["properties"]

        # Should use default values
        assert props["start_datetime"] == "1850-01-01T00:00:00Z"
        assert props["end_datetime"] == "1850-01-01T00:00:01Z"

    def test_convert_copies_reference_file_asset(
        self, stac_config, cmip6_dataset_doc, cmip6_file_doc
    ):
        """Test reference file assets are copied from the dataset document."""
        dataset = cmip6_dataset_doc.copy()
        dataset["reference_file"] = {
            "href": "https://test.com/reference.zarr",
            "type": "application/zarr",
        }

        converter = ESGSTACConverter(stac_config)
        item = converter.convert2stac([dataset, cmip6_file_doc])

        assert item["assets"]["reference_file"] == dataset["reference_file"]


class TestESGSTACItem:
    """Tests for ESGSTACItem class."""

    @pytest.fixture
    def sample_stac_item(self):
        """Sample STAC item for testing."""
        return {
            "id": "test.item.id",
            "type": "Feature",
            "assets": {
                "data0001.nc": {
                    "href": "https://test.com/data0001.nc",
                    "type": "application/netcdf",
                    "file:local_path": "test/path/data0001.nc",
                    "alternate:name": "original.node"
                },
                "globus": {
                    "href": "https://app.globus.org/file-manager?origin_id=test",
                    "type": "text/html",
                    "file:local_path": "test/path",
                    "alternate:name": "original.node"
                }
            }
        }

    def test_stac_item_initialization(self, sample_stac_item):
        """Test ESGSTACItem initialization."""
        stac_item = ESGSTACItem(sample_stac_item)
        assert stac_item.stac_item == sample_stac_item

    def test_stac_item_none_initialization(self):
        """Test ESGSTACItem with None sets stac_item to None."""
        # Callers should check before creating ESGSTACItem, but if they don't,
        # the object should still be valid with stac_item=None
        stac_item = ESGSTACItem(None)
        assert stac_item.stac_item is None

    def test_add_replica_operation(self, sample_stac_item):
        """Test adding replica operations."""
        stac_item = ESGSTACItem(sample_stac_item)

        rep_datanode = "replica.node"
        template = "https://replica.com/{}/{}"
        prefix = "data"

        operations = stac_item.add_replica(rep_datanode, template, prefix)

        # Should generate operations for each non-reference_file asset
        assert len(operations) > 0

        # Check operation structure
        op = operations[0]
        assert op["op"] == "add"
        assert "path" in op
        assert "value" in op
        assert rep_datanode in op["path"]

    def test_add_aggregate_new(self, sample_stac_item):
        """Test adding new aggregate asset."""
        # Remove reference_file if present
        if "reference_file" in sample_stac_item["assets"]:
            del sample_stac_item["assets"]["reference_file"]

        stac_item = ESGSTACItem(sample_stac_item)

        aggtype = "zarr"
        url = "https://test.com/aggregate.zarr"
        site = "test.site"

        operations = stac_item.add_aggregate(aggtype, url, site)

        assert len(operations) == 1
        op = operations[0]
        assert op["op"] == "add"
        assert op["path"] == "/assets/reference_file"
        assert op["value"]["href"] == url
        assert op["value"]["type"] == "application/zarr"
        assert "virtual" in op["value"]["role"]

    def test_remove_aggregate(self, sample_stac_item):
        """Test removing aggregate asset."""
        # Add a reference_file to test removal
        sample_stac_item["assets"]["reference_file"] = {
            "href": "https://test.com/ref.zarr",
            "alternate:name": "test.site"
        }

        stac_item = ESGSTACItem(sample_stac_item)

        operations = stac_item.remove_aggregate("test.site")

        assert len(operations) == 1
        op = operations[0]
        assert op["op"] == "remove"
        assert "reference_file" in op["path"]

    def test_remove_aggregate_alternate_site(self, sample_stac_item):
        """Test removing one alternate aggregate asset site."""
        sample_stac_item["assets"]["reference_file"] = {
            "href": "https://test.com/ref.zarr",
            "alternate:name": "primary.site",
            "alternate": {
                "replica.site": {
                    "href": "https://replica.com/ref.zarr",
                    "type": "application/zarr",
                }
            },
        }

        stac_item = ESGSTACItem(sample_stac_item)
        operations = stac_item.remove_aggregate("replica.site")

        assert operations == [
            {
                "op": "remove",
                "path": "/assets/reference_file/alternate/replica.site",
            }
        ]

    def test_add_aggregate_as_alternate_when_reference_exists(self, sample_stac_item):
        """Test adding an aggregate site when reference_file already exists."""
        sample_stac_item["assets"]["reference_file"] = {
            "href": "https://test.com/ref.zarr",
            "alternate:name": "primary.site",
        }

        stac_item = ESGSTACItem(sample_stac_item)
        operations = stac_item.add_aggregate(
            "zarr", "https://replica.com/ref.zarr", "replica.site"
        )

        assert len(operations) == 1
        op = operations[0]
        assert op["op"] == "add"
        assert op["path"] == "/assets/reference_file/alternate/replica.site"
        assert op["value"]["href"] == "https://replica.com/ref.zarr"
        assert op["value"]["alternate:name"] == "replica.site"

    def test_add_replica_skips_reference_matching_and_existing_alternates(self):
        """Test replica operations skip assets that should not be duplicated."""
        item = {
            "id": "test.item.id",
            "assets": {
                "reference_file": {
                    "href": "https://test.com/ref.zarr",
                    "type": "application/zarr",
                },
                "same-node.nc": {
                    "href": "https://replica.com/same-node.nc",
                    "type": "application/netcdf",
                    "file:local_path": "test/path/same-node.nc",
                    "alternate:name": "replica.node",
                },
                "existing-alt.nc": {
                    "href": "https://test.com/existing-alt.nc",
                    "type": "application/netcdf",
                    "file:local_path": "test/path/existing-alt.nc",
                    "alternate:name": "original.node",
                    "alternate": {"replica.node": {}},
                },
            },
        }

        operations = ESGSTACItem(item).add_replica(
            "replica.node", "https://replica.com/{}/{}", "data"
        )

        assert operations == []

    def test_add_replica_adds_globus_when_endpoint_provided(self, sample_stac_item):
        """Test adding a Globus replica asset when a replica endpoint is provided."""
        stac_item = ESGSTACItem(sample_stac_item)

        operations = stac_item.add_replica(
            "replica.node",
            "https://replica.com/{}/{}",
            "data",
            rep_globus="replica-endpoint",
        )

        globus_ops = [op for op in operations if op["path"] == "/assets/globus/alternate/replica.node"]
        assert len(globus_ops) == 1
        assert globus_ops[0]["value"]["href"] == (
            "https://app.globus.org/file-manager?"
            "origin_id=replica-endpoint&origin_path=test/path"
        )
