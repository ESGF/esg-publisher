from esgcet.update_base import ESGUpdateBase
import json, requests

class ESGUpdateSolr(ESGUpdateBase):

    def __init__(self):
        pass


    def update_file(self, dsetid):
        self._update_core(dsetid, "files")


    def update_dataset(self, dsetid):
        self._update_core(dsetid,"datasets")

     


    def query_update(self, dnode, mst):
        return self._query_esg_search(dnode, mst)

    def _query_esg_search(self, dnode, mst):

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
        
    def _update_core(self, dsetid, type):
        """ For a specific core, generate the xml and run the update.

            id - the full dataset identifier
            type - which core to target: "files" or datasets"
        """
        update_rec = self.gen_hide_xml(dsetid, type)
        self.publog.debug(update_rec)
        self.pubCli.update(update_rec)