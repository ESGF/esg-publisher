import sys, json, os
from esgcet.index_pub import ESGPubIndex
import argparse
from pathlib import Path
import esgcet.logger as logger
import esgcet.args as pub_args

log = logger.ESGPubLogger()
publog = log.return_logger('esgindexpub')


def get_args():
    parser = argparse.ArgumentParser(description="Publish data sets to ESGF databases.")

    home = str(Path.home())
    def_config = home + "/.esg/esg.yaml"
    parser.add_argument("--index-node", dest="index_node", default=None, help="Specify index node.")
    parser.add_argument("--certificate", "-c", dest="cert", default="./cert.pem",
                        help="Use the following certificate file in .pem form for publishing (use a myproxy login to generate).")
    parser.add_argument("--pub-rec", dest="json_data", default=None,
                        help="JSON file output from esgpidcitepub or esgmkpubrec.")
    parser.add_argument("--config", "-cfg", dest="cfg", default=def_config, help="Path to yaml config file.")
    parser.add_argument("--silent", dest="silent", action="store_true", help="Enable silent mode.")
    parser.add_argument("--verbose", dest="verbose", action="store_true", help="Enable verbose mode.")
    parser.add_argument("--no-auth", dest="no_auth", action="store_true",
                        help="Run publisher without certificate, only works on certain index nodes.")
    parser.add_argument("--verify", dest="verify", action="store_true",
                        help="Toggle server certificate verification for publishing, default is off.")
    parser.add_argument("--xml-list", dest="xml_list", default=None,
                        help="Publish directly from xml files listed (supply a file containing paths to the files).")
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

    if not (a.json_data or a.xml_list):
        publog.error("Input data argument missing.  Please provide either records in .json form or a list of xml files for index publishing")
        exit(1)

    if not (a.json_data or a.xml_list):
        publog.error("Input data argument missing.  Please provide either records in .json form or a list of xml files for index publishing")
        exit(1)

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

    if a.index_node is None:
        try:
            index_node = config['index_node']
        except:
            publog.exception("Index node not defined. Use the --index-node option or define in esg.ini.")
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

    rc = True
    ip = ESGPubIndex(index_node, cert, silent=silent, verbose=verbose, verify=verify, auth=auth)

    if a.json_data:
        try:
            new_json_data = json.load(open(a.json_data))
        except:
            publog.exception("Could not open json file. Exiting.")
            exit(1)
        try:
            rc = rc and ip.do_publish(new_json_data)
        except Exception as ex:
            publog.exception("Failed to publish to index node")
            exit(1)
    else:
        try:
            with open(a.xml_list) as inf:
                for line in inf:
                    ip.pub_xml(open(line.strip()).read())
        except Exception as ex:
            publog.exception(f"Index publishing failure: {ex}")
            exit(1)
    if not rc:
        exit(1)

def main():
    run()


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()

