import json
import requests
from datetime import datetime

from esgcet.pub_client import publisherClient
from esgcet.update_base import ESGUpdateBase
import esgcet.logger as logger

log = logger.ESGPubLogger()

class ESGUpdateSolr(ESGUpdateBase):

    def __init__(self, index_node : str, cert_fn : str = "", silent : bool = False, verbose : bool = False, verify : bool = False, auth : bool = False):
        self.index_node = index_node
        self.cert_fn = cert_fn
        self.silent = silent
        self.verbose = verbose
        self.verify = verify
        self.pubCli = publisherClient(self.cert_fn, self.index_node, verify=verify, verbose=self.verbose, silent=self.silent, auth=auth)

        self.SEARCH_TEMPLATE = 'https://{}/esg-search/search/?latest=true&distrib=false&format=application%2Fsolr%2Bjson&data_node={}&master_id={}&fields=version,id'
        self.publog = log.return_logger('Update Record', silent, verbose)


    def update_file(self, dsetid : str):
        self._update_core(dsetid, "files")


    def update_dataset(self, dsetid : str):
        self._update_core(dsetid,"datasets")


    def gen_hide_xml(self, id : str, core_type : str):
        ''' Generate the xml to hide the previous version

            id - the full dataset identifier
            core_type - which core to target: "files" or datasets"
        '''

        dateFormat = "%Y-%m-%dT%H:%M:%SZ"
        now = datetime.utcnow()
        ts = now.strftime(dateFormat)
        idfield = "id"
        if core_type == "files":
            idfield = "dataset_id"
        txt = f"""<updates core="{core_type}" action="set">
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

    def query_update(self, dnode : str, mst : str):
        return self._query_esg_search(dnode, mst)

    def _query_esg_search(self, dnode : str, mst : str):

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

    def _update_core(self, dsetid : str, core_type : str):
        """ For a specific core, generate the xml and run the update.

            id - the full dataset identifier
            core_type - which core to target: "files" or datasets"
        """
        update_rec = self.gen_hide_xml(dsetid, core_type)
        self.publog.debug(update_rec)
        self.pubCli.update(update_rec)
