import sys, json
import os
from esgcet.pid_cite_pub import ESGPubPidCite
from esgcet.search_check import ESGSearchCheck
from esgcet.pub_client import publisherClient

import esgcet.logger as logger

log = logger.ESGPubLogger()

import pdb

class ESGUnpublishSolr:

    def __init__(self):
        self.publog = log.return_logger('esgunpublish-2')
    
    def check_for_pid_proj(self, dset_arr):
    
        for dset in dset_arr:
             parts = dset.split('.')
             if parts[0].lower() in ["cmip6", "input4mips"]:
                 return True
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

        searchcheck = ESGSearchCheck(hostname, silent, verbose)

        pub_log = log.return_logger('Unpublish', args["silent"], args["verbose"])
        status = 0

        for dset_id in args["dataset_id_lst"]:
    
            status += self.single_unpublish(dset_id, pub_log, searchcheck)
        return status
    
    def single_unpublish(self, dset_id, pub_log, searchcheck):

        args = self._args
        
        hostname = args["index_node"]
        do_delete = args["delete"]
        data_node = args["data_node"]
        cert_fn = args["cert"]
        auth = args["auth"]

        second_split = []
        if '|' in dset_id:
            first_split = dset_id.split('|')
            second_split = first_split[0].split('.')
            data_node = first_split[1]
        else:
            second_split = dset_id.split('.')
            dset_id_new = '{}|{}'.format(dset_id, data_node)
            dset_id = dset_id_new

        found, notretracted = searchcheck.run_check(dset_id)
    
        if not found:
            return(-1)
        
        if (not notretracted) and (not do_delete):
            pub_log.info("Use --delete to permanently erase the retracted record")
            return(0)
        
        if "pid_creds" in args and self.check_for_pid_proj([dset_id]):
            version = second_split[-1][1:]
            master_id = '.'.join(second_split[0:-1])
            pid_module = ESGPubPidCite({}, args["pid_creds"], data_node, False, args["silent"], args["verbose"])
            ret = pid_module.pid_unpublish(master_id, version)
            if not ret:
                pub_log.warning("PID Module did not return success")
        # ensure that dataset id is in correct format, use the set data node as a default
    
    
        
        pubCli = publisherClient(cert_fn, hostname, auth=auth, verbose=args["verbose"], silent=args["silent"])

        if do_delete:
            pubCli.delete(dset_id)
        else:
            pubCli.retract(dset_id)
        return(0)
