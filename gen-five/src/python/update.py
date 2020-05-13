from pub_client import publisherClient
import sys, json, requests
from settings import INDEX_NODE, CERT_FN

from datetime import datetime

hostname = INDEX_NODE
cert_fn = CERT_FN

ARGS = 1

SEARCH_TEMPLATE = 'http://{}/esg-search/search/?latest=true&distrib=false&format=application%2Fsolr%2Bjson&data_node={}&master_id={}&fields=version,id'

''' The xml to hide the previous version
'''
def gen_hide_xml(id, *args):

    dateFormat = "%Y-%m-%dT%H:%M:%SZ"
    now = datetime.utcnow()
    ts = now.strftime(dateFormat)
    txt =  """<updates core="datasets" action="set">
        <update>
          <query>id={}</query>
          <field name="latest">
             <value>false</value>
          </field>
          <field name="_timestamp">
             <value>{}</value>
          </field>
        </update>
    </updates>
    \n""".format(id, ts)

    return txt

def main(args):

    if len(args) < (ARGS):
        print("Missing required arguments")
        exit(0)

    try:
        input_rec = json.load(open(args[0]))
    except Exception as e:
        print("Error opening input json format {}".format(e))
        exit(1)
    # The dataset record either first or last in the input file
    dset_idx = -1
    if not input_rec[dset_idx]['type'] == 'Dataset':
        dset_idx = 0
    
    if not input_rec[dset_idx]['type'] == 'Dataset':
        print("Could not find the Dataset record.  Malformed input, exiting!")
        exit(1)

    mst = input_rec[dset_idx]['master_id']
    dnode = input_rec[dset_idx]['data_node']

    # query for 
    url = SEARCH_TEMPLATE.format(INDEX_NODE, dnode, mst)

    print(url)
    resp = requests.get(url)

    print (resp.text)
    if not resp.status_code == 200:
        print('Error')
        exit(1)
    
    res = json.loads(resp.text)

    if res['response']['numFound'] > 0:
        docs = res['response']["docs"]
        dsetid = docs[0]['id']
        update_rec = gen_hide_xml( dsetid )
        pubCli = publisherClient(cert_fn, hostname)
        print (update_rec)
        pubCli.update(update_rec)
        print('INFO: Found previous version, updating the record: {}'.format(dsetid))

    else:
        print('INFO: First dataset version for {}.'.format(mst))




if __name__ == '__main__':
    main(sys.argv[1:])
