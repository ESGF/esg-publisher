from esgcet.pub_client import publisherClient
import sys, json

from esgcet.pid_cite_pub import ESGPubPidCite
from esgcet.search_check import ESGSearchCheck


import esgcet.logger as logger

log = logger.Logger()




def run(args):
    
    pub_log = log.return_logger('Unpublish', args["silent"], args["verbose"])
    status = 0


    for dset_id in args["dataset_id_lst"]:

        status += single_unpublish(dset_id, args, pub_log)
    return status

def single_unpublish(dset_id, args, pub_log):

    do_delete = args["delete"]

    data_node = args["data_node"]
    hostname = args["index_node"]
    cert_fn = args["cert"]
    auth = args["auth"]
    verbose = args["verbose"]    
    silent = args["silent"]

    second_split = []
    if '|' in dset_id:
        first_split = dset_id.split('|')
        second_split = first_split[0].split('.')
        data_node = first_split[1]
    else:
        second_split = dset_id.split('.')
        dset_id_new = '{}|{}'.format(dset_id, data_node)
        dset_id = dset_id_new

    searchcheck = ESGSearchCheck(hostname, silent, verbose)
    found, notretracted = searchcheck.run_check(dset_id)

    if not found:
        return(-1)

    if (not notretracted) and (not do_delete):
        pub_log.info("Use --delete to permanently erase the retracted record")
        return(0)

    if pid_creds in args:
        version = second_split[-1][1:]
        master_id = '.'.join(second_split[0:-1])
        pid_module = ESGPubPidCite({}, args[8], data_node, False, silent, verbose)
        ret = pid_module.pid_unpublish(master_id, version)
        if not ret:
            pub_log.warning("PID Module did not return success")
    # ensure that dataset id is in correct format, use the set data node as a default
        
    pubCli = publisherClient(cert_fn, hostname, auth=auth, verbose=verbose, silent=silent)

    if do_delete:
        pubCli.delete(dset_id)
    else:
        pubCli.retract(dset_id)
    return(0)


