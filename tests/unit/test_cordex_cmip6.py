"""Tests for CORDEX-CMIP6 project support."""
import pytest


class FakeHandler:
    """Small scan handler test double for CORDEX-CMIP6 tests."""

    def __init__(self, publog):
        self.publog = publog

    def get_attrs_dict(self, scanobj):
        return scanobj.get("attrs", {})


def test_cordex_cmip6_dataset_id_parsing():
    """Test CORDEX-CMIP6 dataset ID is parsed correctly according to DRS."""
    from esgcet.scan.mk_dataset import ESGPubMakeDataset

    # DRS: ["collection", "activity_drs", "domain_id", "institution_id",
    #       "driving_source_id", "driving_experiment_id", "driving_variant_label",
    #       "source_id", "version_realization", "frequency", "variable_id"]
    dataset_id = "CORDEX-CMIP6.DD.NAM-25.CCCma.CanESM5-1.historical.r1i1p1f2.CanRCM5-SN.v1-r2.mon.tas.v20260903"

    mkd = ESGPubMakeDataset(
        data_node="test.node",
        index_node="index.node",
        replica=False,
        globus="none",
        data_roots={"/test": "test_root"},
        https=None,
        handler_class=FakeHandler,
    )

    mkd.get_dataset(dataset_id, {"attrs": {}})

    # Verify DRS facets are populated
    assert mkd.dataset["collection"] == "CORDEX-CMIP6"
    assert mkd.dataset["activity_drs"] == "DD"
    assert mkd.dataset["domain_id"] == "NAM-25"
    assert mkd.dataset["institution_id"] == "CCCma"
    assert mkd.dataset["driving_source_id"] == "CanESM5-1"
    assert mkd.dataset["driving_experiment_id"] == "historical"
    assert mkd.dataset["driving_variant_label"] == "r1i1p1f2"
    assert mkd.dataset["source_id"] == "CanRCM5-SN"
    assert mkd.dataset["version_realization"] == "v1-r2"
    assert mkd.dataset["frequency"] == "mon"
    assert mkd.dataset["variable_id"] == "tas"
    assert mkd.dataset["version"] == "20260903"
    assert mkd.dataset["project"] == "CORDEX-CMIP6"


def test_cordex_cmip6_accepts_hash_version_format():
    """Test CORDEX-CMIP6 accepts dataset ID with hash-separated version."""
    from esgcet.scan.mk_dataset import ESGPubMakeDataset

    dataset_id = "CORDEX-CMIP6.DD.NAM-25.CCCma.CanESM5-1.historical.r1i1p1f2.CanRCM5-SN.v1-r2.mon.tas#20260903"

    mkd = ESGPubMakeDataset(
        data_node="test.node",
        index_node="index.node",
        replica=False,
        globus="none",
        data_roots={"/test": "test_root"},
        https=None,
        handler_class=FakeHandler,
    )

    mkd.get_dataset(dataset_id, {"attrs": {}})

    assert mkd.dataset["version"] == "20260903"
    assert mkd.dataset["variable_id"] == "tas"
