import sys, json, requests
from datetime import datetime
from pathlib import Path
import esgcet.logger as logger

log = logger.ESGPubLogger()

''' Handles setting latest=false for previously published versions, includes finding those in the index
'''
class ESGSearchCheck():


    def __init__(self, index_node,  silent=False, verbose=False, verify=True):
        """
            index_node (string):  The node to search for the update 
            cert_fn (string):  Filename for certicate to use to push updates to the API
            silent (bool):  suppress INFO messages
            verbose (bool):  extended output, useful for debugging
        """
        self.index_node = index_node 
        self.silent = silent
        self.verbose = verbose
        self.verify = verify

        self.SEARCH_TEMPLATE = 'https://{}/esg-search/search/?format=application%2Fsolr%2Bjson&id={}&fields=id,retracted'
        self.publog = log.return_logger('Search Check', silent, verbose)



    def run_check(self, datasetid):
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
