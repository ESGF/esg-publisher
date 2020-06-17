from pub_client import publisherClient

import list2json, sys, json

from settings import INDEX_NODE, CERT_FN

hostname = INDEX_NODE
cert_fn = CERT_FN

def main(outfile):



    #	hostname = args[1]
    #	cert_fn = args[3]

    pubCli = publisherClient(cert_fn, hostname)

    d = json.load(open(outfile))

    for rec in d:

        new_xml = list2json.gen_xml(rec)
        pubCli.publish(new_xml)
#        print(new_xml)
