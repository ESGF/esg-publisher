from abc import ABC, abstractmethod

from esgcet.globus_query import ESGGlobusQuery
from esgcet.globus_search import GlobusSearch

class ESGUpdateGlobus:

    def __init__(self, index_UUID : str, data_node : str, silent : bool = False, verbose : bool = False):
        self._index_UUID = index_UUID
        self._query = ESGGlobusQuery(self._index_UUID, data_node)

    def update_file(self, dsetid : str):
        # Check cache
        #
        gs = GlobusSearch({})
        #gs.check_cache()   

        filerecs = self._query.query_file_records(dsetid)
        gs.set_doc(filerecs)
        res = gs.convert2esgf2(True)
        gs.extern_globus_publish(res, self._index_UUID)
        # publish file recs

    def update_dataset(self, dsetid : str):

        gs = GlobusSearch(self._dataset_ctx)        
        res = gs.convert2esgf2(True)
        gs.extern_globus_publish(res, self._index_UUID)

    def query_update(self,  master_id : str):
        
   
        res = self._query.dataset_query_master(master_id)
        if (res):
            self._dataset_ctx = res
            subject = res[0]  # todo get subject
            return subject
        else:
            return ""
        
        
        
