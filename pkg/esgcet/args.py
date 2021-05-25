import argparse
from pathlib import Path
import os, sys, json
import esgcet.esgmigrate as em
import configparser as cfg
from esgcet.settings import *


DEFAULT_ESGINI = '/esg/config/esgcet'


class PublisherArgs:

    def __init__(self):
        pass

    def get_args(self):
        parser = argparse.ArgumentParser(description="Publish data sets to ESGF databases.")

        # ANY FILE NAME INPUT: check first to make sure it exists
        home = str(Path.home())
        def_config = home + "/.esg/esg.ini"
        parser.add_argument("--test", dest="test", action="store_true", help="PID registration will run in 'test' mode. Use this mode unless you are performing 'production' publications.")
        # replica stuff new... hard-coded, modify mk dataset so that it imports it instead
        parser.add_argument("--set-replica", dest="set_replica", action="store_true", help="Enable replica publication.")
        parser.add_argument("--no-replica", dest="no_replica", action="store_true", help="Disable replica publication.")
        parser.add_argument("--esgmigrate", dest="migrate", action="store_true", help="Run esgmigrate before publishing, to migrate over old config. May be left with incomplete config settings.")
        parser.add_argument("--json", dest="json", default=None, help="Load attributes from a JSON file in .json form. The attributes will override any found in the DRS structure or global attributes.")
        parser.add_argument("--data-node", dest="data_node", default=None, help="Specify data node.")
        parser.add_argument("--index-node", dest="index_node", default=None, help="Specify index node.")
        parser.add_argument("--certificate", "-c", dest="cert", default="./cert.pem", help="Use the following certificate file in .pem form for publishing (use a myproxy login to generate).")
        parser.add_argument("--project", dest="proj", default="", help="Set/overide the project for the given mapfile, for use with selecting the DRS or specific features, e.g. PrePARE, PID.")
        parser.add_argument("--cmor-tables", dest="cmor_path", default=None, help="Path to CMIP6 CMOR tables for PrePARE. Required for CMIP6 only.")
        parser.add_argument("--autocurator", dest="autocurator_path", default=None, help="Path to autocurator repository folder.")
        parser.add_argument("--map", dest="map", required=True, nargs="+", help="Mapfile or list of mapfiles.")
        parser.add_argument("--ini", "-i", dest="cfg", default=def_config, help="Path to config file.")
        parser.add_argument("--silent", dest="silent", action="store_true", help="Enable silent mode.")
        parser.add_argument("--verbose", dest="verbose", action="store_true", help="Enable verbose mode.")
        parser.add_argument("--no-auth", dest="no_auth", action="store_true", help="Run publisher without certificate, only works on certain index nodes.")
        parser.add_argument("--verify", dest="verify", action="store_true", help="Toggle verification for publishing, default is off.")

        pub = parser.parse_args()

        return pub

    def get_dict(self, fullmap):

        pub = self.get_args()
        json_file = pub.json

        if pub.migrate:
            em.run({})

        ini_file = pub.cfg
        config = cfg.ConfigParser()
        config_file = ini_file
        try:
            config.read(config_file)
        except Exception as ex:
            if not os.path.exists(ini_file):
                print("No config file found. Attempting to migrate old settings.")
                em.run(DEFAULT_ESGINI, False, False)
            else:
                print("Error opening config file: " + str(ex))
                exit(1)

        if pub.proj != "":
            project = pub.proj
        else:
            try:
                project = config['user']['project']
            except:
                project = None

        if not pub.silent:
            try:
                s = config['user']['silent']
                if 'true' in s or 'yes' in s:
                    silent = True
                else:
                    silent = False
            except:
                silent = False
        else:
            silent = True

        if not pub.verbose:
            try:
                v = config['user']['verbose']
                if 'true' in v or 'yes' in v:
                    verbose = True
                else:
                    verbose = False
            except:
                verbose = False
        else:
            verbose = True

        if pub.cert == "./cert.pem":
            try:
                cert = config['user']['cert']
            except:
                cert = pub.cert
        else:
            cert = pub.cert

        conda_auto = False
        if pub.autocurator_path is None:
            try:
                autocurator = config['user']['autoc_path']
                if autocurator == "autocurator":
                    conda_auto = True
            except:
                autocurator = "autocurator"
                conda_auto = True
        else:
            autocurator = pub.autocurator_path

        if pub.index_node is None:
            try:
                index_node = config['user']['index_node']
            except:
                print("Index node not defined. Use the --index-node option or define in esg.ini.", file=sys.stderr)
                exit(1)
        else:
            index_node = pub.index_node

        if pub.data_node is None:
            try:
                data_node = config['user']['data_node']
            except:
                print("Data node not defined. Use --data-node option or define in esg.ini.", file=sys.stderr)
                exit(1)
        else:
            data_node = pub.data_node
        try:
            data_roots = json.loads(config['user']['data_roots'])
            if data_roots == 'none':
                print("Data roots undefined. Define in esg.ini to create file metadata.", file=sys.stderr)
                exit(1)
        except:
            print("Data roots undefined. Define in esg.ini to create file metadata.", file=sys.stderr)
            exit(1)

        try:
            globus = config['user']['globus_uuid']
        except:
            globus = "none"

        try:
            dtn = config['user']['data_transfer_node']
        except:
            dtn = "none"

        skip_prepare = False

        try:
            skip_prep_str = config['user']['skip_prepare'].lower()
            skip_prepare = (skip_prep_str in ["true", "yes"])
        except:
            pass
        if pub.set_replica and pub.no_replica:
            print("Error: replica publication simultaneously set and disabled.", file=sys.stderr)
            exit(1)
        elif pub.set_replica:
            replica = True
        elif pub.no_replica:
            replica = False
        else:
            try:
                r = config['user']['set_replica'].lower()
                if 'yes' in r or 'true' in r:
                    replica = True
                elif 'no' in r or 'false' in r:
                    replica = False
                else:
                    print("Config file error: set_replica must be true, false, yes, or no.", file=sys.stderr)
                    exit(1)
            except:
                print("Set_replica not defined. Use --set-replica or --no-replica or define in esg.ini.",
                      file=sys.stderr)
                exit(1)

        test = False
        if pub.test:
            test = True

        if not conda_auto:
            autoc_command = autocurator + "/bin/autocurator"  # concatenate autocurator command
        else:
            autoc_command = autocurator
        
        try:
            proj_config = json.loads(config['user']['user_project_config'])
        except:
            proj_config = None


        os.system("cert_path=" + cert)

        if pub.verify:
            verify = True
        else:
            verify = False

        if pub.no_auth:
            auth = False
        else:
            auth = True

        if globus == "none" and not silent:
            print("INFO: no Globus UUID defined. Using default: " + GLOBUS_UUID, file=sys.stderr)

        if dtn == "none" and not silent:
            print("INFO: no data transfer node defined. Using default: " + DATA_TRANSFER_NODE, file=sys.stderr)

        argdict = {"fullmap": fullmap, "silent": silent, "verbose": verbose,
                   "cert": cert,
                   "autoc_command": autoc_command, "index_node": index_node, "data_node": data_node,
                   "data_roots": data_roots, "globus": globus, "dtn": dtn, "replica": replica, "proj": project,
                   "json_file": json_file, "test": test, "user_project_config": proj_config, "verify": verify,
                   "auth": auth}

        if project == "CMIP6":
            if pub.cmor_path is None:
                try:
                    argdict["cmor_tables"] = config['user']['cmor_path']
                except:
                    print("No path for CMOR tables defined. Use --cmor-tables option or define in config file.",
                          file=sys.stderr)
                    exit(1)
            else:
                argdict["cmor_tables"] = pub.cmor_path
        try:
            argdict["pid_creds"] = json.loads(config['user']['pid_creds'])
        except:
            print("PID credentials not defined. Define in config file esg.ini.", file=sys.stderr)
            exit(1)

        return argdict
