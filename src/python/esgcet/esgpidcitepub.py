from esgcet.pid_cite_pub import ESGPubPidCite
import argparse
import sys
import json
from pathlib import Path
import os
import esgcet.args as pub_args
import esgcet.logger as logger

log = logger.ESGPubLogger()
publog = log.return_logger('esgpidcitepub')


def get_args():
    parser = argparse.ArgumentParser(description="Publish data sets to ESGF databases.")
    home = str(Path.home())
    def_config = home + "/.esg/esg.yaml"
    parser.add_argument("--data-node", dest="data_node", default=None, help="Specify data node.")
    parser.add_argument("--pub-rec", dest="json_data", required=True,
                        help="Dataset and file json data; output from esgmkpubrec.")
    parser.add_argument("--config", "-cfg", dest="cfg", default=def_config, help="Path to yaml config file.")
    parser.add_argument("--out-file", dest="out_file", default=None,
                        help="Optional output file destination. Default is stdout.")
    parser.add_argument("--silent", dest="silent", action="store_true", help="Enable silent mode.")
    parser.add_argument("--verbose", dest="verbose", action="store_true", help="Enable verbose mode.")
    parser.add_argument("--test", dest="test", action="store_true",
                        help="PID registration will run in 'test' mode. Use this mode unless you are performing 'production' publications.")

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

    p = True
    if a.out_file is not None:
        p = False
        outfile = a.out_file

    if a.data_node is None:
        try:
            data_node = config['data_node']
        except:
            publog.exception("Data node not supplied in config or command line. Exiting.")
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

    if a.data_node is None:
        try:
            data_node = config['data_node']
        except:
            publog.exception("Data node not supplied in config or command line. Exiting.")
            exit(1)
    else:
        data_node = a.data_node

    test = False
    if a.test:
        test = True

    try:
        pid_creds = config['pid_creds']
    except:
        publog.exception("PID credentials not defined. Define in config file.")
        exit(1)

    try:
        out_json_data = json.load(open(a.json_data))
    except:
        publog.exception("Could not open JSON file. Exiting.")
        exit(1)

    pid = ESGPubPidCite(out_json_data, pid_creds, data_node, test=test, silent=silent,
                        verbose=verbose)

    try:
        new_json_data = pid.do_pidcite()
    except Exception as ex:
        publog.exception("Failed assigning pid or running activity check")
        exit(1)

    if p:
        print(json.dumps(new_json_data))
    else:
        with open(outfile, 'w') as of:
            json.dump(new_json_data, of)


def main():
    run()


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
