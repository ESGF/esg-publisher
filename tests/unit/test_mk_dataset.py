"""Tests for esgcet.scan.mk_dataset module."""
import pytest

from esgcet.scan.mk_dataset import ESGPubMakeDataset


class FakeHandler:
    """Small scan handler test double for metadata helper tests."""

    def __init__(self, publog):
        self.publog = publog

    def get_attrs_dict(self, scanobj):
        return scanobj.get("attrs", {})

    def get_variables(self, scanobj):
        return scanobj["variables"]

    def get_variable_list(self, variables):
        return list(variables)

    def set_bounds(self, record, scanobj):
        record["west_degrees"] = scanobj.get("west_degrees", -180.0)
        record["east_degrees"] = scanobj.get("east_degrees", 180.0)


def make_dataset(**kwargs):
    """Create an ESGPubMakeDataset with defaults suitable for unit tests."""
    defaults = {
        "data_node": "data.node",
        "index_node": "index.node",
        "replica": False,
        "globus": "globus-endpoint",
        "data_roots": {"/data": "test_root"},
        "https": None,
        "handler_class": FakeHandler,
    }
    defaults.update(kwargs)
    return ESGPubMakeDataset(**defaults)


def test_normalize_path_finds_matching_data_root():
    """Test relative path extraction from configured data roots."""
    rel_path, proj_root = ESGPubMakeDataset.normalize_path(
        "/data/CMIP6/test.nc", {"/data": "test_root"}
    )

    assert rel_path == "CMIP6/test.nc"
    assert proj_root == "/data"


def test_normalize_path_rejects_unmapped_path():
    """Test paths outside configured data roots are rejected."""
    with pytest.raises(BaseException, match="File Path does not match"):
        ESGPubMakeDataset.normalize_path(
            "/other/CMIP6/test.nc", {"/data": "test_root"}
        )


def test_format_template_handles_skip_custom_https_and_globus():
    """Test URL template handling for skipped, custom, and Globus templates."""
    mkd = make_dataset(https="https://custom.example/{}/{}", skip_opendap=True)

    assert mkd.format_template(
        "https://{}/thredds/dodsC/{}/{}|application/opendap-html|OPENDAP",
        "root",
        "path/file.nc",
    ) is None
    assert mkd.format_template(
        "https://{}/thredds/fileServer/{}/{}|application/netcdf|HTTPServer",
        "root",
        "path/file.nc",
    ) == "https://custom.example/root/path/file.nc"
    assert mkd.format_template(
        "globus:{}/{}/{}|Globus|Globus", "root", "path/file.nc"
    ) == "globus:globus-endpoint/root/path/file.nc|Globus|Globus"

    mkd_no_globus = make_dataset(globus="none")
    assert mkd_no_globus.format_template(
        "globus:{}/{}/{}|Globus|Globus", "root", "path/file.nc"
    ) is None


def test_global_attributes_splits_delimited_fields():
    """Test global attributes copy scalar fields and split configured list fields."""
    mkd = make_dataset()
    mkd.init_project("cmip6")
    mkd.global_attributes(
        "cmip6",
        {
            "title": "test dataset",
            "source_type": "AOGCM BGC",
            "activity_id": "DCPP ScenarioMIP",
        },
    )

    assert mkd.dataset["title"] == "test dataset"
    assert mkd.dataset["source_type"] == ["AOGCM", "BGC"]
    assert mkd.dataset["activity_id"] == ["DCPP", "ScenarioMIP"]


def test_global_attr_mapped_renames_present_attributes():
    """Test configured global attribute mappings are copied under target names."""
    mkd = make_dataset()
    mkd.global_attr_mapped("cmip6", {"experiment": "Decadal prediction"})

    assert mkd.dataset["experiment_title"] == "Decadal prediction"


def test_global_attr_mapped_warns_when_source_attribute_missing():
    """Test missing mapped attrs warn instead of raising an UnboundLocalError."""
    mkd = make_dataset()

    mkd.global_attr_mapped("cmip6", {})

    assert "experiment_title" not in mkd.dataset


