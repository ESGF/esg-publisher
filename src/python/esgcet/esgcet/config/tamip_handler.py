"""Handle TAMIP data file metadata

This handler is based on the IPCC5Handler distributed with esgcet.

@author: Stephen Pascoe.

"""

import os
import re

#!NOTE: This handler doesn't support product dection for TAMIP.  
#    Assume you've assigned it with drslib
#from cmip5_product import getProduct

from esgcet.exceptions import *
from esgcet.config import BasicHandler, getConfig
from esgcet.messaging import debug, info, warning, error, critical, exception

import numpy

DRS_ACTIVITY = 'tamip'
PROJECT_ID = 'TAMIP'

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

cmorTables = ['3hrCurt', '3hrPlev', 'sites', '3hrMlev', '3hrSlev'] 


cmorArrayAttributes = ['initialization_method', 'physics_version', 'realization', 'run_name']

drsInvalidValues = re.compile(r'[^a-zA-Z0-9-]+')
drsFields = {
    'cmor_table' : 1,
    'ensemble' : 1,
    'experiment' : 1,
    'institute' : 1,
    'model' : 1,
    'product' : 1,
    'realm' : 1,
    'time_frequency' : 1,
    }

def mapToComp(date_str):
    try:
        m = re.match(r'(\d{4})(\d{2})?(\d{2})?(\d{2})?', date_str)
        if not m:
            raise ValueError()

        (y, m, d, h) = m.groups()
        result = (int(y), intOrNone(m), intOrNone(d), intOrNone(h))
    except TypeError:
        result = (None, None, None, None)
    return result

def intOrNone(x):
    if x is None:
        return None
    else:
        return int(x)
    
def isDRSField(field):
    return (field in drsFields)

def validateDRSFieldValues(context, cdfile):
    """DRS fields must be formed from characters a-z,A-Z,0-9,-
    
    context: dictionary of context values to be validated
    cdfile: CdunifFormatHandler instance

    Returns the context with any sequence of invalid characters (for a DRS field) mapped to '-'.
    
    For example, 'NOAA  GFDL' is mapped to 'NOAA-GFDL'.
    """

    for key in context.keys():
        if isDRSField(key):
            value = context[key]
            if drsInvalidValues.search(value) is not None:
                result = drsInvalidValues.sub('-', value)
                info('Mapped invalid %s value: %s to %s, file: %s'%(key, value, result, cdfile.path))
                context[key] = result

    return context

class TAMIPHandler(BasicHandler):

    def __init__(self, name, path, Session, validate=True, offline=False):
        self.caseSensitiveValidValues = {} # : field => (dict : lowerCaseValue => validValue)
        self.checkFilenames = True      # True <=> check variable shortname against file basename
        BasicHandler.__init__(self, name, path, Session, validate=validate, offline=offline)

    def initializeFields(self, Session):
        BasicHandler.initializeFields(self, Session)
        config = getConfig()
        projectSection = 'project:'+self.name

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
        self.checkFilenames = config.getboolean(projectSection, 'thredds_check_file_names', default=True)

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
            result =  (project_id[:5]==PROJECT_ID)
            message = "project_id should be '%s'" % PROJECT_ID
        if not result:
            raise ESGInvalidMetadataFormat(message)

    def getResolution(self):
        resolution = None
        freq = self.context.get('frequency')
        if freq is not None:
            resolution = resolutionTable[freq]
        return resolution

    def compareEnumeratedValue(self, value, options, delimiter=""):
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

    def getDateRangeFromPath(self):
        "Parse date range from DRS-style file path"
        fields = self.path.split('_')
        m = re.match(r'(\d+)(?:-(\d+))?(-clim)?', fields[-1])
        if m is not None:
            n1, n2, clim = m.groups()
            ct1 = mapToComp(n1)
            ct2 = mapToComp(n2)
        else:
            ct1 = ct2 = (None, None, None, None)
        return (ct1, ct2)

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
            result['run_name'] = ensemble

        base = os.path.basename(cdfile.path)
        try:
            index = base.index('_')
            varname = base[0:index]
            result['variable'] = varname
        except:
            warning("File path must have the form varname_XXX: %s"%cdfile.path)

        #!WARNING: I think all TAMIP2 data goes into output1
        result['product'] = 'output1'

        self.mapEnumeratedValues(result)

        # If realm has multiple fields, pick the first one
        if 'realm' in result:
            realm = result['realm'].strip()
            if realm.find(' ')!=-1:
                realms = realm.split(' ')
                result['realm'] = realms[0]

        # Parse CMOR table.
        if 'table_id' in result:
            tableId = result['table_id']
            fields = tableId.split()

            # Assume table ID has the form 'Table table_id ...'
            if len(fields)>1 and (fields[1] in cmorTables):
                table = fields[1]
                result['cmor_table'] = table
            else:
                result['cmor_table'] = 'noTable'
        else:
            result['cmor_table'] = 'noTable'


        # Cache a 'drs_id' attribute for DRS-style dataset lookups
        validateDRSFieldValues(result, cdfile)
        if 'product' in result and 'institute' in result and 'model' in result and 'experiment' in result and 'time_frequency' in result and 'realm' in result and 'cmor_table' in result and 'ensemble' in result:
            drsid = '%s.%s.%s.%s.%s.%s.%s.%s.%s'%(DRS_ACTIVITY, result['product'], result['institute'], result['model'], result['experiment'], result['time_frequency'], result['realm'], result['cmor_table'], result['ensemble'])
            result['drs_id'] = drsid
            

        return result

    def threddsIsValidVariableFilePair(self, variable, fileobj):
        """Returns True iff the variable and file should be published
        to a per-variable THREDDS catalog for this project.

        variable
          A Variable instance.

        fileobj
          A File instance.
        """
        # Require that the variable short name match the portion
        # of the file basename preceding the first underscore.
        try:
            if self.checkFilenames:
                shortname = variable.short_name
                path = fileobj.getLocation()
                basename = os.path.basename(path)
                pathshortname = basename.split('_')[0]
                result = (shortname == pathshortname)
            else:
                result = True
        except:
            result = True
        if not result:
            info("Skipping variable %s (in file %s)"%(variable.short_name, fileobj.getLocation()))
        return result
