from abc import ABC, abstractmethod
import esgcet.logger as logger

log = logger.ESGPubLogger()

from pystac_client import Client
from stac_client import getTransactionClient

FIELDNAME = "master_id"


class ESGUpdateSTAC(ESGUpdateBase):


    def __init__(self, stac_config, silent=False, verbose=False, dry_run=False):
        ESGUpdateBase.__init__(self, silent=silent, verbose=verbose)


        self.search_client = Client(stac_config.get("stac_api"))
        self._dry_run = dry_run
        self.trans_client = getTransactionClient(stac_config)

    def update_file(self, dsetid : str):
        """
        Irrelevant 
        """
        pass

    def update_dataset(self, dsetid : str, update_dict={}, set_latest=True):
        self.stac_item["properties"]["latest"] = set_latest
        # Use STAC property in update not legacy field names from Solr-era
        if update_dict:
            for k in update_dict:
                props = self.stac_item["properties"]
                if k in props:
                    props[k] = update_dict[k]

        print("WOULD PUT")

        #self.trans_client.put(self.stac_item)
    

    def query_update(self, data_node : str, master_id : str):

        parts = master_id.split('.')
        if parts[0] == "MIP-DRS7":
            collection = parts[1]
        else:
            collection = parts[0]
            
        filt=  { 
                "op": "and",
                "args": [
                {
                    "op": "=", "args": [{"property": f"properties.{FIELDNAME}"}, master_id]
                },
                {
                    "op": "=", "args": [{"property": "properties.latest"}, True]} ]

                }
                
        resp = self.pystac_client.search(collections=[collection],filter=filt, max_items=1)

        if resp.matched() < 1:
            return False
        elif resp.matched() > 1:
            log.warn("Multiple latest {}")
        d = l[0].to_dict()
        self.stac_item = d

        return d["id"]
        
        
        



