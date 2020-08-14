from esgcet.pub_client import publisherClient

import esgcet.list2json, sys, json
import configparser as cfg


def run(args):

    if len(args) < 1:
        print("usage: esgindexpub <JSON file with dataset output>")
    config = cfg.ConfigParser()
    config.read('esg.ini')

    if len(args) == 3:
        hostname = args[1]
        cert_fn = args[2]
    else:
        try:
            hostname = config['user']['index_node']
        except:
            print("Index node not defined. Define in esg.ini.")
            exit(1)

        try:
            cert_fn = config['user']['cert']
        except:
            print("Certificate file not found. Define in esg.ini.")
            exit(1)

    if isinstance(args[0], str):
        d = json.load(open(args[0]))
    else:
        d = args[0]

    pubCli = publisherClient(cert_fn, hostname)

    for rec in d:

        new_xml = esgcet.list2json.gen_xml(rec)
        print(new_xml)
        pubCli.publish(new_xml)


def main():
    run(sys.argv[1:])


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
