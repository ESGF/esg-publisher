"Handle IPCC4 data file metadata"

from esgcet.exceptions import *
from esgcet.config import BasicHandler, getConfig, splitLine, splitRecord, genMap, ENUM, STRING, FIXED, TEXT
from esgcet.model import Model, Experiment

from ipcc4_table_A1 import dic_A1
from ipcc4_table_O1 import dic_O1
import os, string, glob
import datetime

SUBM = 0
FREQ = 1
WIDGET_TYPE = 0
IS_MANDATORY = 1
IS_THREDDS_PROPERTY = 2
WIDGET_ORDER = 3

tables={
    'A1':('atm','mo'),
    'A2':('atm','da'),
    'A3':('atm','3h'),
    'A4':('atm','yr'),
    'A5':('atm','mo'),
    'O1':('ocn','mo'),
}

tabtable = {
('atm', 'mo'):'A1',
('atm', 'da'):'A2',
('atm', '3h'):'A3',
('atm', 'yr'):'A4',
('atm', 'forcing'):'A5',
('ice', 'mo'):'A1',
('land', 'fixed'):'A1',
('land', 'mo'):'A1',
('ocn', 'fixed'):'A1',
('ocn', 'mo'):'O1',
}

exps={
    '1pctto2x':'1pctto2x',
    '1pctto4x':'1pctto4x',
    '1%/year CO2 increase experiment (to doubling)':'1pctto2x',
    '1%/year CO2 increase experiment (to doubling) (1%_to2x)':'1pctto2x',
    '1%/year CO2 increase experiment (to quadrupling)':'1pctto4x',
    '20c3m':'20c3m',
    '2xco2':'2xco2',
    '2xCO2 equilibrium experiment':'2xco2',
    '550 ppm stabilization experiment (SRES B1)':'sresb1',
    '550 ppm stabilization experiment (SRES B1))':'sresb1',
    '720 ppm stabilization experiment (SRES A1B)':'sresa1b',
    '720 ppm stabilization experiment (SRES A1B))':'sresa1b',
    '720 ppm stabilization experiment (SRESA1B)':'sresa1b',
    'amip':'amip',
    'AMIP experiment':'amip',
    'climate of the 20th Century (20C3M)':'20c3m',
    'climate of the 20th Century experiment (20C3M)':'20c3m',
    'commit':'commit',
    'committed climate change experiment':'commit',
    'committed climate change experiment (Commit)':'commit',
    'Committed climate change experiment (commit)':'commit',
    'pdcntrl':'pdcntrl',
    'picntrl':'picntrl',
    'pre-industrial control experiment':'picntrl',
    'pre-industrial control experiment (PIcntrl)':'picntrl',
    'present-day control experiment':'pdcntrl',
    'present-day control experiment (PDcntrl)':'pdcntrl',
    'slabcntl':'slabcntl',
    'slab ocean control experiment':'slabcntl',
    'SRES A1B experiment':'sresa1b',
    'sresa1b':'sresa1b',
    'SRES A2 experiment':'sresa2',
    'SRES A2 experiment (SRES A2)':'sresa2',
    'SRES A2 experiment (SRESA2)':'sresa2',
    'sresa2':'sresa2',
    'sresb1':'sresb1',
    }

expdes = {
    '1pctto2x':('1%/year CO2 increase experiment (to doubling)', '1pctto2x'),
    '1pctto4x':('1%/year CO2 increase experiment (to quadrupling)', '1pctto4x'),
    '20c3m':('climate of the 20th Century experiment (20C3M)', '20c3m'),
    '2xco2':('2xCO2 equilibrium experiment', '2xco2'),
    'amip':('AMIP experiment', 'amip'),
    'commit':('committed climate change experiment', 'committed climate change experiment (Commit)', 'commit'),
    'pdcntrl':('present-day control experiment (PDcntrl)', 'present-day control experiment', 'pdcntrl'),
    'picntrl':('pre-industrial control experiment', 'picntrl'),
    'slabcntl':('slab ocean control experiment', 'slabcntl'),
    'sresa1b':('720 ppm stabilization experiment (SRES A1B)', 'sresa1b', '720 ppm stabilization experiment (SRESA1B)'),
    'sresa2':('SRES A2 experiment', 'sresa2', 'SRES A2 experiment (SRESA2)', 'SRES A2 experiment (SRES A2)'),
    'sresb1':('550 ppm stabilization experiment (SRES B1)', 'sresb1', '550 ppm stabilization experiment (SRESB1)'),
    }

shortfreq = {
    '3hourly': '3h',
    'daily': 'da',
    'fixed': 'fixed',
    'monthly': 'mo',
    'yearly': 'yr'
}    

