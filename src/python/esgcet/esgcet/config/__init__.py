#!/usr/bin/env python

"ESG-CET configuration modules"

from config import loadConfig, getConfig, splitLine, splitRecord, loadStandardNameTable, textTableIter, initLogging, registerHandlers, loadModelsTable, genMap, splitMap, loadConfig1, initializeExperiments, SaneConfigParser, getOfflineLister, getThreddsServiceSpecs, getThreddsAuxiliaryServiceSpecs
from project import ProjectHandler, ENUM, STRING, FIXED, TEXT
from format import FormatHandler
from registry import getHandler, getHandlerByName, getHandlerFromDataset, getHandlerByEntryPointGroup, getRegistry, ESGCET_PROJECT_HANDLER_GROUP, ESGCET_FORMAT_HANDLER_GROUP, ESGCET_METADATA_HANDLER_GROUP, ESGCET_THREDDS_CATALOG_HOOK_GROUP
from cf_handler import CFHandler
from netcdf_handler import BasicHandler, CdunifFormatHandler
from metadata import MetadataHandler

from ipcc4_handler import IPCC4Handler
from ipcc5_handler import IPCC5Handler
from tamip_handler import TAMIPHandler
builtinProjectHandlers = {
    'basic_builtin' : BasicHandler,
    'ipcc4_builtin' : IPCC4Handler,
    'ipcc5_builtin' : IPCC5Handler,
    'tamip_builtin' : TAMIPHandler,
    }
builtinFormatHandlers = {
    'netcdf_builtin' : CdunifFormatHandler,
    }
