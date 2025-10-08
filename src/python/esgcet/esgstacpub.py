import sys, json, os, re
from esgcet.stac_client import TransactionClient
import argparse
from pathlib import Path
from esgcet.settings import STAC_API
import esgcet.logger as logger
import esgcet.args as pub_args

log = logger.ESGPubLogger()
publog = log.return_logger('esgstacpub')

 

def get_args():
    parser = argparse.ArgumentParser(description="Publish data sets to ESGF STAC Transaction API.")

    home = str(Path.home())
    def_config = home + "/.esg/esg.yaml"
    parser.add_argument("--stac-api", dest="stac_api", default=None, help="Specify STAC Transaction API.")
    parser.add_argument("--pub-rec", dest="json_data", default=None,
                        help="JSON file output from esgpidcitepub or esgmkpubrec.")
    parser.add_argument("--config", "-cfg", dest="cfg", default=def_config, help="Path to yaml config file.")
    parser.add_argument("--silent", dest="silent", action="store_true", help="Enable silent mode.")
    parser.add_argument("--verbose", dest="verbose", action="store_true", help="Enable verbose mode.")
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

    if not a.json_data:
        publog.error("Input data argument missing.  Please provide either records in .json form for esgf2 publishing")
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


    rc = True
    tc = TransactionClient(argdict)

    if a.json_data:
        try:
            new_json_data = json.load(open(a.json_data))
        except:
            publog.exception("Could not open json file. Exiting.")
            exit(1)
        try:
            stac_item = tc.convert2stac(new_json_data)
            #publog.warn(json.dumps(stac_item, indent=4))
            rc = rc and tc.publish(stac_item)
        except Exception as ex:
            publog.exception("Failed to publish to STAC Transaction API")
            exit(1)
    if not rc:
        exit(1)


def main():
    run()


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()

