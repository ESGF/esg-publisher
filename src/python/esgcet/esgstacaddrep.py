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
        "--rep-path", dest="rep_path", required=True, help="Path to replicated item"
    )
    parser.add_argument(
        "--http-hostname",
        dest="rep_hostname",
        help="Hostname of the HTTP server if different from the data node",
    )
    parser.add_argument(
        "--datanode",
        dest="rep_datanode",
        help="Datanode that will be used to identify replicated assets of the item",
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

    if a.json_data:
        try:
            new_json_data = json.load(open(a.json_data))
        except:
            publog.exception("Could not open json file. Exiting.")
            exit(1)
        try:
            sc = ESGSTACConverter(config["stac_config"])
            si = sc.convert2stac(new_json_data)
            stac_item = ESGSTACItem(si)
            stac_item.add_replica(a.rep_datanode, a.rep_globus, a.rep_path, a.rep_hostname)
            rc = rc and tc.put(stac_item.stac_item)
            
        except Exception as ex:
            publog.exception(f"Failed to publish replica to STAC Transaction API {ex}")
            exit(1)
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

        #si = sc.stac_item_fetch(a.dataset_id)
        stac_item = ESGSTACItem(si)
        if a.rep_datanode:
            site = a.rep_datanode
        else:
            site = config["data_node"]
        if a.agg:

                operations = [
                        entry = {
                            "op": "add",
                            "path": f"/assets/{site}",
                            "value": {
                                "alternate": {
                                    site: {
                                        "href": a.rep_path,
                                        "type": a.agg,
                                        "roles": roles,
                                        "description": description,
                                        "alternate:name": site,
                                    }
                                },
                            }
                        }
                ]
                response = tc.json_patch(
                        "CMIP6",
                        item_id=item_id,
                        entry={
                            "operations": operations
                        },
            

            #stac_item.add_aggregate(a.agg, a.rep_path, site)
        else:
            patch_entry = {}
            
            stac_item.add_replica(a.rep_datanode, a.rep_globus, a.rep_path, a.rep_hostname)
        
        rc = rc and tc.json_patch(collection, a.datasetid, patch_entry)    
    if not rc:
        exit(1)


def main():
    rc = run()
    if not rc:
        exit(1)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
