import sys, json
import os
from esgcet.pid_cite_pub import ESGPubPidCite
from esgcet.globus_query import ESGGlobusQuery
from esgcet.globus_search import GlobusSearchIngest


import esgcet.logger as logger

log = logger.ESGPubLogger()

import pdb

class ESGUnpublishGlobus:

    def __init__(self):
        self.publog = log.return_logger('esgunpublish-2')
    
    def check_for_pid_proj(self, dset_arr):
    
        # for dset in dset_arr:
    
        #     parts = dset.split('.')
        #     if parts[0].lower() in ["cmip6", "input4mips"]:
        #         return True            
        
        return False
    
    def run(self, args):

        self._args = args
        hostname = args["index_node"]
        data_node = args["data_node"]
        verbose = args["verbose"]    
        silent = args["silent"]
        auth = args["auth"]
        cert_fn = args["cert"]
        do_delete = args["delete"]
    
        pub_log = log.return_logger('Unpublish', args["silent"], args["verbose"])
        #searchcheck = ESGSearchCheck(hostname, silent, verbose)
        status = 0

        for dset_id in args["dataset_id_lst"]:
    
            status += self.single_unpublish(dset_id, pub_log)
        return status
    
    def single_unpublish(self, dset_id, pub_log):

        args = self._args
        
        hostname = args["index_node"]
        do_delete = args["delete"]
        data_node = args["data_node"]
        cert_fn = args["cert"]
        auth = args["auth"]
        self.UUID = args["index_UUID"]
        second_split = []
        if '|' in dset_id:
            first_split = dset_id.split('|')
            second_split = first_split[0].split('.')
            data_node = first_split[1]
        else:
            second_split = dset_id.split('.')
            dset_id_new = '{}|{}'.format(dset_id, data_node)
            dset_id = dset_id_new
    
    #    found, notretracted = searchcheck.run_check(dset_id)
    
        # if not found:
        #     return(-1)
        query= ESGGlobusQuery(self.UUID, data_node)
        try:
            res = query._post_proc_query([dset_id])
        except:
            return(-1)
            
        if args["deprecate"]:
            self.globus_deprecate(dset_id, query)
            res = query.query_file_records(dset_id, False)
            for x in res:
                self.globus_deprecate(x, query)  
            return (0)

        notretracted = not res["retracted"]
        
        if (not notretracted) and (not do_delete):
            pub_log.info("Use --delete to permanently erase the retracted record")
            return(0)
        
        if "pid_creds" in args and check_for_pid_proj([dset_id]):
            version = second_split[-1][1:]
            master_id = '.'.join(second_split[0:-1])
            pid_module = ESGPubPidCite({}, args["pid_creds"], data_node, False, args["silent"], args["verbose"])
            ret = pid_module.pid_unpublish(master_id, version)
            if not ret:
                pub_log.warning("PID Module did not return success")
        # ensure that dataset id is in correct format, use the set data node as a default
    
    
        
        # pubCli = publisherClient(cert_fn, hostname, auth=auth, verbose=args["verbose"], silent=args["silent"])
        self.data_node = data_node
        if do_delete:
            self.globus_delete_files(dset_id, query)
            self.globus_delete_subj(dset_id)
        else:
            self.globus_retract_files(dset_id, query)
            self.globus_retract_dataset(dset_id, query)
                
        #     pubCli.delete(dset_id)
        # else:
        #     pubCli.retract(dset_id)
        return(0)
    
    
    def globus_deprecate(self, dset_id, query):
        res = query._post_proc_query([dset_id])
        gs = GlobusSearchIngest([res])        

        res3 = gs.run(True, False, True)        
        if not self._args.get("dry_run", False):
            gs.extern_globus_publish(res3, self.UUID)
        else:
            self.publog.info(f"Dry Run publish-deprecate {res3}")

    def globus_retract_dataset(self, dset_id, query):
    
   #     query= ESGGlobusQuery(self.UUID, self.data_node)
        res = query._post_proc_query([dset_id])
        gs = GlobusSearchIngest([res])        

        res3 = gs.run(True, True)
        if not self._args.get("dry_run", False):
            gs.extern_globus_publish(res3, self.UUID)
        else:
            self.publog.info(f"Dry Run publish-retract {res3}")
    
    def globus_delete_files(self, dset_id, query):
        res = query.query_file_records(dset_id, False)
        for x in res:
            self.globus_delete_subj(x)
            
    def globus_retract_files(self, dset_id, query):
        res = query.query_file_records(dset_id, False)
        for x in res:
            self.globus_retract_dataset(x, query)    
        
    def globus_delete_subj(self,  subj):

        if not self._args.get("dry_run", False):
            os.system(f"globus search subject delete {self.UUID} '{subj}'") 
        else:
            self.publog.info(f"Dry Run delete {subj}")
    
