import sys, json
import os
from esgcet.pid_cite_pub import ESGPubPidCite
from esgcet.search_check import ESGSearchCheck

from esgcet.stac_client import getTransactionClient
from esgcet.update_stac import ESGUpdateSTAC

import esgcet.logger as logger

log = logger.ESGPubLogger()

import pdb

class ESGUnpublishSTAC:

    def __init__(self, conf={}):
        self.publog = log.return_logger('esgunpublish-2')
        self.config = conf
    
    def check_for_pid_proj(self, dset_arr):
    
        for dset in dset_arr:
             parts = dset.split('.')
             if parts[0].lower() in ["cmip6", "input4mips"]:
                 return True
        return False
    
    def run(self, args):

        self._args = args
 
        data_node = args["data_node"]
        verbose = args["verbose"]    
        silent = args["silent"]
        do_delete = args["delete"]


        
        try:
            stac_api = self.config["stac_config"]["stac_api"]
        except:
            raise RuntimeError("STAC API not configured.  Ensure you have a correct 'stac_config' entry in your config file.")
            
        searchcheck = ESGSearchCheck(stac_api=stac_api, silent=silent, verbose=verbose)

        pub_log = log.return_logger('Unpublish', args["silent"], args["verbose"])
        status = 0

        if args.get("deprecate", False):
            upd = ESGUpdateSTAC(self.config.get("stac_config"))

            
        for dset_id in args["dataset_id_lst"]:
            if args.get("deprecate", False):
                upd.update_dataset()

            else: 
                status += self.single_unpublish(dset_id, pub_log, searchcheck)
        return status
    
    def single_unpublish(self, dset_id, pub_log, searchcheck):

        args = self._args
        
        do_delete = args["delete"]

        found, notretracted = searchcheck.run_check(dset_id)
    
        if not found:
            return(-1)
        
        if (not notretracted) and (not do_delete):
            pub_log.info("Use --delete to permanently erase the retracted record")
            return(0)
        
        # ensure that dataset id is in correct format, use the set data node as a default
    
    
        transCli = getTransactionClient(self.config.get("stac_config"))        

        return(0)
