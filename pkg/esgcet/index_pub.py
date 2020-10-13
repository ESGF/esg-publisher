from esgcet.pub_client import publisherClient

import esgcet.list2json, sys, json, os
import configparser as cfg
from pathlib import Path


def run(args):

    hostname = args[1]
    cert_fn = args[2]
    d = args[0]
    silent = args[3]
    verbose = args[4]


    pubCli = publisherClient(cert_fn, hostname, verbose=verbose)

    for rec in d:

        new_xml = esgcet.list2json.gen_xml(rec)
        if not silent:
            print(new_xml)
        pubCli.publish(new_xml)

