from esgcet.pub_client import publisherClient
import sys, json, requests
from esgcet.settings import INDEX_NODE, CERT_FN
import configparser as cfg
from datetime import datetime
from pathlib import Path

ARGS = 1
silent = False
verbose = False

SEARCH_TEMPLATE = 'https://{}/esg-search/search/?latest=true&distrib=false&format=application%2Fsolr%2Bjson&data_node={}&master_id={}&fields=version,id'

''' The xml to hide the previous version
'''


def gen_hide_xml(id, type):
    dateFormat = "%Y-%m-%dT%H:%M:%SZ"
    now = datetime.utcnow()
    ts = now.strftime(dateFormat)
    idfield = "id"
    if type == "files":
        idfield = "dataset_id"
    txt = """<updates core="{}" action="set">
        <update>
          <query>{}={}</query>
          <field name="latest">
             <value>false</value>
          </field>
          <field name="_timestamp">
             <value>{}</value>
          </field>
        </update>
    </updates>
    \n""".format(type, idfield, id, ts)

    return txt


def run(args):
    global silent
    global verbose

    input_rec = args[0]
    index_node = args[1]
    cert_fn = args[2]
    silent = args[3]
    verbose = args[4]

    # The dataset record either first or last in the input file
    dset_idx = -1
    if not input_rec[dset_idx]['type'] == 'Dataset':
        dset_idx = 0

    if not input_rec[dset_idx]['type'] == 'Dataset':
        print("Error: could not find the Dataset record.  Malformed input, exiting!", file=sys.stderr)
        exit(1)

    mst = input_rec[dset_idx]['master_id']
    dnode = input_rec[dset_idx]['data_node']

    # query for
    url = SEARCH_TEMPLATE.format(index_node, dnode, mst)

    if verbose:
        print("Search Url: '{}'".format(url))
    resp = requests.get(url)

    if verbose:
        print(resp.text)
    if not resp.status_code == 200:
        print('Error: received {} from index server.'.format(resp.status_code), file=sys.stderr)
        exit(1)

    res = json.loads(resp.text)

    if res['response']['numFound'] > 0:
        docs = res['response']["docs"]
        dsetid = docs[0]['id']
        update_rec = gen_hide_xml(dsetid, "datasets")
        pubCli = publisherClient(cert_fn, index_node, verbose=verbose, silent=silent)
        if verbose:
            print(update_rec)
        pubCli.update(update_rec)
        update_rec = gen_hide_xml(dsetid, "files")
        if verbose:
            print(update_rec)
        pubCli.update(update_rec)
        if not silent:
            print('INFO: Found previous version, updating the record: {}'.format(dsetid))

    else:
        if not silent:
            print('INFO: First dataset version for {}.'.format(mst))
