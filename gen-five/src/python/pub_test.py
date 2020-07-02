from pub_client import publisherClient

import list2json, sys, json
import publish_script as ps
from settings import INDEX_NODE, CERT_FN


def main(outdata):



    #	hostname = args[1]
    #	cert_fn = args[3]
    data_node, index_node, replica = ps.get_args()
    hostname = index_node
    cert_fn = ps.get_cert()
    pubCli = publisherClient(cert_fn, hostname)

    d = outdata

    for rec in d:

        new_xml = list2json.gen_xml(rec)
        pubCli.publish(new_xml)
#        print(new_xml)
