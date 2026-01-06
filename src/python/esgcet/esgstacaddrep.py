import argparse
import json
import os
import sys
from pathlib import Path

import esgcet.args as pub_args
import esgcet.logger as logger
from esgcet.stac_client import TransactionClient
from esgcet.stac_converter import convert2stac

log = logger.ESGPubLogger()
publog = log.return_logger("esgstacpub")


def add_replica(stac_item, rep_datanode, rep_globus, rep_path, rep_hostname):
    assets = stac_item.get("assets", {})
    for name, asset in assets.items():
        if asset.get("alternate:name") == rep_datanode:
            continue

        if "alternate" not in asset:
            asset["alternate"] = {}

        if rep_datanode in asset.get("alternate"):
            continue

        replica_asset = {
            "description": asset.get("description"),
            "type": asset.get("type"),
            "roles": asset.get("roles", []),
            "alternate:name": rep_datanode,
        }

        if name == "globus":
            replica_asset["href"] = (
                f"https://app.globus.org/file-manager?"
                f"origin_id={rep_globus}&origin_path={rep_path}"
            )

        elif asset.get("type") == "application/netcdf":
            filename = asset["href"].split("/")[-1]
            replica_asset["href"] = f"https://{rep_hostname}{rep_path}/{filename}"

        asset["alternate"][rep_datanode] = replica_asset

    return stac_item


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
        required=True,
        help="UUID of Globus collection to access replicated item",
    )
    parser.add_argument(
        "--rep-path", dest="rep_path", required=True, help="Path to replicated item"
    )
    parser.add_argument(
        "--http-hostname",
        dest="rep_hostname",
        required=True,
        help="Hostname of the HTTP server",
    )
    parser.add_argument(
        "--datanode",
        dest="rep_datanode",
        required=True,
        help="Datanode that iwll be used to identify replicated assets of the item",
    )
    parser.add_argument(
        "--config",
        "-cfg",
        dest="cfg",
        default=def_config,
        help="Path to yaml config file.",
    )
    parser.add_argument(
        "--silent", dest="silent", action="store_true", help="Enable silent mode."
    )
    parser.add_argument(
        "--verbose", dest="verbose", action="store_true", help="Enable verbose mode."
    )
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

    if not a.json_data:
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

    rc = True
    tc = TransactionClient(a.stac_api, silent=silent, verbose=verbose)

    if a.json_data:
        try:
            new_json_data = json.load(open(a.json_data))
        except:
            publog.exception("Could not open json file. Exiting.")
            exit(1)
        try:
            stac_item = convert2stac(new_json_data)
            stac_item = add_replica(
                stac_item, a.rep_datanode, a.rep_globus, a.rep_path, a.rep_hostname
            )
            rc = rc and tc.put(stac_item)
        except Exception as ex:
            publog.exception("Failed to publish replica to STAC Transaction API")
            exit(1)
    if not rc:
        exit(1)


def main():
    run()


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
