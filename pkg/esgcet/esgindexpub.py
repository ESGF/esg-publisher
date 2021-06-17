import sys, json, os
from esgcet.index_pub import ESGPubIndex
import argparse
import configparser as cfg
from pathlib import Path


def get_args():
    parser = argparse.ArgumentParser(description="Publish data sets to ESGF databases.")

    home = str(Path.home())
    def_config = home + "/.esg/esg.ini"
    parser.add_argument("--index-node", dest="index_node", default=None, help="Specify index node.")
    parser.add_argument("--certificate", "-c", dest="cert", default="./cert.pem",
                        help="Use the following certificate file in .pem form for publishing (use a myproxy login to generate).")
    parser.add_argument("--pub-rec", dest="json_data", required=True,
                        help="JSON file output from esgpidcitepub or esgmkpubrec.")
    parser.add_argument("--ini", "-i", dest="cfg", default=def_config, help="Path to config file.")
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
        print("Error: config file not found. " + ini_file + " does not exist.", file=sys.stderr)
        exit(1)
    if os.path.isdir(ini_file):
        print("Config file path is a directory. Please use a complete file path.", file=sys.stderr)
        exit(1)
    config = cfg.ConfigParser()
    try:
        config.read(ini_file)
    except Exception as ex:
        print("Error reading config file: " + str(ex))
        exit(1)

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

    if a.verify:
        verify = True
    else:
        verify = False

    if a.no_auth:
        auth = False
    else:
        auth = True

    ip = ESGPubIndex(index_node, cert, silent=silent, verbose=verbose, verify=verify, auth=auth)
    try:
        new_json_data = json.load(open(a.json_data))
    except:
        print("Error opening json file. Exiting.", file=sys.stderr)
        exit(1)
    try:
        ip.do_publish(new_json_data)
    except Exception as ex:
        print("Error running index pub: " + str(ex), file=sys.stderr)
        exit(1)


def main():
    run()


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()

