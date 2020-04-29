DEBUG = False

# these settings are presently managed within esg.ini and esg.<project>.ini

# Project-specific settings
#TODO: DRS and GA should be managed by a remote project service.  
#    Then, set by the workflow at reasonable intervals

# For each project these become the . delimited components of the dataset_id
DRS = { 'CMIP6' : [ 'mip_era' , 'activity_drs','institution_id','source_id','experiment_id','member_id','table_id','variable_id','grid_label'] }

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
                     'data_specs_version', 'title']}


# These below are server-specific settings
DATA_NODE = "greyworm1-rh7.llnl.gov"
INDEX_NODE = "esgf-fedtest.llnl.gov"

# the prefix is found in the published urls that are backed by the path prefix below
ROOT = {'esgf_data': '/esg/data'}


# a certificate file for the index, assumes in the CWD
CERT_FN = "cert.pem"

# Eg replace /thredds/fileServer with the prefix for NginX
# Note these are netCDF specific and will need to change if other formats are considered
URL_Templates = ["https://{}/thredds/fileServer/{}/{}|application/netcdf|HTTPServer",
"https://{}/thredds/dodsC/{}/{}|application/opendap-html|OPENDAP"]

