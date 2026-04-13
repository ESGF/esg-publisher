from abc import ABC, abstractmethod
import esgcet.logger as logger

log = logger.ESGPubLogger()

from pystac_client import Client
from esgcet.stac_client import getTransactionClient
from esgcet.update_base import ESGUpdateBase

FIELDNAME = "base_id"


class ESGUpdateSTAC(ESGUpdateBase):


    def __init__(self, config):
        ESGUpdateBase.__init__(self, silent=config.get("silent", False), verbose=config.get("verbose", False))


        self.stacclient = Client.open(config.get("stac_config", {}).get("stac_api"))
        self.dry_run = config.get("dry_run")
        self.trans_client = getTransactionClient(config.get("stac_config",{}))(config)


    def update_file(self, dsetid : str):
        """
        Irrelevant 
        """
        pass

    def update_assets(self, dsetid : str, asset_info):
        operations = []
        site = asset_info["site"]
        op = {
        "op" : "add",
            "path": f"/assets/reference_file/alternate",
                        "value": {
                                site: {
                                    "href": asset_info["href"],
                                    "type": asset_info["type"],
                                    "roles": ["data"],
                                    "description": "TEST",
                                    "alternate:name": site,
                                }
                            }
        }
        
        collection = self.collection
        operations.append(op)
        response = self.trans_client.json_patch(collection, dsetid, operations)
        # Do something with response?
        return response
        
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

        
        entry = operations  
        #{ "operations": operations}
        collection = self.collection
        response = self.trans_client.json_patch(collection, dsetid, entry)


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
                    "op": "=", "args": [{"property": "properties.title"}, master_id]
                },
                {
                    "op": "=", "args": [{"property": "properties.latest"}, True]} ]

                }
                
        resp = self.stacclient.search(collections=[collection],filter=filt, max_items=1)

        if resp.matched() < 1:
            return False
        elif resp.matched() > 1:
            log.warn("Multiple latest {}")

        for it in resp.items_as_dicts():
            d = it
#        d = l[0].to_dict()
        self.stac_item = d
        self.collection = collection
        return d["id"]
        
        
        



