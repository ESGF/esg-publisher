from pub_client import publisherClient

import list2json, sys, json
import args
from settings import INDEX_NODE, CERT_FN


def main(outdata):



    #	hostname = args[1]
    #	cert_fn = args[3]
    pub = args.get_args()
    hostname = pub.index_node
    cert_fn = pub.cert
    pubCli = publisherClient(cert_fn, hostname)

    d = outdata

    for rec in d:

        new_xml = list2json.gen_xml(rec)
        pubCli.publish(new_xml)
#        print(new_xml)
