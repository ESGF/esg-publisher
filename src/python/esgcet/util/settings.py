DEBUG = False

DATA_NODE = None

CMOR_PATH = None
AUTOC_PATH = None
# these settings are presently managed within esg.ini and esg.<project>.ini

# Project-specific settings
# TODO: DRS and GA should be managed by a remote project service.
#    Then, set by the workflow at reasonable intervals

# For each project these become the . delimited components of the dataset_id
DRS = {
    "cmip6": [
        "mip_era",
        "activity_drs",
        "institution_id",
        "source_id",
        "experiment_id",
        "member_id",
        "table_id",
        "variable_id",
        "grid_label",
    ],
    "e3sm": [
        "source",
        "model_version",
        "experiment",
        "grid_resolution",
        "realm",
        "regridding",
        "data_type",
        "time_frequency",
        "ensemble_member",
    ],
    "input4mips": [
        "activity_id",
        "mip_era",
        "target_mip",
        "institution_id",
        "source_id",
        "realm",
        "frequency",
        "variable_id",
        "grid_label",
    ],
    "cordex": [
        "project",
        "product",
        "domain",
        "institute",
        "driving_model",
        "experiment",
        "ensemble",
        "rcm_model",
        "rcm_version",
        "time_frequency",
        "variable",
    ],
    "create-ip-exp": [
        "project",
        "product",
        "institute",
        "experiment",
        "realm",
        "time_frequency",
    ],
    "create-ip-src": [
        "project",
        "product",
        "institute",
        "source_id",
        "realm",
        "time_frequency",
    ],
    "create-ip-model": [
        "project",
        "product",
        "institute",
        "model",
        "source_id",
        "realm",
        "time_frequency",
    ],
    "create-ip-var": [
        "project",
        "product",
        "institute",
        "model",
        "source_id",
        "time_frequency",
        "realm",
        "variable",
    ],
    "cmip5": [
        "project",
        "product",
        "institute",
        "model",
        "experiment",
        "realm",
        "time_frequency",
        "ensemble",
    ],
    "obs4mips": [
        "activity_id",
        "institution_id",
        "source_id",
        "frequency",
        "variable_id",
        "grid_label",
    ],
    "mip-drs7": [
        "drs_specs",
        "mip_era",
        "activity_id",
        "institution_id",
        "source_id",
        "experiment_id",
        "variant_label",
        "region",
        "frequency",
        "variable_id",
        "variable_branding_suffix",
        "grid_label",
    ],
    "cordex-cmip6":  ["collection", "activity_drs","domain_id","institution_id","driving_source_id","driving_experiment_id","driving_variant_label","source_id","version_realization","frequency", "variable_id"]
}

#             "directory_path_template":"<drs_specs>/<mip_era>/<activity_id>/<institution_id>/<source_id>/<experiment_id>/<variant_label>/<region>/<frequency>/<variable_id>/<branding_suffix>/<grid_label>/<version>",

SPLIT_FACET = {"e3sm": {"delim": "_", "facet": "grid_resolution", 0: ""}}

# Global attributes expected to be read for a particular project.  For now a simple list.
GA = {
    "cmip6": [
        "frequency",
        "realm",
        "product",
        "nominal_resolution",
        "source_type",
        "grid",
        "creation_date",
        "variant_label",
        "sub_experiment_id",
        "activity_id",
        "data_specs_version",
        "title",
        
    ],
    "input4mips": [
        "contact",
        "dataset_category",
        "source_version",
        "source",
        "further_info_url",
        "title",
        "product",
        "nominal_resolution",
        "deprecated",
        "dataset_status",
        "Conventions",
        "target_mip_list",
        "creation_date",
    ],
    "obs4mips": [
        "realm",
        "product",
        "nominal_resolution",
        "source_type",
        "creation_date",
        "institution",
        "source",
        "source_type",
        "contact",
        "region",
        "data_specs_version",
        "further_info_url",
        "source_version_number",
        "cmor_version",
    ],
    "mip-drs7": [
        "grid",
        "nominal_resolution",
        "license_id",
        "area_label",
        "data_specs_version",
        "product",
        "realm",
        "Conventions",
        "source_type",
        "title",
        "temporal_label",
        "vertical_label",
        "forcing_index",
        "initialization_index",
        "realization_index",
        "physics_index",
        "member_id",
        "branded_variable",
        "branch_time_in_parent",
        "parent_activity_id",
        "parent_experiment_id",
        "parent_mip_era",
        "parent_source_id",
        "parent_time_units",
        "parent_variant_label",
        "horizontal_label"
    ],
    "cordex-cmip6": [
        "grid",
        "license",
        "product",
        "Conventions",
        "title", 
        "mip_era",
        "domain",
        "project_id",
        "version_realization_info",
        "driving_institution_id",
        "source_type",
        "activity_id"

]
}

