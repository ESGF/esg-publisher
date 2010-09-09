"Handle IPCC5 data file metadata"

import os

from esgcet.exceptions import *
from esgcet.config import BasicHandler
from esgcet.messaging import debug, info, warning, error, critical, exception

import numpy

resolutionTable = {
    '3hr': '3 hour',
    '6hr': '6 hour',
    'day': '1 day',
    'fx': '1 month',
    'mon': '1 month',
    'monclim': '1 month',
    'subhr': '1 hour',
    'yr': '1 year',
    }

cmorAttributes = {
    'experiment': 'experiment_id',
    'forcing': 'forcing',
    'initialization_method': 'initialization_method',
    'institute': 'institute_id',
    'model': 'model_id',
    'physics_version': 'physics_version',
    'product': 'product',
    'realm': 'modeling_realm',
    'realization': 'realization',
    'run_name': 'realization',
    'table_id': 'table_id',
    'time_frequency': 'frequency',
    }

cmorTables = ['3hr', '6hrLev', '6hrPlev', 'Amon', 'LImon', 'Lmon', 'OImon', 'Oclim', 'Omon', 'Oyr', 'aero', 'cf3hr', 'cfDay', 'cfMon', 'cfOff', 'cfSites', 'day', 'fx', 'grids']

cmorArrayAttributes = ['initialization_method', 'physics_version', 'realization', 'run_name']

class IPCC5Handler(BasicHandler):

    def __init__(self, name, path, Session, validate=True, offline=False):
        self.caseSensitiveValidValues = {} # : field => (dict : lowerCaseValue => validValue)
        BasicHandler.__init__(self, name, path, Session, validate=validate, offline=offline)

    def initializeFields(self, Session):
        BasicHandler.initializeFields(self, Session)

        # Enumerated value validation is case-insensitive
        lowerCaseValidValues = {}
        for field, valueList in self.validValues.items():
            lowerCaseValidList = []
            validDict = {}
            for value in valueList:
                if value is not None:
                    lvalue = value.lower()
                else:
                    lvalue = None
                lowerCaseValidList.append(lvalue)
                validDict[lvalue] = value
            lowerCaseValidValues[field] = lowerCaseValidList
            self.caseSensitiveValidValues[field] = validDict
        self.validValues = lowerCaseValidValues

    def openPath(self, path):
        """Open a sample path, returning a project-specific file object,
        (e.g., a netCDF file object or vanilla file object)."""
        fileobj = BasicHandler.openPath(self, path)
        fileobj.path = path
        return fileobj

    def validateFile(self, fileobj):
        """Raise ESGInvalidMetadataFormat if the file cannot be processed by this handler."""
        if not fileobj.hasAttribute('project_id'):
            result = False
            message = "No global attribute: project_id"
        else:
            project_id = fileobj.getAttribute('project_id', None)
            result =  (project_id[:5]=="CMIP5")
            message = "project_id should be 'CMIP5'"
        if not result:
            raise ESGInvalidMetadataFormat(message)

    def getResolution(self):
        resolution = None
        freq = self.context.get('frequency')
        if freq is not None:
            resolution = resolutionTable[freq]
        return resolution

    def compareEnumeratedValue(self, value, options):
        if hasattr(value, 'lower'):
            lvalue = value.lower()
        else:
            lvalue = value
        return (lvalue in options)

    def mapValidFieldOptions(self, field, options):
        caseSensitiveValues = self.caseSensitiveValidValues[field]
        return caseSensitiveValues.values()

    def mapEnumeratedValues(self, context):
        for key in context.keys():
            if self.isEnumerated(key) and key in self.caseSensitiveValidValues:
                caseSensitiveValues = self.caseSensitiveValidValues[key]
                lvalue = context[key]
                if lvalue in caseSensitiveValues:
                    context[key] = caseSensitiveValues[lvalue]

    def readContext(self, cdfile, model=''):
        "Get a dictionary of keys from an open file"
        result = BasicHandler.readContext(self, cdfile)
        f = cdfile.file

        for key, value in cmorAttributes.items():
            try:
                result[key] = getattr(f, value)
                if key in cmorArrayAttributes and type(result[key]) is numpy.ndarray:
                    res = str(result[key][0])
                    if key=='run_name':
                        if res[0:3]!='run':
                            res = 'run'+res
                    result[key] = res
            except:
                pass

        if 'realization' in result and 'initialization_method' in result and 'physics_version' in result:
            ensemble = 'r%si%sp%s'%(result['realization'], result['initialization_method'], result['physics_version'])
            result['ensemble'] = ensemble

        base = os.path.basename(cdfile.path)
        try:
            index = base.index('_')
            varname = base[0:index]
            result['variable'] = varname
        except:
            warning("File path must have the form varname_XXX: %s"%cdfile.path)

        if not result.has_key('product'):
            result['product'] = 'output'

        self.mapEnumeratedValues(result)

        # Parse CMOR table.
        if 'table_id' in result:
            tableId = result['table_id']
            fields = tableId.split()

            # Assume table ID has the form 'Table table_id ...'
            if len(fields)>1 and (fields[1] in cmorTables):
                table = fields[1]
                result['cmor_table'] = table

        return result

    
