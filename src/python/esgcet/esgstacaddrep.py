import argparse
import json
import os
import sys
from pathlib import Path

import esgcet.args as pub_args
import esgcet.logger as logger
from esgcet.stac_client import getTransactionClient
from esgcet.stac_converter import ESGSTACConverter, ESGSTACItem

from esgcet.search_check import ESGSearchCheck

log = logger.ESGPubLogger()
publog = log.return_logger("esgstacpub")
    


def get_args():
    parser = argparse.ArgumentParser(
        description="Publish data sets to ESGF STAC Transaction API."
    )

    home = str(Path.home())
    def_config = home + "/.esg/esg.yaml"
    parser.add_argument(
        "--stac-api",
        dest="stac_api",
        default=None,
        help="Specify STAC Transaction API.",
    )
    parser.add_argument(
        "--pub-rec",
        dest="json_data",
        default=None,
        help="JSON file output from esgpidcitepub or esgmkpubrec.",
    )
    parser.add_argument(
        "--globus-collection-uuid",
        dest="rep_globus",
        help="UUID of Globus collection to access replicated item",
    )
    parser.add_argument(
        "--datanode",
        dest="rep_datanode",
        help="Datanode that will be used to identify replicated assets of the item",
    )
    parser.add_argument(
        "--rep-url", dest="rep_path", help="Url of reference file asset to add"
    )    
    parser.add_argument(
        "--prefix", dest="rep_prefix", help="Url path prefix that proceeds the dataset DRS in the url"
    )    
    parser.add_argument(
        "--config",
        "-cfg",
        dest="cfg",
        default=def_config,
        required=True,
        help="Path to yaml config file.",
    )
    parser.add_argument(
        "--silent", dest="silent", action="store_true", help="Enable silent mode."
    )
    parser.add_argument(
        "--verbose", dest="verbose", action="store_true", help="Enable verbose mode."
    )
    parser.add_argument('--agg', help="Add an aggregtion of the specified type [zarr|kerchunk|virtualizarr|icechunk]. --rep-path is the url for the item", default=None)
    parser.add_argument('--dataset-id', help="ID of the dataset to add the asset (aggregate or files)", default=None)
    pub = parser.parse_args()

    return pub


def run():
    a = get_args()

    ini_file = a.cfg
    if not os.path.exists(ini_file):
        publog.error("Config file not found. " + ini_file + " does not exist.")
        exit(1)
    if os.path.isdir(ini_file):
        publog.error(
            "Config file path is a directory. Please use a complete file path."
        )
        exit(1)
    args = pub_args.PublisherArgs()
    config = args.load_config(ini_file)

    if (not a.json_data) and (not a.dataset_id):
        publog.error(
            "Input data argument missing.  Please provide either records in .json form for esgf2 publishing"
        )
        exit(1)

    if not a.silent:
        try:
            s = config["silent"]
            if "true" in s or "yes" in s:
                silent = True
            else:
                silent = False
        except:
            silent = False
    else:
        silent = True

    if not a.verbose:
        try:
            v = config["verbose"]
            if "true" in v or "yes" in v:
                verbose = True
            else:
                verbose = False
        except:
            verbose = False
    else:
        verbose = True


    config["verbose"] = verbose
    config["silent"] = silent
    
    rc = True
    client = getTransactionClient(config["stac_config"])
    tc = client(config)

    if a.rep_datanode:
        site = a.rep_datanode
    else:
        site = config["data_node"]
    
    
    if a.json_data:
        try:
            new_json_data = json.load(open(a.json_data))
        except:
            publog.exception("Could not open json file. Exiting.")
            exit(1)
        collection = new_json_data[-1]["project"]
        datasetid = new_json_data[-1]["instance_id"]
        
    elif a.dataset_id:
        if a.stac_api:
            stac_api = a.stac_api
        else:
            stac_conf = config.get("stac_config", {})
            stac_api = stac_conf.get("stac_api","") 
            if not stac_api:
                publog.exception("STAC API not set cannot fetch Item")
                exit(1)
        sc = ESGSearchCheck(stac_api=stac_api, verbose=verbose, silent=silent)

        si = sc.stac_item_fetch(a.dataset_id)
        
        stac_item = ESGSTACItem(si)
        collection = si["collection"]
        datasetid = a.dataset_id
    else:
        publog.warn("No Dataset-ID specified in command line")
        return
    if a.agg:

        operations = stac_item.add_aggregate(a.agg, a.rep_path, site)
        print(f"DEBUG {operations}")
        
        rc = tc.json_patch(
                collection,
                item_id=a.dataset_id,
            entry=operations
        ) 
        print(f"DEBUG {rc}")
    else:
        if "https_url" in config:
            http_template = config["https_url"].split('|')[0]
        else:
            http_template = f"https://{site}/thredds/fileServer/{a.rep_prefix}" + "/{}/{}"
        if a.rep_globus:
            rep_globus = a.rep_globus
        else:
            rep_globus = config.get("globus_uuid", "")
        patch_entry = stac_item.add_replica(site, http_template, a.rep_prefix, rep_globus)
        rc = rc and tc.json_patch(collection, datasetid, patch_entry)     
    if not rc:
        exit(1)


def main():
    rc = run()
    if not rc:
        exit(1)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