GA_DELIMITED = {
    "cmip6": {"source_type": " ", "activity_id": " ", "realm": " "},
    "mip-drs7": {"realm": " ", "Conventions": " "},
    "cordex-cmip6" : {"Conventions": " ", "activity_id" : ' ' }
}
#                 'input4mips' : {'target_mip_list' : ','}}

CONST_ATTR = {
    "cmip6": {"model_cohort": "Registered", "project": "CMIP6"},
    "obs4mips": {"project": "obs4MIPs"},
    "input4mips": {"project": "input4MIPs"},
    "mip-drs7": {"project": "CMIP7", "acrhive_id": "WCRP"},
        "cordex-cmip6" : { "project" : "CORDEX-CMIP6"}
}

GA_MAPPED = {"cmip6": {"experiment": "experiment_title"}}

# the prefix is found in the published urls that are backed by the path prefix below
DATA_ROOTS = {}


SOURCE_ID_LIMITS = {"cmip6": 25, "mip-drs7": 32}

# a certificate file for the index, assumes in the CWD

# for these the following are inserted in order: 1. hostname 2. prefix 3. relative dataset path
# Eg replace /thredds/fileServer with the prefix for NginX
# Note these are netCDF specific and will need to change if other formats are considered
URL_Templates = [
    "https://{}/thredds/fileServer/{}/{}|application/netcdf|HTTPServer",
    # "https://{}/thredds/dodsC/{}/{}|application/opendap-html|OPENDAP",
    "globus:{}/{}/{}|Globus|Globus",
]

DATASET_GLOBUS_URL_TEMPLATE = (
    "https://app.globus.org/file_manager?origin_id={}&amp;origin_path=/{}"
)


#        handle-esgf-trusted.dkrz.de | 5671 | esgf-pid | esgf-publisher

PID_CREDS = [
    {
        "url": "aims4.llnl.gov",
        "port": 7070,
        "vhost": "esgf-pid",
        "user": "esgf-publisher",
        "password": "",
        "ssl_enabled": True,
        "priority": 1,
    }
]

PID_PREFIX = { 
    "cmip6" :  "21.14100" ,
    "cmip6plus" : "21.14100",
    "input4mips" : "21:14100",
    "cordex-cmip6" : "21.14103" ,
    "mip-drs7" : "21.14107" ,
    # for testing use CMIP6,  need to be project-specific
}
    
PID_EXCHANGE = "esgffed-exchange"
HTTP_SERVICE = "/thredds/fileServer/"

CITATION_URLS = {
    "cmip6": {
        "test": "http://cera-www.dkrz.de/WDCC/testmeta/CMIP6/{}.v{}.json",
        "prod": "http://cera-www.dkrz.de/WDCC/meta/CMIP6/{}.v{}.json",
    },
    "input4mips": {
        "test": "http://cera-www.dkrz.de/WDCC/testmeta/CMIP6/{}.v{}.json",
        "prod": "http://cera-www.dkrz.de/WDCC/meta/CMIP6/{}.v{}.json",
    },
}

PID_URL = "http://hdl.handle.net/{}|PID|pid"  # PIDs include hdl:
TEST_PUB = True

SET_REPLICA = False

QAQC = {
    "cordex-cmip6": {
        "test": ["wcrp_cordexcmip6:1.0"],
        "criteria": "lenient",
        "include_checks": None,
        "skip_checks": None,
    },
    "mip-drs7": {
        "test": ["wcrp_cmip7:1.0", "cf:1.11"],
        "criteria": "lenient",
        "include_checks": None,
        "skip_checks": None,
    },
}

