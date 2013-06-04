"Handle CFMIP data file metadata"

import os, string, glob

from esgcet.exceptions import *
from esgcet.config import ProjectHandler, getConfig, splitLine, ENUM, STRING, FIXED
from esgcet.model import Model, Experiment
# from Scientific.IO import NetCDF
try:
    import cdat_info
    cdat_info.ping = False
except:
    pass
from cdms2 import Cdunif
from ipcc4_handler import IPCC4Handler

SUBM = 0
FREQ = 1


tables={
    'CF1':('atm', 'mo'),
    'CF2':('atm', 'yr'),
    'CF3':('atm', 'da'),
    'CF4':('atm', 'mo')
}

tabtable = {
    ('atm', 'mo'):'CF1',
    ('atm', 'da'):'CF3',
    ('atm', 'yr'):'CF2',
    ('atm', 'forcing'):'CF4',
}

exps={
    '2xco2' : '2xco2',
    '2xCO2 equilibrium experiment' : '2xco2',
    'slabcntl' :'slabcntl',
    'slab ocean control experiment' : 'slabcntl',
    }

expdes = {
    '2xco2':('2xCO2 equilibrium experiment', '2xco2'),
    'slabcntl':('slab ocean control experiment', 'slabcntl'),
    }

shortfreq = {
    'daily': 'da',
    'forcing': 'forcing',
    'monthly': 'mo',
    'yearly': 'yr'
}    

longfreq = {
    'da': 'daily',
    'forcing': 'forcing',
    'mo': 'monthly',
    'yr': 'yearly',
    }

resolutionTable = {
    'daily': '1 day',
    'forcing': None,
    'monthly': '1 month',
    'yearly': '1 year'
}    

def frequency(tableid, varid):
    """Return the frequency"""
    return tables[tableid][FREQ]
    
def datasetFrequency(tableid):
    """Return the frequency associated with a dataset containing this table ID.
    For example, table A1 contains both monthly and fixed fields, but fixed
    fields are folded into 'monthly' datasets.
    """
    return tables[tableid][FREQ]

def submodel(tableid, varid):
    return tables[tableid][SUBM]
    
def totable(subm, freq):
    return tabtable[(subm, freq)]

def experiment(experDescrip):
    return exps[experDescrip]

def experimentDescription(expid):
    "Return a tuple of recognized experiment descriptions"
    return expdes[expid]

def experimentKeys():
    "Return a list of valid experiment keys"
    return expdes.keys()

def tableid(tabledesc):
    "Normalize the table ID from the CMOR table_id global attribute."
    tbl = tabledesc[6:9]
    return tbl

def tableKeys():
    return tables.keys()

def keys2path(keys):
    "Create a directory path from a dictionary of keys."
    run = keys['run']
    if run[0:3]!='run':
        run = 'run'+run
    return os.path.join(rootdir, keys['experiment'], keys['model'], run, keys['submodel'], keys['frequency'], keys['variable'])

def path2keys(path):
    "Create a dictionary of keys from an absolute file path (including base path)."
    scenario, model, run, submodel, frequency, variable, basepath = string.split(path,'/')[-7:]
    result = {'experiment': scenario,
              'submodel': submodel,
              'frequency': frequency,
              'variable': variable,
              'model': model, 
              'run_name': run,
              'basepath':basepath
              }

    return result

def canonicalizePath(path, fullpath=True):
    "Create the actual data path from any path that has the correct keys."
    keys = path2keys(path)
    basepath = keys.get("basepath", None)
    canonicalPath = keys2path(keys)
    if fullpath and (basepath is not None):
        canonicalPath = os.path.join(canonicalPath, basepath)
    return canonicalPath

def gentop(scenario, table):
    """Generate a 'top-level' directory without specifying the variable,
sufficient to determine the volume that the data will reside on."""
    return os.path.join(rootdir, scenario)

def listfiles(keys):
    "List all files matching the keys"
    pathTemplate = os.path.join(keys2path(keys),'*.nc')
    return glob.glob(pathTemplate)
    
def getModelList():
    pass

def normalizeMajor(major):
    return major

class CFMIPHandler(IPCC4Handler):

    def __init__(self, projectName, path, Session, validate=True, offline=False):

        ProjectHandler.__init__(self, projectName, path, Session, validate=validate, offline=offline)
        if not offline:
            try:
#                 f = NetCDF.NetCDFFile(path)
                f = Cdunif.CdunifFile(path)
            except:
                raise ESGPublishError('Error opening %s. Is the data offline?'%path)
            if not self.validateProject(f):
                raise ESGInvalidMetadataFormat("Not a %s datafile"%projectName)
            f.close()

        self.fieldNames = {
            'project': (ENUM, True, 0),
            'experiment': (ENUM, True, 1),
            'model': (ENUM, True, 2),
            'product': (ENUM, True, 3),
            'submodel': (ENUM, False, 4),
            'run_name': (STRING, True, 5),
            }
        self.context = {}
        self.validValues = {}

        if validate:
            self.initValidValues(Session)

    def validateProject(self, f):
        if not hasattr(f, 'project_id'):
            return False
        return (f.project_id=="CFMIP")

    def getContext(self, **context):
        if not self.offline:
#             f = NetCDF.NetCDFFile(self.path)
            f = Cdunif.CdunifFile(self.path)
            fileContext = self.file2keys(f, self.path)
            f.close()
            for key in ['experiment', 'submodel', 'run_name']:
                if not context.has_key(key):
                    context[key] = fileContext[key]
            if not context.has_key('product'):
                context['product'] = fileContext['frequency']
        if not context.has_key('project'):
            context['project'] = self.name
        if self.validate:
            self.validateContext(**context)
        self.context = context
        return context

    def getResolution(self):
        resolution = None
        product = self.context.get('product')
        if product is not None:
            resolution = resolutionTable[product]
        return resolution

    def file2keys(self, f, path, model=None):
        "Get a dictionary of keys from an open file. The model cannot be determined in general"

        fnm = os.path.basename(path)
        var = fnm.split('_')[0]
        try:
            exp=experiment(f.experiment_id.strip())
        except AttributeError:
            exp = None

        try:
            tbl = tableid(f.table_id)
            fqcy = frequency(tbl, var)
            loc = submodel(tbl, var)
        except:
            fqcy = None
            loc = None

        try:
            rlz='run'+str(f.realization[0])
        except AttributeError:
            rlz = None

        result = {'experiment': exp,
                  'submodel': loc,
                  'frequency': longfreq[fqcy],
                  'model': model, 
                  'run_name': rlz,
                  'variable': var,
                  'table': tbl}

        return result
