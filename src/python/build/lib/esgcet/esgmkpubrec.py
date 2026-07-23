from esgcet.args import PublisherArgs
import argparse
from pathlib import Path
import sys
import esgcet.args as pub_args
import json
import os
import esgcet.logger as logger

log = logger.ESGPubLogger()
publog = log.return_logger('esgmkpubrec')

from esgcet.mk_dataset_autoc import ESGPubAutocHandler
from esgcet.mk_dataset_xarray import ESGPubXArrayHandler

def get_args():
    parser = argparse.ArgumentParser(description="Publish data sets to ESGF databases.")

    # ANY FILE NAME INPUT: check first to make sure it exists
    home = str(Path.home())
    def_config = home + "/.esg/esg.yaml"
    parser.add_argument("--set-replica", dest="set_replica", action="store_true", help="Enable replica publication.")
    parser.add_argument("--no-replica", dest="no_replica", action="store_true", help="Disable replica publication.")
    parser.add_argument("--json", dest="json", default=None,
                        help="Load attributes from a JSON file in .json form. The attributes will override any found in the DRS structure or global attributes.")
    parser.add_argument("--scan-file", dest="scan_file", help="JSON output file from autocurator.  If not set will use XArray to load data from files")
    parser.add_argument("--map-data", dest="map_data", required=True,
                        help="Mapfile json data converted using esgmapconv.")
    parser.add_argument("--out-file", dest="out_file", default=None,
                        help="Optional output file destination. Default is stdout.")
    parser.add_argument("--data-node", dest="data_node", default=None, help="Specify data node.")
    parser.add_argument("--index-node", dest="index_node", default=None, help="Specify index node.")
    parser.add_argument("--project", dest="proj", default="",
                        help="Set/overide the project for the given mapfile, for use with selecting the DRS or specific features, e.g. PrePARE, PID.")
    parser.add_argument("--config", "-cfg", dest="cfg", default=def_config, help="Path to yaml config file.")
    parser.add_argument("--silent", dest="silent", action="store_true", help="Enable silent mode.")
    parser.add_argument("--verbose", dest="verbose", action="store_true", help="Enable verbose mode.")

    pub = parser.parse_args()

    return pub


def run():

    a = get_args()
    ini_file = a.cfg
    if not os.path.exists(ini_file):
        publog.error("Config file not found. " + ini_file + " does not exist.")
        exit(1)
    if os.path.isdir(ini_file):
        publog.error("Config file path is a directory. Please use a complete file path.")
        exit(1)
    args = pub_args.PublisherArgs()
    config = args.load_config(ini_file)

    p = True
    if a.out_file is not None:
        p = False
        outfile = a.out_file

    if not a.silent:
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
        
    if not a.verbose:
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

    try:
        map_json_data = json.load(open(a.map_data, 'r'))
    except:
        publog.exception("Missing required  Exiting.")
        exit(1)

    scanarg = a.scan_file
    
    if scanarg:
        format_handler = ESGPubAutocHandler
    else:
        format_handler = ESGPubXArrayHandler
        scanarg = format_handler.xarray_load(map_json_data)

    if a.data_node is None:
        try:
            data_node = config['data_node']
        except:
            publog.exception("Data node not supplied in config or command line. Exiting.")
            exit(1)
    else:
        data_node = a.data_node

    if a.index_node is None:
        try:
            index_node = config['index_node']
        except:
            publog.exception("Index node not supplied in config or command line. Exiting.")
            exit(1)
    else:
        index_node = a.index_node

    if a.set_replica and a.no_replica:
        publog.exception("Replica publication simultaneously set and disabled.")
        exit(1)
    elif a.set_replica:
        replica = True
    elif a.no_replica:
        replica = False
    else:
        try:
            r = config['set_replica']
            if 'yes' in r or 'true' in r:
                replica = True
            elif 'no' in r or 'false' in r:
                replica = False
            else:
                publog.error("Set_replica must be true, false, yes, or no.")
                exit(1)
        except:
            publog.exception("Set_replica not defined. Use --set-replica or --no-replica or define in config file.")
            exit(1)

    try:
        data_roots = config['data_roots']
        if data_roots == 'none':
            publog.error("Data roots undefined. Define in config file to create file metadata.")
            exit(1)
    except:
        publog.exception("Data roots undefined. Define in config file to create file metadata.")
        exit(1)

    try:
        globus = json.loads(config['globus_uuid'])
    except:
        # globus undefined
        globus = "none"

    try:
        dtn = config['data_transfer_node']
    except:
        # dtn undefined
        dtn = "none"

    json_file = None
    if a.json is not None:
        json_file = a.json

    if a.proj != "":
        project = a.proj
    else:
        try:
            project = config['project']
        except:
            project = None

    try:
        non_netcdf = config['non_netcdf'].lower()
        if 'yes' in non_netcdf or 'true' in non_netcdf:
            non_nc = True
        else:
            non_nc = False
    except:
        non_nc = False

    try:
        proj_config = json.loads(config['user_project_config'])
    except:
        proj_config = None


    construct = None

    if project == "create-ip":
        from esgcet.mkd_create_ip import ESGPubMKDCreateIP
        construct = ESGPubMKDCreateIP
    elif project == "cmip5":
        from esgcet.mkd_cmip5 import ESGPubMKDCmip5
        construct = ESGPubMKDCmip5
    elif project == "input4mips":
        from esgcet.mkd_input4mips import ESGPubMKDinput4MIPs
        construct = ESGPubMKDinput4MIPs
    elif non_nc:
        from esgcet.mkd_non_nc import ESGPubMKDNonNC
        construct = ESGPubMKDNonNC
    else:
        from esgcet.mk_dataset import ESGPubMakeDataset
        construct = ESGPubMakeDataset
    mkd = construct(data_node, index_node, replica, globus, data_roots, dtn, format_handler, silent, verbose)

    try:
        if non_nc:
            out_json_data = mkd.get_records(map_json_data, json_file)
        else:
            out_json_data = mkd.get_records(map_json_data, scanarg, json_file, user_project=proj_config)

    except Exception as ex:
        publog.exception("Failed to make dataset")
        exit(1)

    if p:
        print(json.dumps(out_json_data))
    else:
        with open(outfile, 'w') as of:
            json.dump(out_json_data, of)


def main():
    run()


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
