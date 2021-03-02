import esgcet.pid_cite_pub as pid
import argparse
import sys
import json
from pathlib import Path
import configparser as cfg
import os


def get_args():
    parser = argparse.ArgumentParser(description="Publish data sets to ESGF databases.")
    home = str(Path.home())
    def_config = home + "/.esg/esg.ini"
    parser.add_argument("--data-node", dest="data_node", default=None, help="Specify data node.")
    parser.add_argument("--pub-rec", dest="json_data", required=True,
                        help="Dataset and file json data; output from esgmkpubrec.")
    parser.add_argument("--ini", "-i", dest="cfg", default=def_config, help="Path to config file.")
    parser.add_argument("--out-file", dest="out_file", default=None,
                        help="Optional output file destination. Default is stdout.")
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

    if a.data_node is None:
        try:
            data_node = config['user']['data_node']
        except:
            print("Error: data node not supplied in config or command line. Exiting.", file=sys.stderr)
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

    if a.data_node is None:
        try:
            data_node = config['user']['data_node']
        except:
            print("Error: data node not supplied in config or command line. Exiting.", file=sys.stderr)
            exit(1)
    else:
        data_node = a.data_node

    try:
        pid_creds = json.loads(config['user']['pid_creds'])
    except:
        print("PID credentials not defined. Define in config file esg.ini.", file=sys.stderr)
        exit(1)

    try:
        out_json_data = json.load(open(a.json_data))
    except:
        print("Error opening JSON file. Exiting.", file=sys.stderr)
        exit(1)

    try:
        new_json_data = pid.run([out_json_data, data_node, pid_creds, silent, verbose])
    except Exception as ex:
        print("Error running pid cite: " + str(ex), file=sys.stderr)
        exit(1)

    if p:
        print(json.dumps(new_json_data, indent=4))
    else:
        with open(outfile, 'w') as of:
            json.dump(new_json_data, of, indent=4)


def main():
    run()


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
