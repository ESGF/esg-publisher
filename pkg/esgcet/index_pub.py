from esgcet.pub_client import publisherClient

import esgcet.list2json, sys, json
from esgcet.settings import INDEX_NODE, CERT_FN
import esgcet.args as args
import configparser as cfg


def run(outdata):

    pub = args.get_args()
    config = cfg.ConfigParser()
    config.read('esg.ini')

    if pub.index_node is None:
        try:
            hostname = config['user']['index_node']
        except:
            print("Index node not defined. Use the --index-node option or define in esg.ini.")
    else:
        hostname = pub.index_node

    if pub.cert == "./cert.pem":
        try:
            cert_fn = config['user']['cert']
        except:
            cert_fn = pub.cert
    else:
        cert_fn = pub.cert

    pubCli = publisherClient(cert_fn, hostname)

    d = outdata

    for rec in d:

        new_xml = esgcet.list2json.gen_xml(rec)
        print(new_xml)
        pubCli.publish(new_xml)
#        print(new_xml)

def main():
    run(sys.argv[1:])

if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
