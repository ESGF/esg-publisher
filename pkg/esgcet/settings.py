DEBUG = False

INDEX_NODE = "esgf-node.llnl.gov"
DATA_NODE = None

CMOR_PATH = None
AUTOC_PATH = None
# these settings are presently managed within esg.ini and esg.<project>.ini

# Project-specific settings
#TODO: DRS and GA should be managed by a remote project service.  
#    Then, set by the workflow at reasonable intervals

# For each project these become the . delimited components of the dataset_id
DRS = { 'CMIP6' : [ 'mip_era' , 'activity_drs','institution_id','source_id','experiment_id','member_id','table_id','variable_id','grid_label'],
         'E3SM' : [ 'source', 'model_version', 'experiment', 'grid_resolution', 'realm', 'regridding', 'data_type', 'time_frequency', 'ensemble_member'],
    'input4MIPs' : ['activity_id', 'mip_era', 'target_mip', 'institution_id', 'source_id', 'realm', 'frequency', 'variable_id', 'grid_label' ] }

SPLIT_FACET = { 'E3SM' : { 'delim' : '_' , 'facet' : 'grid_resolution', 0 : ''}  }

# Global attributes expected to be read for a particular project.  For now a simple list.  
GA = { 'CMIP6' : ['frequency',
                     'realm',
                     'product',
                     'nominal_resolution',
                     'source_type',
                     'grid',
                     'creation_date',
                     'variant_label',
                     'sub_experiment_id',
                     'further_info_url',
                     'activity_id',
                     'data_specs_version', 'title'],
       'input4MIPs' : ['contact',
'dataset_category',
'source_version',
'further_info_url',
'title',
'product',
'table',
'nominal_resolution',
'institution',
'target_mip_list'
'source',
'deprecated',
'dataset_status',
'realm_drs',
'Conventions',
'creation_date']}

GA_DELIMITED = { 'CMIP6' : { 'source_type' : ' ', 'activity_id' : ' ', 'realm' : ' '  },
                 'input4MIPs' : {'target_mip' : ','}}

CONST_ATTR =  { 'CMIP6' : { 'model_cohort' : 'Registered' }}

GA_MAPPED = { 'CMIP6' : { 'experiment' : 'experiment_title'} }

# the prefix is found in the published urls that are backed by the path prefix below
DATA_ROOTS = {'/esg/data' : 'esgf_data',
 '/p/user_pub/work' :  'user_pub_work', 
 '/p/css03/esgf_publish' : 'css03_data' }


# a certificate file for the index, assumes in the CWD
CERT_FN = "/p/user_pub/publish-queue/certs/certificate-file"

# for these the following are inserted in order: 1. hostname 2. prefix 3. relative dataset path
# Eg replace /thredds/fileServer with the prefix for NginX
# Note these are netCDF specific and will need to change if other formats are considered
# TODO - add Globus , GridFTP
URL_Templates = ["https://{}/thredds/fileServer/{}/{}|application/netcdf|HTTPServer",
"https://{}/thredds/dodsC/{}/{}.html|application/opendap-html|OPENDAP",
                 "gsiftp://{}:2811/{}/{}|application/gridftp|GridFTP",
                 "globus:{}/{}/{}|Globus|Globus"]

#        handle-esgf-trusted.dkrz.de | 5671 | esgf-pid | esgf-publisher 

PID_CREDS = [ {'url': 'aims4.llnl.gov',
             'port': 7070,
             'vhost': 'esgf-pid',
             'user': 'esgf-publisher',
             'password': "",
             'ssl_enabled': True,
             'priority': 1}] 

PID_PREFIX = '21.14100' # for testing use CMIP6,  need to be project-specific
PID_EXCHANGE = 'esgffed-exchange'
HTTP_SERVICE = '/thredds/fileServer/'

CITATION_URLS = { 'CMIP6' : {'test' :
'http://cera-www.dkrz.de/WDCC/testmeta/CMIP6/{}.v{}.json' ,
        'prod' : 'http://cera-www.dkrz.de/WDCC/meta/CMIP6/{}.v{}.json'},
'input4MIPs' : {'test' :
'http://cera-www.dkrz.de/WDCC/testmeta/CMIP6/{}.v{}.json' ,
        'prod' : 'http://cera-www.dkrz.de/WDCC/meta/CMIP6/{}.v{}.json'}
                  
}

PID_URL = 'http://hdl.handle.net/{}|PID|pid'  # PIDs include hdl:
TEST_PUB = False

PROJECT = "input4MIPs"  # project setting.  This would be used to consider some project-specific features, eg. for CMIP6
SET_REPLICA = False
