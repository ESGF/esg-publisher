import esgcet.unpublish as upub
import os
import sys
import json
import argparse
import configparser as cfg
from pathlib import Path


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
    parser.add_argument("--ini", "-i", dest="cfg", default=def_config, help="Path to config file.")

    pub = parser.parse_args()

    return pub


def run():
    a = get_args()
    ini_file = a.cfg
    config = cfg.ConfigParser()
    try:
        config.read(ini_file)
    except:
        print("WARNING: no config file found.", file=sys.stderr)

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
            print("Index node not defined. Use the --index-node option or define in esg.ini.", file=sys.stderr)
            exit(1)
    else:
        index_node = a.index_node

    if a.data_node is None:
        try:
            data_node = config['user']['data_node']
        except:
            print("Data node not defined. Use the --data-node option or define in esg.ini.", file=sys.stderr)
            exit(1)
    else:
        data_node = a.data_node

    dset_id = a.dset_id

    if a.delete:
        d = True
    else:
        d = False

    try:
        upub.run([dset_id, d, data_node, index_node, cert])
    except Exception as ex:
        print("Error unpublishing: " + str(ex), file=sys.stderr)
        exit(1)


def main():
    run()


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
