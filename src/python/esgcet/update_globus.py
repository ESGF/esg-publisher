from abc import ABC, abstractmethod

from esgcet.globus_query import ESGGlobusQuery

class ESGUpdateGlobus:

    def __init__(self, index_UUID : str):
        self._index_UUID = index_UUID

    def update_file(self, dsetid : str):
        pass

    def update_dataset(self, dsetid : str):
        pass

    def query_update(self, data_node : str, master_id : str):
        
        query = ESGGlobusQuery(self._index_UUID, data_node)

        res = query.dataset_query(master_id)
        
        
