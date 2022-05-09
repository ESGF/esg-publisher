import esgcet.unpublish as upub
import os
import sys
import json
import argparse
import configparser as cfg
from pathlib import Path
import esgcet.logger as logger

from esgcet.mapfile import ESGPubMapConv

log = logger.Logger()
publog = log.return_logger('esgunpublish')

import esgcet

def get_args():
    parser = argparse.ArgumentParser(description="Unpublish data sets from ESGF databases.")

    home = str(Path.home())
    def_config = home + "/.esg/esg.ini"
    parser.add_argument("--index-node", dest="index_node", default=None, help="Specify index node.")
    parser.add_argument("--data-node", dest="data_node", default=None, help="Specify data node.")
    parser.add_argument("--certificate", "-c", dest="cert", default="./cert.pem",
                        help="Use the following certificate file in .pem form for unpublishing (use a myproxy login to generate).")
    parser.add_argument("--delete", dest="delete", action="store_true", help="Specify deletion of dataset (default is retraction).")
    parser.add_argument("--dset-id", dest="dset_id", default=None,
                        help="Dataset ID for dataset to be retracted or deleted.")
    parser.add_argument("--map", dest="map", default=None, nargs="+",
                        help="Path(s) to a mapfile or directory(s) containing mapfiles.")    
    parser.add_argument("--use-list", dest="dset_list", default=None,
                        help="Path to a file containing list of dataset_ids.")
    parser.add_argument("--ini", "-i", dest="cfg", default=def_config, help="Path to config file.")
    parser.add_argument("--version", action="version", version=f"esgunpublish v{esgcet.__version__}",help="Print the version and exit")
    parser.add_argument("--no-auth", dest="no_auth", action="store_true", help="Run publisher without certificate, only works on certain index nodes.")
    parser.add_argument("--silent", dest="silent", action="store_true", help="Enable silent mode.")
    parser.add_argument("--verbose", dest="verbose", action="store_true", help="Enable verbose mode.")

    pub = parser.parse_args()

    return pub


def map_to_dataset(fullmap):

    mapconv = ESGPubMapConv(fullmap)
    map_json_data = None
    try:
        map_json_data = mapconv.mapfilerun()
        return map_json_data[0][0].replace("#",".v") 
    except Exception as ex:
        return None


def maps_to_dataset_list(maps):
    dset_list = []
    for m in maps:
        if os.path.isdir(m):
            os.listdir(m)
            if os.path.isdir(m):
                files = os.listdir(m)
                for f in files:
                    if os.path.isdir(m + f):
                        continue
                    dataset_id = map_to_dataset(m + f)
                    if not dataset_id is None:
                        dset_list.append(dataset_id)
        else:
            dataset_id = map_to_dataset(m)
            dset_list.append(dataset_id)

    return dset_list


def run():
    a = get_args()

    ini_file = a.cfg
    config = cfg.ConfigParser()
    if not os.path.exists(ini_file):
        publog.error("Config file not found. " + ini_file + " does not exist.")
        exit(1)
    if os.path.isdir(ini_file):
        publog.error("Config file path is a directory. Please use a complete file path.")
        exit(1)
    try:
        config.read(ini_file)
    except Exception as ex:
        publog.exception("Could not read config file")
        exit(1)


    if a.cert == "./cert.pem":
        try:
            cert = config['user']['cert']
        except:
            cert = a.cert
    else:
        cert = a.cert

    if a.index_node is None:
        try:
            index_node = config['user']['index_node']
        except:
            publog.exception("Index node not defined. Use the --index-node option or define in esg.ini.")
            exit(1)
    else:
        index_node = a.index_node


    dset_id = ""

    if a.dset_id:

        dset_id = a.dset_id

    if not '|' in dset_id or (a.map):
        if a.data_node is None:
            try:
                data_node = config['user']['data_node']
            except:
                publog.exception("Data node not defined. Use the --data-node option or define in esg.ini.")
                exit(1)
        else:
            data_node = a.data_node
    else:
        data_node = None


    if a.delete:
        d = True
    else:
        d = False

    if a.no_auth:
        auth = False
    else:
        auth = True

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
        if not a.silent:
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
        silent = False


    args = {    "delete": d, 
             "data_node": data_node, 
             "index_node": index_node, 
             "cert": cert, 
             "auth" :auth, 
             "verbose" : verbose,
             "silent" :silent }


    if len(dset_id) > 0:
        args["dataset_id_lst"] = [dset_id]
    elif a.map:

        args["dataset_id_lst"] = maps_to_dataset_list(a.map)
    elif a.dset_list:
        try:
            dset_arr = [line.rstrip() for line in open(a.dset_list)]
        except:
            publog.exception(f"Error opening {args['dset_list']} file.")

        args["dataset_id_lst"] = dset_arr
    else:
        publog.error("No unpublish input method specified.  Please use from one of the following arguments: --map --use-list --dset-id ; type esgunpublish --help for more info")
        exit(1)

    if (upub.check_for_pid_proj(args["dataset_id_lst"])):
        try:
            pid_creds = json.loads(config['user']['pid_creds'])
            args["pid_creds"] = pid_creds
        except:
            publog.exception("PID credentials not defined. Define in config file esg.ini.")
            exit(1)    

    status = 0
    try:
        status = upub.run(args)
    except Exception as ex:
        publog.exception("Failed to unpublish")
        exit(1)
    exit(status)

def main():
    run()


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
