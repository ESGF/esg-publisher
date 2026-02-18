from abc import ABC, abstractmethod
import esgcet.logger as logger

log = logger.ESGPubLogger()

from pystac_client import Client
from esgcet.stac_client import getTransactionClient
from esgcet.update_base import ESGUpdateBase

FIELDNAME = "base_id"


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

    def update_dataset(self, dsetid : str, update_dict={}, set_latest=False):


        operations = []
        
        if not (set_latest):
            op =                     {
                        "op": "replace",
                        "path": "/properties/latest",
                        "value": set_latest
                    }
            operations.append(op) 

                
        # Use STAC property in update not legacy field names from Solr-era
        if update_dict:
            for k in update_dict:
    #                props[k] = update_dict[k]
                op =                     {
                        "op": "replace",
                        "path": "/properties/{k}",
                        "value": update_dict[k]
                    }
                operations.append(op) 

        

        response = tc.json_patch(
                        "CMIP7",
                        item_id=item_id,
                        entry={
                            "operations": operations
                        },
                )


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
        
        
        



