import esgcet.util.logger as logger

log = logger.ESGPubLogger()

from esgcet.stac.stac_client import getTransactionClient
from esgcet.util.update_base import ESGUpdateBase
from pystac_client import Client

FIELDNAME = "base_id"


class ESGUpdateSTAC(ESGUpdateBase):

    def __init__(self, config):
        ESGUpdateBase.__init__(
            self,
            silent=config.get("silent", False),
            verbose=config.get("verbose", False),
        )

        self.stacclient = Client.open(config.get("stac_config", {}).get("stac_api"))
        self.dry_run = config.get("dry_run")
        self.trans_client = getTransactionClient(config.get("stac_config", {}))(config)

    def update_file(self, dsetid: str):
        """
        Irrelevant
        """
        pass

    def update_assets(self, dsetid: str, asset_info):
        operations = []
        site = asset_info["site"]
        op = {
            "op": "add",
            "path": "/assets/reference_file/alternate",
            "value": {
                site: {
                    "href": asset_info["href"],
                    "type": asset_info["type"],
                    "roles": ["data"],
                    "description": "TEST",
                    "alternate:name": site,
                }
            },
        }

        collection = self.collection
        operations.append(op)
        response = self.trans_client.json_patch(collection, dsetid, operations)
        # Do something with response?
        return response

    def update_dataset(self, dsetid: str, update_dict={}, set_latest=False):

        self.set_collection(dsetid)
        operations = []

        if not (set_latest):
            op = {"op": "replace", "path": "/properties/latest", "value": set_latest}
            operations.append(op)

        # Use STAC property in update not legacy field names from Solr-era
        if update_dict:
            for k in update_dict.get("properties", {}):
                #                props[k] = update_dict[k]
                op = {
                    "op": "replace",
                    "path": f"/properties/{k}",
                    "value": update_dict[k],
                }
                operations.append(op)
            for it in update_dict.get("links", []):
                op = {"op": "add", "path": "/links", "value": it}
                operations.append(op)

        entry = operations
        response = self.trans_client.json_patch(self.collection, dsetid, entry)

    def set_collection(self, msid):
        parts = msid.split(".")
        if parts[0] == "MIP-DRS7":
            self.collection = parts[1]
        else:
            self.collection = parts[0]

    def query_update(self, data_node: str, master_id: str):

        self.set_collection(master_id)
        filt = {
            "op": "and",
            "args": [
                {"op": "=", "args": [{"property": "properties.title"}, master_id]},
                {"op": "=", "args": [{"property": "properties.latest"}, True]},
            ],
        }

        resp = self.stacclient.search(
            collections=[self.collection], filter=filt, max_items=1
        )

        if resp.matched() < 1:
            return False
        elif resp.matched() > 1:
            log.warn("Multiple latest {}")
        d = {}
        for it in resp.items_as_dicts():
            d = it
        #        d = l[0].to_dict()
        if not "id" in d:
            return False
        self.stac_item = d
        
        return d.get("id")
