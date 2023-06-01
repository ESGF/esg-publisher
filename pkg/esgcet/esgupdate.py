import os
from esgcet.update import ESGPubUpdate
import sys
import json
import argparse
from pathlib import Path
import esgcet.args as pub_args
import esgcet.logger as logger

log = logger.ESGPubLogger()
publog = log.return_logger('esgupdate')


def get_args():
    parser = argparse.ArgumentParser(description="Publish data sets to ESGF databases.")

    home = str(Path.home())
    def_config = home + "/.esg/esg.yaml"
    parser.add_argument("--index-node", dest="index_node", default=None, help="Specify index node.")
    parser.add_argument("--certificate", "-c", dest="cert", default="./cert.pem",
                        help="Use the following certificate file in .pem form for publishing (use a myproxy login to generate).")
    parser.add_argument("--pub-rec", dest="json_data", required=True,
                        help="JSON file output from esgpidcitepub or esgmkpubrec.")
    parser.add_argument("--config", "-cfg", dest="cfg", default=def_config, help="Path to yaml config file.")
    parser.add_argument("--silent", dest="silent", action="store_true", help="Enable silent mode.")
    parser.add_argument("--verbose", dest="verbose", action="store_true", help="Enable verbose mode.")
    parser.add_argument("--no-auth", dest="no_auth", action="store_true",
                        help="Run publisher without certificate, only works on certain index nodes.")
    parser.add_argument("--verify", dest="verify", action="store_true",
                        help="Toggle verification for publishing, default is off.")

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

    if a.cert == "./cert.pem":
        try:
            cert = config['cert']
        except:
            cert = a.cert
    else:
        cert = a.cert

    if a.verify:
        verify = True
    else:
        verify = False

    if a.no_auth:
        auth = False
    else:
        auth = True

    if a.index_node is None:
        try:
            index_node = config['index_node']
        except:
            publog.exception("Index node not defined. Use the --index-node option or define in esg.ini.")
            exit(1)
    else:
        index_node = a.index_node

    try:
        new_json_data = json.load(open(a.json_data))
    except:
        publog.exception("Could not open json file. Exiting.")
        exit(1)

    up = ESGPubUpdate(index_node, cert, silent=silent, verbose=verbose, verify=verify,
                      auth=auth)
    try:
        up.run(new_json_data)
    except Exception as ex:
        publog.exception("Failed to update record")
        exit(1)


def main():
    run()


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