def test_set_variables_uses_selected_variable_metadata():
    """Test variable metadata is copied for the requested variable."""
    mkd = make_dataset()
    record = {"variable_id": "tas"}
    scanobj = {
        "variables": {
            "tas": {
                "long_name": "Near-Surface Air Temperature",
                "standard_name": "air_temperature",
                "units": "K",
            }
        }
    }

    mkd.set_variables(record, scanobj)

    assert record["variable_long_name"] == "Near-Surface Air Temperature"
    assert record["cf_standard_name"] == "air_temperature"
    assert record["variable_units"] == "K"
    assert record["variable"] == "tas"


def test_set_variables_summarizes_multiple_variables():
    """Test fallback metadata when the requested variable is absent."""
    mkd = make_dataset()
    record = {"variable_id": "Multiple"}
    scanobj = {
        "variables": {
            "tas": {
                "long_name": "Near-Surface Air Temperature",
                "standard_name": "air_temperature",
                "units": "K",
            },
            "time_bounds": {
                "long_name": "time bounds",
                "standard_name": "",
                "units": "1",
            },
            "pr": {
                "info": "Precipitation",
                "standard_name": "precipitation_flux",
                "units": "kg m-2 s-1",
            },
        }
    }

    mkd.set_variables(record, scanobj)

    assert record["variable_id"] == "Multiple"
    assert record["variable"] == "Multiple"
    assert sorted(record["variable_long_name"]) == [
        "Near-Surface Air Temperature",
        "Precipitation",
    ]
    assert sorted(record["cf_standard_name"]) == [
        "air_temperature",
        "precipitation_flux",
    ]
    assert sorted(record["variable_units"]) == ["K", "kg m-2 s-1"]


def test_init_project_uses_custom_project_configuration():
    """Test user-defined projects can provide DRS, constants, and global attrs."""
    mkd = make_dataset(
        user_project={
            "custom": {
                "DRS": ["project", "variable_id"],
                "CONST_ATTR": {"product": "custom-output"},
                "GA": ["title"],
            }
        }
    )

    mkd.init_project("custom")

    assert mkd.DRS == ["project", "variable_id"]
    assert mkd.CONST_ATTR == {"product": "custom-output"}
    assert mkd.GA == {"custom": ["title"]}
    assert mkd.dataset["project"] == "custom"


def test_init_project_clones_existing_project_configuration():
    """Test user projects can clone stock DRS and override constants."""
    mkd = make_dataset(
        user_project={
            "clone_project": "cmip6",
            "custom": {"CONST_ATTR": {"product": "custom-output"}},
        }
    )

    mkd.init_project("custom")

    assert mkd.DRS[0] == "mip_era"
    assert mkd.CONST_ATTR["model_cohort"] == "Registered"
    assert mkd.CONST_ATTR["product"] == "custom-output"
    assert mkd.dataset["project"] == "custom"


def test_init_project_rejects_unknown_project():
    """Test an unknown project without user configuration is rejected."""
    mkd = make_dataset()

    with pytest.raises(BaseException, match="DRS.*not defined"):
        mkd.init_project("unknown")


def test_load_xattr_reads_json_and_keeps_existing_cache(tmp_path):
    """Test xattr JSON is loaded once and cached."""
    xattr = tmp_path / "xattr.json"
    xattr.write_text('{"tracking_project": "CMIP6"}')
    mkd = make_dataset()

    mkd.load_xattr(str(xattr))
    assert mkd.xattr == {"tracking_project": "CMIP6"}

    xattr.write_text('{"tracking_project": "changed"}')
    mkd.load_xattr(str(xattr))
    assert mkd.xattr == {"tracking_project": "CMIP6"}


def test_xattr_handler_returns_loaded_attributes():
    """Test the base xattr handler returns the loaded attribute dictionary."""
    mkd = make_dataset()
    mkd.xattr = {"tracking_project": "CMIP6"}

    assert mkd.xattr_handler() == {"tracking_project": "CMIP6"}


def test_get_dataset_accepts_dot_v_version_identifier():
    """Test .v dataset IDs are split into master_id and version."""
    mkd = make_dataset()
    mapdata = (
        "CMIP6.DCPP.MRI.MRI-ESM2-0.dcppA-hindcast."
        "s2017-r1i1p1f1.Amon.psl.gn.v20210114"
    )

    mkd.get_dataset(mapdata, {"attrs": {"experiment": "Decadal prediction"}})

    assert mkd.dataset["master_id"] == (
        "CMIP6.DCPP.MRI.MRI-ESM2-0.dcppA-hindcast."
        "s2017-r1i1p1f1.Amon.psl.gn"
    )
    assert mkd.dataset["version"] == "20210114"
    assert mkd.dataset["instance_id"] == mapdata


