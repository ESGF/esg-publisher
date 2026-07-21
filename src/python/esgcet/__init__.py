"""
ESGF Publisher (esgcet) - Publishing tools for ESGF data nodes.

This package provides tools for publishing datasets to ESGF infrastructure
including Solr indexes, STAC catalogs, and Globus Search.
"""

from importlib.metadata import version

project = 'esgcet'
__version__ = str(version(project))

# =============================================================================
# Backward Compatibility Layer
# =============================================================================
# These re-exports maintain backward compatibility with code that imports
# from the old flat structure. All imports below will continue to work after
# the directory reorganization.
#
# New code should import from the specific subdirectories:
#   - esgcet.project.* for project handlers and core framework
#   - esgcet.solr.* for Solr backend
#   - esgcet.stac.* for STAC backend
#   - esgcet.globus.* for Globus backend
#   - esgcet.mk_dataset.* for dataset creation
#   - esgcet.util.* for utilities
# =============================================================================

# NOTE: These imports will work once files are moved.
# Before moving files, this will cause import errors - that's expected.
# The import errors will resolve as files are moved to their new locations.

try:
    # Project handlers and core framework
    from esgcet.project.generic_pub import BasePublisher
    from esgcet.project.generic_netcdf import GenericPublisher
    from esgcet.project.cmip5 import cmip5
    from esgcet.project.cmip6 import cmip6
    from esgcet.project.e3sm import e3sm
    from esgcet.project.input4mips import input4mips
    from esgcet.project.create_ip import CreateIP

    # Main entry point (stays at root)
    from esgcet.pub_internal import PubRunner, main as pub_main

    # Solr backend
    from esgcet.solr.index_pub import ESGPubIndex
    from esgcet.solr.pub_client import publisherClient
    from esgcet.solr.search_check import ESGSearchCheck

    # STAC backend
    from esgcet.stac.stac_client import (
        getTransactionClient, GlobusTransactionClient, EGITransactionClient
    )
    from esgcet.stac.stac_converter import ESGSTACConverter, ESGSTACItem

    # Globus backend
    from esgcet.globus.globus_search import GlobusSearchIngest
    from esgcet.globus.globus_query import ESGGlobusQuery

    # Metadata scanning
    from esgcet.scan.handler_base import ESGPubHandlerBase
    from esgcet.scan.mk_dataset import ESGPubMakeDataset
    from esgcet.scan.mk_dataset_autoc import ESGPubAutocHandler
    from esgcet.scan.mk_dataset_xarray import ESGPubXArrayHandler
    from esgcet.scan.mk_dataset_nc4 import ESGPubNC4Handler

    # Utilities
    from esgcet.util.logger import ESGPubLogger
    from esgcet.util.args import PublisherArgs
    from esgcet.util.settings import *  # Settings exports many constants
    from esgcet.util.mapfile import ESGPubMapConv
    from esgcet.util.pid_cite_pub import ESGPubPidCite

    # Support for 'import esgcet.logger as logger' pattern
    # For effective logging usage, we recommend: 'from esgcet.util import logger'
    # But we maintain backward compatibility with old pattern
    from esgcet.util import logger, settings, args, mapfile

except ImportError:
    # During the migration, some imports may fail temporarily.
    # This is expected and will be resolved as files are moved.
    pass

__all__ = [
    '__version__',
    # Core framework
    'BasePublisher',
    'GenericPublisher',
    'ESGPubHandlerBase',
    'PubRunner',
    'pub_main',
    # Project handlers
    'cmip5',
    'cmip6',
    'e3sm',
    'input4mips',
    'CreateIP',
    # Services
    'ESGPubPidCite',
    # Solr
    'ESGPubIndex',
    'publisherClient',
    'ESGSearchCheck',
    # STAC
    'getTransactionClient',
    'GlobusTransactionClient',
    'EGITransactionClient',
    'ESGSTACConverter',
    'ESGSTACItem',
    # Globus
    'GlobusSearchIngest',
    'ESGGlobusQuery',
    # Dataset creation
    'ESGPubMakeDataset',
    'ESGPubAutocHandler',
    'ESGPubXArrayHandler',
    'ESGPubNC4Handler',
    # Utilities
    'ESGPubLogger',
    'PublisherArgs',
    'ESGPubMapConv',
    'logger',
    'settings',
    'args',
    'mapfile',
]
