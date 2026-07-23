
import argparse
from pathlib import Path
import os
import esgcet.util.logger as logger
import esgcet
import yaml

log = logger.ESGPubLogger()
publog = log.return_logger('Settings')



class PublisherArgs:
    """  Reconcile command line argumenets and config file settings.
    """
    def __init__(self):
        pass

    def get_args(self):
        """ Wrap argument parser
        """
        parser = argparse.ArgumentParser(description="Publish data sets to ESGF databases.")

        # ANY FILE NAME INPUT: check first to make sure it exists
        # Check for environment variable first (useful for testing)
        import os
        env_config = os.getenv('ESG_CONFIG_FILE')
        if env_config:
            def_config = env_config
        else:
            home = Path.home()
            def_config = home / ".esg/esg.yaml"
        parser.add_argument("--test", dest="test", action="store_true", help="PID registration will run in 'test' mode. Use this mode unless you are performing 'production' publications.")
        # replica stuff new... hard-coded, modify mk dataset so that it imports it instead
        parser.add_argument("--set-replica", dest="set_replica", action="store_true", help="Enable replica publication.")
        parser.add_argument("--no-replica", dest="no_replica", action="store_true", help="Disable replica publication.")
        parser.add_argument("--json", dest="json", default=None, help="Load attributes from a JSON file in .json form. The attributes will override any found in the DRS structure or global attributes.")
        parser.add_argument("--data-node", dest="data_node", default=None, help="Specify data node.")
        parser.add_argument("--index-node", dest="index_node", default=None, help="Specify index node. Legacy Solr use only.")
        parser.add_argument("--certificate", "-c", dest="cert", default=None, help="Use the following certificate file in .pem form for publishing (use a myproxy login to generate). Legacy Solr with auth only.")
        parser.add_argument("--project", dest="proj", default="", help="Set/overide the project for the given mapfile, for use with selecting the DRS or specific features, e.g. PIDs.  Also required for custom and cloned projects")
        parser.add_argument("--cmor-tables", dest="cmor_path", default=None, help="Path to CMIP CMOR tables for metadata checks. Required for CMIP6Plus and later. Deprecated for ESGF-NG in favor of compliance checker")
        parser.add_argument("--autocurator", dest="autocurator_path", default=None, help="Path to autocurator repository folder.  Only use if you have installed autocurator to use in place of xarray scanning")
        parser.add_argument("--map", dest="map", required=True, nargs="+", help="Mapfile, a file containing list of mapfiles (relative or absolute paths), or a directory containing mapfiles.  esgpublish will determine which input")
        parser.add_argument("--config", "-cfg", dest="cfg", default=str(def_config), help="Path to yaml config file.")
        parser.add_argument("--silent", dest="silent", action="store_true", help="Enable silent mode.")
        parser.add_argument("--verbose", dest="verbose", action="store_true", help="Enable verbose (debug) mode.")
        parser.add_argument("--verify", dest="verify", action="store_true", help="Toggle certificate verification for publishing, default is off (supports insecure checking to allow for self-signed nodes).")
        parser.add_argument("--version", action="version", version=f"esgpublish v{esgcet.__version__}",help="Print the version and exit")
        parser.add_argument("--xarray", dest="xarray", action="store_true", help="Use Xarray to extract metadata even if Autocurator is configured. (Default, overrides setting)") 
        parser.add_argument("--stac-api", dest="stac_api", default=None, help="Specify STAC Discovery API.")
        parser.add_argument("--no-xarray", dest="skipxr", action="store_true", help="Bypass use of Xarray (metadata will be incomplete)")
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Dry run publishing. Scans data but does not interface with index APIs.")
        parser.add_argument("--save-stac", action="store_true", help="For use with STAC publishing: saves the STAC Item to the cwd named as <dataset-id>.json.  Useful to validate an Item in event of an error.")
        pub = parser.parse_args()

        return pub

    def load_config(self, config_path):
        """
        Load the configuration file from specified path
        config_path : string  config file path cannot be empty
        """
        config_file = None
        try:
            config_file = open(config_path, 'r')  # or "a+", whatever you need
        except IOError:
            publog.error("Could not open file, please provide correct path to yaml config file.")
            quit(1)

        with config_file as fd:
            conf = yaml.load(fd, Loader=yaml.SafeLoader)
        return conf

    def get_dict(self,  fn_project):
        """
        Return a dict containing the publisher arguments to use:
        fn_project (string)  Specified project if pre-parsed.
        """
        pub = self.get_args()
        json_file = pub.json


        config_file = pub.cfg
        config = self.load_config(config_file)
        if not os.path.exists(config_file):
            publog.error("Config file not found. " + config_file + " does not exist.")
            exit(1)
        if os.path.isdir(config_file):
            publog.error("Config file path is a directory. Please use a complete file path, exiting.")
            exit(1)

        if pub.proj != "":
            project = pub.proj
        else:
            try:
                project = config['project']
                if "none" in project:
                    project = fn_project
            except:
                project = fn_project

        verbose = False
        if not pub.silent:
            try:
                s = config['silent']
                if 'true' in s or 'yes' in s:
                    silent = True
                else:
                    silent = False
            except:
                silent = False
        else:
            silent = True

        if not pub.verbose:
            if not pub.silent:
                try:
                    v = config['verbose']
                    if 'true' in v or 'yes' in v:
                        verbose = True
                    else:
                        verbose = False
                except:
                    verbose = False
        else:
            verbose = True
            silent = False

        auth = False
        cert = ""
        if pub.cert:
            auth = True
            cert = pub.cert
        elif 'cert' in config:
            cert = config['cert']
            auth = True
        try:
            if pub.no_auth:
                auth = False
        except:
            pass

        if pub.xarray:
            autocurator = None
        elif pub.autocurator_path is None:
            autocurator = config.get('autoc_path', None)
            if autocurator == "none":
                autocurator = None
        else:
            autocurator = pub.autocurator_path

        if pub.index_node is None:
            index_node = config.get('index_node', None)
        else:
            index_node = pub.index_node

        if pub.data_node is None:
            data_node = config.get('data_node',None)
        else:
            data_node = pub.data_node
        try:
            data_roots = config['data_roots']
            if data_roots == 'none':
                publog.error("Data roots undefined. Define in config file to create file metadata.")
                exit(1)
        except:
            publog.exception("Data roots undefined. Define in config file to create file metadata.")
            exit(1)

        try:
            globus = config['globus_uuid']
        except:
            globus = "none"


        disable_citation = config.get("disable_citation", False)
        disable_further_info = config.get("disable_further_info", False)
        
        if pub.set_replica and pub.no_replica:
            publog.error("Replica publication simultaneously set and disabled.")
            exit(1)
        elif pub.set_replica:
            replica = True
        elif pub.no_replica:
            replica = False
        else:
            replica = config.get('set_replica', False)
            
        test = False
        if pub.test:
            test = True

        try:
            proj_config = config['user_project_config']
        except:
            publog.warning("User project config missing or could not be parsed.")
            proj_config = {}


        if pub.verify:
            verify = True
        else:
            verify = False

        non_nc = config.get('non_netcdf', False)
      
        if not type(non_nc) is bool: 
            non_netcdf = config['non_netcdf'].lower()
            if 'yes' in non_netcdf or 'true' in non_netcdf:
                non_nc = True
            else:
                non_nc = False

        try:
            mountpoints = config['mountpoint_map']
            if mountpoints == "none":
                mountpoints = None
        except:
            mountpoints = None

        if globus == "none" and not silent:
            publog.info("No Globus UUID defined.")

        argdict = { "silent": silent, 
                   "verbose": verbose,
                   "autoc_command": autocurator, 
                   "index_node": index_node, 
                   "data_node": data_node,
                   "data_roots": data_roots, 
                   "globus": globus, 
                   "replica": replica,
                   "json_file": json_file, 
                   "test": test, 
                   "user_project_config": proj_config, 
                   "verify": verify,
                   "auth": auth, 
                   "non_nc": non_nc, 
                   "mountpoints": mountpoints,
                   "disable_citation": disable_citation,
                   "disable_further_info": disable_further_info,
                   "disable_qaqc" : config.get("disable_qaqc", False),
                   "kerchunk" : config.get("kerchunk", None)
                   }

        if auth and cert:
            argdict["cert"] = cert
            
        if project and "none" not in project:
            argdict["proj"] = project
            
        project = project.lower()
        if project == "cmip6":
            if pub.cmor_path is None:
                try:
                    argdict["cmor_tables"] = config['cmor_path']
                except:
                    publog.exception("No path for CMOR tables defined. Use --cmor-tables option or define in config file.")
                    exit(1)
            else:
                argdict["cmor_tables"] = pub.cmor_path
        if project == "cmip6" or project == "input4mips" or (project in proj_config and "pid_prefix" in proj_config[project]):  
                # Unpack the PID credentials format from the yaml to be compatible with the legacy format
            pid_creds = config.get('pid_creds', [])
            creds_lst = []
            for it in pid_creds:
                rec = pid_creds[it]
                rec['url'] = it
                creds_lst.append(rec)
            argdict['pid_creds'] = creds_lst
        if "cmip6_clone" in config and project == config['cmip6_clone'].lower():
            if "pid_creds" in argdict:
                argdict["cmip6-clone"] = project
            if not argdict["user_project_config"]:
                argdict["user_project_config"] = {}
            argdict["user_project_config"]["clone_project"] = "cmip6"
        if "enable_archive" in config and config.get("enable_archive", False):
            try:
                argdict["enable_archive"] = True

                argdict["archive_path"] = config["archive_location"]
                argdict["archive_path_length"] = config["archive_depth"]
                if not os.path.isdir(argdict["archive_path"]):
                    publog.exception(f"Error with archive path {argdict['archive_path']}")
                    exit(1)
            except:
                publog.exception("Configuration file error: check archive (and other) settings")
                exit(1)
        else:
            argdict["enable_archive"] = False

        if "https_url" in config:
            argdict["https_url"] = config["https_url"]

        if config.get("globus_index", False):
            argdict["globus_index"] = True
            argdict["index_UUID"] = config.get("index_UUID", "")
        else:
            argdict["index_UUID"] =""
    
        argdict["dry_run"] = config.get("dry_run", pub.dry_run)
        
        if "skip_opendap" in config:
            argdict["skip_opendap"] = config["skip_opendap"]

        argdict["stac_config"] = config.get("stac_config",{})
        stac_api = pub.stac_api
        if stac_api:
            if not argdict.get("stac_config"):
                argdict["stac_api"] = stac_api
            elif "stac_transaction_api" in argdict["stac_config"]:
                argdict["stac_config"]["stac_transaction_api"]["base_url"]
            else:
                publog.warning("STAC API not properly configured. ")
                argdict["stac_api"] = stac_api

        argdict["skipxr"] = pub.skipxr
        argdict["save_stac"] = config.get("save_stac",pub.save_stac)
        
        return argdict


