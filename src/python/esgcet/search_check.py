import sys, json, requests
from datetime import datetime
from pathlib import Path
import esgcet.logger as logger

log = logger.ESGPubLogger()

''' Handles setting latest=false for previously published versions, includes finding those in the index
'''
class ESGSearchCheck():


    def __init__(self, stac_api="", index_node="",  silent=False, verbose=False, verify=True):
        """
            stac_api = if using STAC set the discovery API
            index_node (string):  The node to search for the update 
            cert_fn (string):  Filename for certicate to use to push updates to the API
            silent (bool):  suppress INFO messages
            verbose (bool):  extended output, useful for debugging
        """
        if stac_api:
            self.stac_api = stac_api
            self.index_node = None
        elif index_node:
            self.index_node = index_node
    
        self.silent = silent
        self.verbose = verbose
        self.verify = verify

        self.SEARCH_TEMPLATE = 'https://{}/esg-search/search/?format=application%2Fsolr%2Bjson&id={}&fields=id,retracted'
        self.publog = log.return_logger('Search Check', silent, verbose)

    def get_stac_item(self):

        return self._stac_item
    
    def run_check(self, datasetid):
    
        if self.index_node:
            res = self._run_check_solr(datasetid)
        else:
            res = self._run_check_stac(datasetid)
    
        return res

    def stac_item_fetch(self, datasetid):
        collection = self._check_collection(datasetid)
        
        req_str = f"{self.stac_api}/collections/{collection}/items/{datasetid}"
        resp = requests.get(req_str)

        if resp.status_code != 200:
            self.publog.info("Dataset not found")            
            return None
        item = resp.json()
        return item
    
    def _check_collection(self, datasetid):
        parts = datasetid.split('.')
        if parts[0] == "MIP-DRS7":
            return "CMIP7"
        else:
            return parts[0]
    
    def _run_check_stac(self, datasetid):

        item = self.stac_item_fetch(datasetid)
        if not item:
            return False, False
        retracted = item["properties"].get("retracted", None)
        if retracted is None:
            raise RuntimeError(f"Retracted property missing for {datasetid}")
        self._stac_item = item
        if retracted:
            self.publog.info("Dataset already retracted")
            return True, False
        return True, True 
        
                
    def _run_check_solr(self, datasetid):
        """ Check a record in the index and peform the updates

            input_rec - a json record to be published containing a "master_id" and "data_node" fields with 
                        a new version
        """
    # The dataset record either first or last in the input file
        # query for
        url = self.SEARCH_TEMPLATE.format(self.index_node, datasetid)

        self.publog.debug("Search Url: '{}'".format(url))
        resp = requests.get(url, verify=self.verify)

        self.publog.debug(resp.text)
        if not resp.status_code == 200:
            self.publog.error('Received {} from index server.'.format(resp.status_code))
            exit(1)

        res = json.loads(resp.text)

        if res['response']['numFound'] > 0:
            docs = res['response']["docs"]
            if len(docs) < 1:
                raise RuntimeError("Error in response from index server, record not found!")
            dsetid = docs[0]['id']
            try:
                retracted = docs[0]['retracted']
            except KeyError: # support older publication without a retracted flag
                retracted = False
            if retracted:
                self.publog.info("Dataset already retracted")
                return True, False
            return True, True
        else:
            self.publog.info("Dataset not found")
            return False, False   