def test_get_dataset_uses_clone_project_for_global_attributes():
    """Test cloned projects read global attrs from the source project settings."""
    mkd = make_dataset(
        user_project={
            "clone_project": "cmip6",
            "custom": {"CONST_ATTR": {"project": "custom"}},
        }
    )
    mapdata = (
        "custom.DCPP.MRI.MRI-ESM2-0.dcppA-hindcast."
        "s2017-r1i1p1f1.Amon.psl.gn.v20210114"
    )

    mkd.get_dataset(
        mapdata,
        {
            "attrs": {
                "experiment": "Decadal prediction",
                "source_type": "AOGCM BGC",
                "activity_id": "DCPP ScenarioMIP",
            }
        },
    )

    assert mkd.dataset["project"] == "custom"
    assert mkd.dataset["source_type"] == ["AOGCM", "BGC"]
    assert mkd.dataset["activity_id"] == ["DCPP", "ScenarioMIP"]


def test_get_dataset_can_disable_further_info_url():
    """Test configured further_info_url metadata can be removed."""
    mkd = make_dataset(
        user_project={
            "custom": {
                "DRS": ["project", "variable_id"],
                "CONST_ATTR": {},
                "GA": ["further_info_url"],
            }
        },
        disable_further_info=True,
    )

    mkd.get_dataset(
        "custom.tas.v20200101",
        {"attrs": {"further_info_url": "https://furtherinfo.example/test"}},
    )

    assert "further_info_url" not in mkd.dataset


def test_get_dataset_rejects_invalid_version_identifier():
    """Test dataset IDs without a v-prefixed version are rejected."""
    mkd = make_dataset()

    with pytest.raises(ValueError, match="not a valid version identifier"):
        mkd.get_dataset("CMIP6.bad.version.not-a-version", {})


def test_set_variables_uses_info_when_long_name_missing():
    """Test selected variable metadata can use the info field as long_name."""
    mkd = make_dataset()
    record = {"variable_id": "pr"}
    scanobj = {
        "variables": {
            "pr": {
                "info": "Precipitation",
                "standard_name": "precipitation_flux",
                "units": "kg m-2 s-1",
            }
        }
    }

    mkd.set_variables(record, scanobj)

    assert record["variable_long_name"] == "Precipitation"
    assert record["cf_standard_name"] == "precipitation_flux"
    assert record["variable_units"] == "kg m-2 s-1"


def test_get_file_rejects_duplicate_tracking_id():
    """Test duplicate tracking IDs terminate file-record creation."""
    mkd = make_dataset()
    mkd.dataset = {
        "id": "dataset|data.node",
        "instance_id": "dataset.v20200101",
        "master_id": "dataset",
    }
    mkd.tracking_id_set.add("hdl:test")

    with pytest.raises(SystemExit):
        mkd.get_file({"file": "/data/file.nc"}, {"tracking_id": "hdl:test"})


def test_get_file_handles_trailing_slash_data_root_and_no_file_count():
    """Test file records normalize roots with trailing slashes."""
    mkd = make_dataset(data_roots={"/archive/CMIP6/": "mapped_root"})
    mkd.first_val = "CMIP6"
    mkd.dataset = {
        "id": "dataset|data.node",
        "instance_id": "dataset.v20200101",
        "master_id": "dataset",
    }

    record = mkd.get_file(
        {
            "file": "/archive/CMIP6/path/file.nc",
            "size": 10,
            "checksum": "abc123",
            "checksum_type": "SHA256",
        },
        {},
    )

    assert record["title"] == "file.nc"
    assert record["publish_path"] == "mapped_root/path/file.nc"
    assert record["url"] == [
        "https://data.node/thredds/fileServer/mapped_root/path/file.nc|application/netcdf|HTTPServer",
        "globus:globus-endpoint/mapped_root/path/file.nc|Globus|Globus",
    ]
    assert mkd.base_path == "mapped_root/path/file.nc"