STAC_CLIENT = {
    "client_id": "ec5f07c0-7ed8-4f2b-94f2-ddb6f8fc91a3",
    "redirect_uri": "https://auth.globus.org/v2/web/auth-code",
}

TOKEN_STORAGE_FILE = "~/.esgf2-publisher.json"

STAC_TRANSACTION_API = {
    "client_id": "6fa3b827-5484-42b9-84db-f00c7a183a6a",
    "access_control_policy": "https://esgf2.s3.amazonaws.com/access_control_policy.json",
    "scope_string": "https://auth.globus.org/scopes/6fa3b827-5484-42b9-84db-f00c7a183a6a/ingest",
    "base_url": "https://stac-transaction-api.esgf-west.org",
}

STAC_API = "https://api.stac.esgf-west.org"


VARIABLE_LIMIT = 75

VARIABLE_EXCLUDES = ["lat_bounds", "lon_bounds", "time_bounds"]

STAC_schema_versions = {
#                         "CMIP6" : "v3.0.4"
                        }

STAC_item_properties = [
    "access",
    "latest",
    "version",
    "project",
    "title",
]


# MAPS STAC property to legacy esgcet property
MAP_properties = {
 "CMIP7" : {
     "variable_cf_standard_name" : "cf_standard_name",
     "variable_branded_name" : "branded_variable",
     
 }   ,
    "CMIP6" : {
    "variable_cf_standard_name" : "cf_standard_name",
    "experiment" : "experiment_title"
    },
    "CORDEX-CMIP6" : {    "variable_cf_standard_name" : "cf_standard_name" } }


STAC_proj_item_properties = {
    "CMIP7": [
        "activity_id",
        "area_label",
        "region",
        "variable_cf_standard_name",
        "data_specs_version",
        "drs_specs",
        "experiment_id",
        "frequency",
        "grid_label",
        "institution_id",
        "nominal_resolution",
        "product",
        "realm",
        "source_id",
        # "source_type",
        "variable_id",
        "variable_long_name",
        "variable_units",
        "variant_label",
        "variable_branding_suffix",
        "Conventions",
        "license_id",
        "mip_era",
        "variable_branded_name",
        "variable_cf_standard_name",
        "temporal_label",
        "vertical_label",
        "forcing_index",
        "initialization_index",
        "realization_index",
        "physics_index",
        "pid",
        "parent_activity_id",
        "parent_experiment_id",
        "parent_mip_era",
        "parent_source_id",
        "parent_time_units",
        "parent_variant_label",
        "horizontal_label"        
    ],
    "CMIP6": [
        "activity_id",
        "data_specs_version",
        "experiment_id",
        "experiment",
        "frequency",
        "grid_label",
        "institution_id",
        "member_id",
        "mip_era",
        "nominal_resolution",
        "pid",
        "product",
        "realm",
        "source_id",
        "source_type",
        "experiment",
        "variable_cf_standard_name",
        "sub_experiment_id",
        "table_id",
        "variable_id",
        "variable_long_name",
        "variable_units",
        "variant_label",
    ],
    "CORDEX-CMIP6"  :  ["activity_id",
                        "domain_id",
                        "domain",
                        "institution_id",
                        "driving_source_id",
                        "driving_experiment_id",
                        "driving_institution_id",
                        "driving_variant_label",
                        "source_id",
                        "version_realization",
                        "frequency",
                        "grid",
                        "license",
                        "product",
                        "Conventions",
                        "project_id",
                        "source_type",
                        "variable_cf_standard_name",
                        "variable_id",
                        "variable_long_name",
                        "variable_units",
                        "version",
                        "version_realization_info",
                        "mip_era",
			            "pid"
                       ]
}

STAC_list_properties = {
    "ALL": [
    "access",
    "realm",
    "source_type",
    "Conventions",
    ],
    "CMIP6" : { "activity_id"},
    "CORDEX-CMIP6" : {"activity_id"}
}

CACHE_DIR_DEPTH = 6
PROJECT_MAP = {"cmip7" : "mip-drs7"}
BUILTIN_GENERICS = ["mip-drs7", "cordex", "cordex-cmip6", "cmip6", "cmip6plus", "obs4mips"]