longfreq = {
    '3h': '3hourly',
    'da': 'daily',
    'fixed': 'fixed',
    'mo': 'monthly',
    'yr': 'yearly',
    }

resolutionTable = {
    '3hourly': '3 hours',
    'daily': '1 day',
    'fixed': None,
    'monthly': '1 month',
    'yearly': '1 year'
    }

def frequency(tableid, var):
    """Return the frequency"""
    if tableid=='A1':
        return dic_A1[var][FREQ]
    elif tableid=='O1':
        return dic_O1[var][FREQ]
    else:
        return tables[tableid][FREQ]

def datasetFrequency(tableid):
    """Return the frequency associated with a dataset containing this table ID.
    For example, table A1 contains both monthly and fixed fields, but fixed
    fields are folded into 'monthly' datasets.
    """
    return tables[tableid][FREQ]

def submodel(tableid, var):
    """Return the submodel."""
    if tableid=='A1':
        return dic_A1[var][SUBM]
    elif tableid=='O1':
        return dic_O1[var][SUBM]
    else:
        return tables[tableid][SUBM]

def totable(subm, freq):
    return tabtable[(subm, freq)]

def experiment(experDescrip):
    return exps[experDescrip]

def experimentDescription(expid):
    return expdes[expid]

def experimentKeys(self):
    "Return a list of valid experiment keys"
    return expdes.keys()

def tableid(tabledesc):
    "Normalize the table ID from the CMOR table_id global attribute."
    if len(tabledesc)>=8:
        tbl=tabledesc[6:8]
    else:
        tbl=tabledesc[0:2]                # CSIRO
    return tbl

def tableKeys(self):
    return tables.keys()

def keys2path(keys):
    "Create a directory path from a dictionary of keys."
    run = keys['run_name']
    if run[0:3]!='run':
        run = 'run'+run
    return os.path.join(rootdir, keys['experiment'], keys['submodel'], keys['frequency'], keys['variable'], keys['model'], run)

def path2keys(path):
    "Create a dictionary of keys from an absolute file path (including base path)."
    scenario, submodel, frequency, variable, model, run, basepath = string.split(path,'/')[-7:]
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
    keys = self.path2keys(path)
    basepath = keys.get("basepath", None)
    canonicalPath = self.keys2path(keys)
    if fullpath and (basepath is not None):
        canonicalPath = os.path.join(canonicalPath, basepath)
    return canonicalPath

def gentop(scenario, table):
    """Generate a 'top-level' directory without specifying the variable,
sufficient to determine the volume that the data will reside on."""
    # (20c3m, A2) => /ipcc/20c3m/atm/da
    if table[0]=='A':
        if table[1]=='2':
            subdir = 'atm/da'
        elif table[1]=='3':
            subdir = 'atm/3h'
        else:
            subdir = 'atm/mo'
    else:
        subdir = 'ocn'
    return os.path.join('/ipcc',scenario,subdir)

def listfiles(keys):
    "List all files matching the keys"
    pathTemplate = os.path.join(keys2path(keys),'*.nc')
    lastargs = glob.glob(pathTemplate)
    if keys['frequency']=="mo":
        keys['frequency'] = 'fixed'
        pathTemplate = os.path.join(keys2path(keys),'*.nc')
        lastargs.extend(glob.glob(pathTemplate))
    return lastargs

def getModelList():
    pass

def normalizeMajor(major):
    return major[0:2]

_FIELDTYPE = 0
_MANDATORY = 1
_SEQ = 2

