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
# Make util submodules available as if they were at root level
# This allows 'from esgcet.args import PublisherArgs' to work
from esgcet.util import logger, settings, args, mapfile
from esgcet import util, project, solr, stac, globus, scan

# Create module aliases for backward compatibility with imports like 'from esgcet.args import'
import sys
sys.modules['esgcet.args'] = args
sys.modules['esgcet.logger'] = logger
sys.modules['esgcet.settings'] = settings
sys.modules['esgcet.mapfile'] = mapfile

# Create module aliases for moved project files
from esgcet.project import generic_pub, generic_netcdf, cmip5 as cmip5_module, cmip6 as cmip6_module, e3sm as e3sm_module, input4mips as input4mips_module, create_ip
from esgcet.util import pid_cite_pub
sys.modules['esgcet.generic_pub'] = generic_pub
sys.modules['esgcet.generic_netcdf'] = generic_netcdf
sys.modules['esgcet.cmip5'] = cmip5_module
sys.modules['esgcet.cmip6'] = cmip6_module
sys.modules['esgcet.e3sm'] = e3sm_module
sys.modules['esgcet.input4mips'] = input4mips_module
sys.modules['esgcet.create_ip'] = create_ip
sys.modules['esgcet.pid_cite_pub'] = pid_cite_pub

# Create module aliases for moved solr files
from esgcet.solr import index_pub, pub_client, search_check, update_solr, unpublish_solr, unpublish_base, xmlfix
sys.modules['esgcet.index_pub'] = index_pub
sys.modules['esgcet.pub_client'] = pub_client
sys.modules['esgcet.search_check'] = search_check
sys.modules['esgcet.update_solr'] = update_solr
sys.modules['esgcet.unpublish_solr'] = unpublish_solr
sys.modules['esgcet.unpublish_base'] = unpublish_base
sys.modules['esgcet.xmlfix'] = xmlfix

# Create module aliases for moved stac files
from esgcet.stac import stac_client, stac_converter, update_stac, unpublish_stac
sys.modules['esgcet.stac_client'] = stac_client
sys.modules['esgcet.stac_converter'] = stac_converter
sys.modules['esgcet.update_stac'] = update_stac
sys.modules['esgcet.unpublish_stac'] = unpublish_stac

# Create module aliases for moved globus files
from esgcet.globus import globus_search, globus_query, update_globus, unpublish_globus
sys.modules['esgcet.globus_search'] = globus_search
sys.modules['esgcet.globus_query'] = globus_query
sys.modules['esgcet.update_globus'] = update_globus
sys.modules['esgcet.unpublish_globus'] = unpublish_globus

# Create module aliases for moved scan files
from esgcet.scan import mk_dataset, mk_dataset_autoc, mk_dataset_xarray, mk_dataset_nc4, handler_base
sys.modules['esgcet.mk_dataset'] = mk_dataset
sys.modules['esgcet.mk_dataset_autoc'] = mk_dataset_autoc
sys.modules['esgcet.mk_dataset_xarray'] = mk_dataset_xarray
sys.modules['esgcet.mk_dataset_nc4'] = mk_dataset_nc4
sys.modules['esgcet.handler_base'] = handler_base

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
