from abc import ABC, abstractmethod


from esgcet.globus_query import ESGGlobusQuery
from esgcet.globus_search import GlobusSearchIngest
from esgcet.update_base import ESGUpdateBase

class ESGUpdateGlobus(ESGUpdateBase):

    def __init__(self, index_UUID : str, data_node : str, silent : bool = False, verbose : bool = False, dry_run : bool = False):
        ESGUpdateBase.__init__(self, silent=silent, verbose=verbose)
        self._index_UUID = index_UUID
        self._query = ESGGlobusQuery(self._index_UUID, data_node)
        self._dry_run = dry_run

    def update_file(self, dsetid : str):
        # Check cache
        #
        gs = GlobusSearchIngest({})
        #gs.check_cache()   

        filerecs = self._query.query_file_records(dsetid)
        gs.set_doc(filerecs)
        res = gs.run(True)
        if not self._dry_run:
            gs.extern_globus_publish(res, self._index_UUID)
        else:
            print(f"DEBUG dry run {res}")
        # publish file recs

    def update_dataset(self, dsetid : str):

        gs = GlobusSearchIngest([self._dataset_ctx])        
        res = gs.run(True)
        if not self._dry_run:
            gs.extern_globus_publish(res, self._index_UUID)
        else:
            print(f"DEBUG dry run {res}")

    def query_update(self, data_node, master_id : str):
        
   
        res = self._query.dataset_query_master(master_id)
        if (res):
            self._dataset_ctx = res
            print(f"DEBUG {res}")
            subject = res['id']  # todo get subject
            return subject
        else:
            return ""
        
        
        
