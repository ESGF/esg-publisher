from esgcet.pub_client import publisherClient
import sys, json, requests
from datetime import datetime
from pathlib import Path
import esgcet.logger as logger

log = logger.ESGPubLogger()

''' Handles setting latest=false for previously published versions, includes finding those in the index
'''
class ESGPubUpdate():


    def __init__(self, index_node, cert_fn="", silent=False, verbose=False, verify=False, auth=False):
        """
            index_node (string):  The node to search for the update 
            cert_fn (string):  Filename for certicate to use to push updates to the API
            silent (bool):  suppress INFO messages
            verbose (bool):  extended output, useful for debugging
        """
        self.index_node = index_node 
        self.cert_fn = cert_fn
        self.silent = silent
        self.verbose = verbose
        self.verify = verify
        self.pubCli = publisherClient(self.cert_fn, self.index_node, verify=verify, verbose=self.verbose, silent=self.silent, auth=auth)

        self.SEARCH_TEMPLATE = 'https://{}/esg-search/search/?latest=true&distrib=false&format=application%2Fsolr%2Bjson&data_node={}&master_id={}&fields=version,id'
        self.publog = log.return_logger('Update Record', silent, verbose)

    def gen_hide_xml(self, id, type):
        ''' Generate the xml to hide the previous version

            id - the full dataset identifier
            type - which core to target: "files" or datasets"
        '''

        dateFormat = "%Y-%m-%dT%H:%M:%SZ"
        now = datetime.utcnow()
        ts = now.strftime(dateFormat)
        idfield = "id"
        if type == "files":
            idfield = "dataset_id"
        txt = f"""<updates core="{type}" action="set">
            <update>
              <query>{idfield}={id}</query>
              <field name="latest">
                 <value>false</value>
              </field>
              <field name="_timestamp">
                 <value>{ts}</value>
              </field>
            </update>
            </updates>
            \n"""

        return txt

    def globus_update():

        # 
        pass         

    def update_core(self, dsetid, type):
        """ For a specific core, generate the xml and run the update.

            id - the full dataset identifier
            type - which core to target: "files" or datasets"
        """
        update_rec = self.gen_hide_xml(dsetid, type)
        self.publog.debug(update_rec)
        self.pubCli.update(update_rec)

    def run(self, input_rec):
        """ Check a record in the index and peform the updates

            input_rec - a json record to be published containing a "master_id" and "data_node" fields with 
                        a new version
        """
    # The dataset record either first or last in the input file
        dset_idx = -1
        if not input_rec[dset_idx]['type'] == 'Dataset':
            dset_idx = 0

        if not input_rec[dset_idx]['type'] == 'Dataset':
            self.publog.error("Could not find the Dataset record.  Malformed input, exiting!")
            exit(1)

        mst = input_rec[dset_idx]['master_id']
        dnode = input_rec[dset_idx]['data_node']

        dsetid = self.query_esg_search(dnode, mst)

        if dsetid:
            self.update_core(dsetid,"datasets")
            self.update_core(dsetid, "files")
            self.publog.info('Found previous version, updating the record: {}'.format(dsetid))

        else:
            version = input_rec[dset_idx]['version']
            self.publog.info('First dataset version for {}: v{}.)'.format(mst, version))


    def query_esg_search(self, dnode, mst):

        # query for
        url = self.SEARCH_TEMPLATE.format(self.index_node, dnode, mst)

        self.publog.debug("Search Url: '{}'".format(url))
        resp = requests.get(url, verify=self.verify)

        self.publog.debug(resp.text)
        if not resp.status_code == 200:
            self.publog.error('Received {} from index server.'.format(resp.status_code))
            exit(1)

        res = json.loads(resp.text)

        if res['response']['numFound'] > 0:
            docs = res['response']["docs"]
            dsetid = docs[0]['id']
            return dsetid
        else:
            return ""
    
