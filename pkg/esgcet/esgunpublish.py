import esgcet.unpublish as upub
import os
import sys
import json
import argparse
import configparser as cfg
from pathlib import Path
import esgcet.logger as logger

log = logger.Logger()
publog = log.return_logger('esgunpublish')


def get_args():
    parser = argparse.ArgumentParser(description="Unpublish data sets from ESGF databases.")

    home = str(Path.home())
    def_config = home + "/.esg/esg.ini"
    parser.add_argument("--index-node", dest="index_node", default=None, help="Specify index node.")
    parser.add_argument("--data-node", dest="data_node", default=None, help="Specify data node.")
    parser.add_argument("--certificate", "-c", dest="cert", default="./cert.pem",
                        help="Use the following certificate file in .pem form for unpublishing (use a myproxy login to generate).")
    parser.add_argument("--delete", dest="delete", action="store_true", help="Specify deletion of dataset (default is retraction).")
    parser.add_argument("--dset-id", dest="dset_id", required=True,
                        help="Dataset ID for dataset to be retracted or deleted.")
    parser.add_argument("--no-auth", dest="no_auth", action="store_true", help="Disable certificate authentication.")
    parser.add_argument("--ini", "-i", dest="cfg", default=def_config, help="Path to config file.")

    pub = parser.parse_args()

    return pub


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

    dset_id = a.dset_id

    if not '|' in dset_id:
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

    try:
        upub.run([dset_id, d, data_node, index_node, cert, auth])
    except Exception as ex:
        publog.exception("Failed to unpublish")
        exit(1)


def main():
    run()


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
