from esgcet.pub_client import publisherClient

import esgcet.list2json, sys, json, os
import configparser as cfg
from pathlib import Path

config = cfg.ConfigParser()
home = str(Path.home())
config_file = home + "/.esg/esg.ini"
config.read(config_file)

try:
    s = config['user']['silent']
    if 'true' in s or 'yes' in s:
        SILENT = True
    else:
        SILENT = False
except:
    SILENT = False
try:
    v = config['user']['verbose']
    if 'true' in v or 'yes' in v:
        VERBOSE = True
    else:
        VERBOSE = False
except:
    VERBOSE = False

def run(args):

    if len(args) < 1:
        print("usage: esgindexpub <JSON file with dataset output>")
        exit(1)

    if len(args) == 3:
        hostname = args[1]
        cert_fn = args[2]
        d = args[0]
    else:
        try:
            hostname = config['user']['index_node']
        except:
            print("Index node not defined. Define in esg.ini.", file=sys.stderr)
            exit(1)

        try:
            cert_fn = config['user']['cert']
        except:
            print("Certificate file not found. Define in esg.ini.", file=sys.stderr)
            exit(1)
        d = json.load(open(args[0]))

    pubCli = publisherClient(cert_fn, hostname, verbose=VERBOSE)

    for rec in d:

        new_xml = esgcet.list2json.gen_xml(rec)
        if not SILENT:
            print(new_xml)
        pubCli.publish(new_xml)


def main():
    run(sys.argv[1:])


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
