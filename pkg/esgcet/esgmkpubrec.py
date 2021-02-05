import esgcet.mk_dataset as mkd
import argparse
from pathlib import Path
import configparser as cfg
import sys
import json
import os


def get_args():
    parser = argparse.ArgumentParser(description="Publish data sets to ESGF databases.")
    home = str(Path.home())
    def_config = home + "/.esg/esg.ini"
    parser.add_argument("--set-replica", dest="set_replica", action="store_true", help="Enable replica publication.")
    parser.add_argument("--no-replica", dest="no_replica", action="store_true", help="Disable replica publication.")
    parser.add_argument("--scan-file", dest="scan_file", required=True, help="JSON output file from autocurator.")
    parser.add_argument("--json", dest="json", default=None, help="Load attributes from a JSON file in .json form. The attributes will override any found in the DRS structure or global attributes.")
    parser.add_argument("--data-node", dest="data_node", default=None, help="Specify data node.")
    parser.add_argument("--index-node", dest="index_node", default=None, help="Specify index node.")
    parser.add_argument("--map-data", dest="map_data", required=True, help="Mapfile json data converted using esgmapconv.")
    parser.add_argument("--ini", "-i", dest="cfg", default=def_config, help="Path to config file.")
    parser.add_argument("--out-file", dest="out_file", default=None, help="Optional output file destination. Default is stdout.")
    parser.add_argument("--silent", dest="silent", action="store_true", help="Enable silent mode.")
    parser.add_argument("--verbose", dest="verbose", action="store_true", help="Enable verbose mode.")

    pub = parser.parse_args()

    return pub


def run():

    a = get_args()
    ini_file = a.cfg
    config = cfg.ConfigParser()
    config.read(ini_file)

    p = True
    if a.out_file is not None:
        p = False
        outfile = a.out_file

    if not a.silent:
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

    if not a.verbose:
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

    try:
        map_json_data = json.load(open(a.map_data, 'r'))
    except:
        print("Error with argparse. Exiting.", file=sys.stderr)
        exit(1)

    try:
        scanfn = a.scan_file
    except:
        print("Error with argparse. Exiting.", file=sys.stderr)
        exit(1)

    if a.data_node is None:
        try:
            data_node = config['user']['data_node']
        except:
            print("Error: data node not supplied in config or command line. Exiting.", file=sys.stderr)
            exit(1)
    else:
        data_node = a.data_node

    if a.index_node is None:
        try:
            index_node = config['user']['index_node']
        except:
            print("Error: index node not supplied in config or command line. Exiting.", file=sys.stderr)
            exit(1)
    else:
        index_node = a.index_node

    if a.set_replica and a.no_replica:
        print("Error: replica publication simultaneously set and disabled.", file=sys.stderr)
        exit(1)
    elif a.set_replica:
        replica = True
    elif a.no_replica:
        replica = False
    else:
        try:
            r = config['user']['set_replica']
            if 'yes' in r or 'true' in r:
                replica = True
            elif 'no' in r or 'false' in r:
                replica = False
            else:
                print("Config file error: set_replica must be true, false, yes, or no.", file=sys.stderr)
                exit(1)
        except:
            print("Set_replica not defined. Use --set-replica or --no-replica or define in config file.", file=sys.stderr)
            exit(1)

    try:
        data_roots = json.loads(config['user']['data_roots'])
        if data_roots == 'none':
            print("Data roots undefined. Define in config file to create file metadata.", file=sys.stderr)
            exit(1)
    except:
        print("Data roots undefined. Define in config file to create file metadata.", file=sys.stderr)
        exit(1)

    try:
        globus = json.loads(config['user']['globus_uuid'])
    except:
        # globus undefined
        globus = "none"

    try:
        dtn = config['user']['data_transfer_node']
    except:
        # dtn undefined
        dtn = "none"

    third_arg_mkd = False
    if a.json is not None:
        json_file = a.json
        third_arg_mkd = True


    try:
        if third_arg_mkd:
            out_json_data = mkd.run([map_json_data, scanfn, data_node, index_node, replica, data_roots, globus, dtn, silent, verbose, json_file])
        else:
            out_json_data = mkd.run([map_json_data, scanfn, data_node, index_node, replica, data_roots, globus, dtn, silent, verbose])
    except Exception as ex:
        print("Error making dataset: " + str(ex), file=sys.stderr)
        exit(1)

    if p:
        print(json.dumps(out_json_data, indent=4))
    else:
        with open(outfile, 'w') as of:
            json.dump(out_json_data, of, indent=4)


def main():
    run()


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