class IPCC4Handler(BasicHandler):

    def validateFile(self, cdfileobj):
        """Raise ESGInvalidMetadataFormat if the file cannot be processed by this handler."""
        fileobj = cdfileobj.file
        if not hasattr(fileobj, 'project_id'):
            result = False
            message = "No global attribute: project_id"
        else:
            result =  (fileobj.project_id[:22]=="IPCC Fourth Assessment")
            message = "project_id should be 'IPCC Fourth Assessment'"
        if not result:
            raise ESGInvalidMetadataFormat(message)

    def getResolution(self):
        resolution = None
        product = self.context.get('product')
        if product is not None:
            resolution = resolutionTable[product]
        return resolution

    def validateContext(self, context):
        BasicHandler.validateContext(self, context)
        run = context.get('run_name', '')
        if len(run)<3 or run[0:3]!='run' or (' ' in run):
            raise ESGPublishError("Invalid value of run: %s, must have the form 'runN'"%run)

    def readContext(self, cdfile, model=''):
        "Get a dictionary of keys from an open file. The model cannot be determined in general"
        result = BasicHandler.readContext(self, cdfile)
        f = cdfile.file
        
        fnm = os.path.basename(self.path)
        try:
            exp = experiment(f.experiment_id.strip())
        except AttributeError:
            exp = None

        try:
            tableid = f.table_id
            if len(tableid)>=8:
                tbl=f.table_id[6:8]
            else:
                tbl=tableid[0:2]                # CSIRO

            if tbl!='A5':
                var = os.path.split(fnm)[-1].split('_')[0]
            else:
                varflds = os.path.split(fnm)[-1].split('_')
                if len(varflds) in [3,4,9]:       # CCCMA has 9 subfields, 4 for NCAR
                    var = varflds[0]+'_'+varflds[1]
                elif len(varflds)==2:
                    var = varflds[0]
                else:
                    raise ESGPublishError('Cannot determine variable name for file %s'%fnm)
            fqcy = longfreq[frequency(tbl, var)]
            loc = submodel(tbl, var)
        except AttributeError:
            var = None
            fqcy = None
            loc = None

        try:
            rlz='run'+str(f.realization[0])
        except AttributeError:
            rlz = None

        if exp is not None:
            result['experiment'] = exp
        if loc is not None:
            result['submodel'] = loc
        if fqcy is not None:
            result['time_frequency'] = fqcy
        if var is not None:
            result['variable'] = var
        if model is not None:
            result['model'] = model
        if rlz is not None:
            result['run_name'] = rlz

        # Try to determine model from source string
        if model=='' and 'source' in result:
            source = result['source']
            if source[0:7]=='BCC-CM1':
                model = 'bcc_cm1'
            elif source[0:6] == 'BCM2.0':
                model = 'bccr_bcm2_0'
            elif source[0:7] == 'CCSM3.0':
                model = 'ncar_ccsm3_0'
            elif source[0:8] == 'CNRM-CM3':
                model = 'cnrm_cm3'
            elif source[0:6] == 'ECHAM5':
                model = 'mpi_echam5'
            elif source[0:6] == 'ECHO-G':
                model = 'miub_echo_g'
            elif source[0:4] in ['FGCM', 'FGOA']:
                model = 'iap_fgoals1_0_g'
            elif source[0:10] in ['GFDL_CM2.1', 'GFDL_AM2.1']:
                model = 'gfdl_cm2_1'
            elif source[0:10] in ['GFDL_CM2.0', 'GFDL_SM2.0']:
                model = 'gfdl_cm2_0'
            elif source[0:8] == 'GISS AOM':
                model = 'giss_aom'
            elif source[0:6] == 'HadCM3':
                model = 'ukmo_hadcm3'
            elif source[0:7] == 'HadGEM1':
                model = 'ukmo_hadgem1'
            elif source[0:8] == 'INGV-SXG':
                model = 'ingv_echam4'
            elif source[0:8] == 'INMCM3.0':
                model = 'inmcm3_0'
            elif source[0:8] == 'IPSL-CM4':
                model = 'ipsl_cm4'
            elif source[0:9] == 'MRI-CGCM2':
                model = 'mri_cgcm2_3_2a'
            elif source[0:8] == 'Parallel':
                model = 'ncar_pcm1'
            elif source[0:50] == 'CGCM3.1 (2004): atmosphere:  AGCM3 (GCM13d, T47L31':
                model = 'cccma_cgcm3_1'
            elif source[0:50] == 'CGCM3.1 (2004): atmosphere:  AGCM3 (GCM13d, T63L31':
                model = 'cccma_cgcm3_1_t63'
            elif source[0:11] == 'CSIRO Mk3.0':
                model = 'csiro_mk3_0'
            elif source[0:11] == 'CSIRO Mk3.5':
                model = 'csiro_mk3_5'
            elif source[0:49] == 'MIROC3.2 (2004): atmosphere: AGCM (AGCM5.7b, T106':
                model = 'miroc3_2_hires'
            elif source[0:48] == 'MIROC3.2 (2004): atmosphere: AGCM (AGCM5.7b, T42':
                model = 'miroc3_2_medres'
            elif source[0:3] == 'E3x':
                model = 'giss_model_e_h'
            elif source[0:19] == 'GISS ModelE/Russell':
                model = 'giss_model_e_r'
            elif source[0:17] == 'GISS ModelE/HYCOM':
                model = 'giss_model_e_h'
            elif source[0:3] == 'E3A':
                model = 'giss_model_e_r'
            elif source[0:3] == 'E3O':
                model = 'giss_model_e_h'
            result['model'] = model

        return result

