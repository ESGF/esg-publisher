"""Backward compatibility tests to ensure old import paths still work."""
import pytest


def test_old_project_imports():
    """Verify old project-related import paths still work."""
    from esgcet.generic_pub import BasePublisher
    from esgcet.generic_netcdf import GenericPublisher
    from esgcet.handler_base import ESGPubHandlerBase
    from esgcet.pub_internal import PubRunner
    from esgcet.pid_cite_pub import ESGPubPidCite

    # If we get here, all imports worked
    assert BasePublisher is not None
    assert GenericPublisher is not None
    assert ESGPubHandlerBase is not None
    assert PubRunner is not None
    assert ESGPubPidCite is not None


def test_old_solr_imports():
    """Verify old Solr backend import paths still work."""
    from esgcet.index_pub import ESGPubIndex
    from esgcet.pub_client import publisherClient
    from esgcet.search_check import ESGSearchCheck

    assert ESGPubIndex is not None
    assert publisherClient is not None
    assert ESGSearchCheck is not None


def test_old_stac_imports():
    """Verify old STAC backend import paths still work."""
    from esgcet.stac_client import getTransactionClient, GlobusTransactionClient, EGITransactionClient
    from esgcet.stac_converter import ESGSTACConverter

    assert getTransactionClient is not None
    assert GlobusTransactionClient is not None
    assert EGITransactionClient is not None
    assert ESGSTACConverter is not None


def test_old_globus_imports():
    """Verify old Globus backend import paths still work."""
    from esgcet.globus_search import GlobusSearchIngest
    from esgcet.globus_query import ESGGlobusQuery

    assert GlobusSearchIngest is not None
    assert ESGGlobusQuery is not None


def test_old_scan_imports():
    """Verify old scan (mk_dataset) import paths still work."""
    from esgcet.mk_dataset import ESGPubMakeDataset
    from esgcet.mk_dataset_autoc import ESGPubAutocHandler
    from esgcet.mk_dataset_xarray import ESGPubXArrayHandler
    from esgcet.mk_dataset_nc4 import ESGPubNC4Handler

    assert ESGPubMakeDataset is not None
    assert ESGPubAutocHandler is not None
    assert ESGPubXArrayHandler is not None
    assert ESGPubNC4Handler is not None


def test_old_util_imports():
    """Verify old utility import paths still work."""
    from esgcet.logger import ESGPubLogger
    from esgcet.args import PublisherArgs
    from esgcet.mapfile import ESGPubMapConv
    import esgcet.settings

    assert ESGPubLogger is not None
    assert PublisherArgs is not None
    assert ESGPubMapConv is not None
    assert esgcet.settings is not None


def test_new_project_imports():
    """Verify new project import paths work."""
    from esgcet.project.generic_pub import BasePublisher
    from esgcet.project.generic_netcdf import GenericPublisher
    from esgcet.scan.handler_base import ESGPubHandlerBase  # handler_base is in scan, not project
    from esgcet.pub_internal import PubRunner  # pub_internal stays at root
    from esgcet.util.pid_cite_pub import ESGPubPidCite  # pid_cite_pub is in util

    assert BasePublisher is not None
    assert GenericPublisher is not None
    assert ESGPubHandlerBase is not None
    assert PubRunner is not None
    assert ESGPubPidCite is not None


def test_new_solr_imports():
    """Verify new Solr import paths work."""
    from esgcet.solr.index_pub import ESGPubIndex
    from esgcet.solr.pub_client import publisherClient
    from esgcet.solr.search_check import ESGSearchCheck

    assert ESGPubIndex is not None
    assert publisherClient is not None
    assert ESGSearchCheck is not None


def test_new_stac_imports():
    """Verify new STAC import paths work."""
    from esgcet.stac.stac_client import getTransactionClient, GlobusTransactionClient, EGITransactionClient
    from esgcet.stac.stac_converter import ESGSTACConverter

    assert getTransactionClient is not None
    assert GlobusTransactionClient is not None
    assert EGITransactionClient is not None
    assert ESGSTACConverter is not None


def test_new_globus_imports():
    """Verify new Globus import paths work."""
    from esgcet.globus.globus_search import GlobusSearchIngest
    from esgcet.globus.globus_query import ESGGlobusQuery

    assert GlobusSearchIngest is not None
    assert ESGGlobusQuery is not None


def test_new_scan_imports():
    """Verify new scan import paths work."""
    from esgcet.scan.mk_dataset import ESGPubMakeDataset
    from esgcet.scan.mk_dataset_autoc import ESGPubAutocHandler
    from esgcet.scan.mk_dataset_xarray import ESGPubXArrayHandler
    from esgcet.scan.mk_dataset_nc4 import ESGPubNC4Handler

    assert ESGPubMakeDataset is not None
    assert ESGPubAutocHandler is not None
    assert ESGPubXArrayHandler is not None
    assert ESGPubNC4Handler is not None


def test_new_util_imports():
    """Verify new utility import paths work."""
    from esgcet.util.logger import ESGPubLogger
    from esgcet.util.args import PublisherArgs
    from esgcet.util.mapfile import ESGPubMapConv
    from esgcet.util import settings

    assert ESGPubLogger is not None
    assert PublisherArgs is not None
    assert ESGPubMapConv is not None
    assert settings is not None
