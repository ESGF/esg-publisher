#!/usr/bin/env python

"ESG-CET configuration modules"

from config import loadConfig, getConfig, splitLine, splitRecord, loadStandardNameTable, textTableIter, initLogging, registerHandlers, loadModelsTable, genMap, splitMap, loadConfig1, initializeExperiments, SaneConfigParser, getOfflineLister, getThreddsServiceSpecs, getThreddsAuxiliaryServiceSpecs
from project import ProjectHandler, ENUM, STRING, FIXED, TEXT, compareLibVersions
from format import FormatHandler
from registry import getHandler, getHandlerByName, getHandlerFromDataset, getHandlerByEntryPointGroup, getRegistry, ESGCET_PROJECT_HANDLER_GROUP, ESGCET_FORMAT_HANDLER_GROUP, ESGCET_METADATA_HANDLER_GROUP, ESGCET_THREDDS_CATALOG_HOOK_GROUP
from cf_handler import CFHandler
from netcdf_handler import BasicHandler, CdunifFormatHandler
from metadata import MetadataHandler
from multiple_format_handler import MultipleFormatHandler

from ipcc4_handler import IPCC4Handler
from ipcc5_handler import IPCC5Handler
# from cmip6_handler import CMIP6Handler  --  should not include by default due to prerequistes deemed optional
from tamip_handler import TAMIPHandler
from obs4mips_handler import Obs4mipsHandler
builtinProjectHandlers = {
    'basic_builtin' : BasicHandler,
    'ipcc4_builtin' : IPCC4Handler,
    'ipcc5_builtin' : IPCC5Handler,
#    'cmip6_builtin' : CMIP6Handler,
    'tamip_builtin' : TAMIPHandler,
    'obs4mips_builtin' : Obs4mipsHandler,
    }
builtinFormatHandlers = {
    'netcdf_builtin' : CdunifFormatHandler,
    'multiple_builtin' : MultipleFormatHandler,
    }
