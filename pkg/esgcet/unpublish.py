from esgcet.pub_client import publisherClient
import sys, json

from esgcet.pid_cite_pub import ESGPubPidCite
from esgcet.search_check import ESGSearchCheck
from esgcet.mapfile import ESGPubMapConv

import esgcet.logger as logger

log = logger.Logger()


def map_to_dataset(fullmap):

    mapconv = ESGPubMapConv(fullmap, project=self.project)
    map_json_data = None
    try:
        map_json_data = mapconv.mapfilerun()

    except Exception as ex:
        return None


def run(args):
    
    logger = log.return_logger('Unpublish', silent, verbose)
    status = 0

    if "dataset_id" in args:
        return single_unpublish(args["dataset_id"], args)
    elif "map" in args:
        for m in args["map"]:
            if os.path.isdir(m):
                os.listdir(m)
                if os.path.isdir(m):
                    files = os.listdir(m)
                    for f in files:
                        if os.path.isdir(m + f):
                            continue
                        dataset_id = map_to_dataset(m + f)
                        if dataset_id is None:
                            status += -1
                        else:
                            status += single_unpublish(dataset_id, pub_args)
            else:
                dataset_id = map_to_dataset(m)
                status += single_unpublish

    elif "dset_list" in args:
        try:
            for line in open(args("dset_list")):
                ret = single_unpublish(line.strip())
                status += ret
            if status != 0:
                logger.warning("Some datasets were not found or problem with unpublish")
                exit(1)  
        except:
            logger.exception(f"Error opening {args['dset_list']} file.")
    else:
        logger.warning("No unpublish input method specified.")
        exit(1)

def single_unpublish(dset_id, args):

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
        logger.info("Use --delete to permanently erase the retracted record")
        return(0)

    if pid_creds in args:
        version = second_split[-1][1:]
        master_id = '.'.join(second_split[0:-1])
        pid_module = ESGPubPidCite({}, args[8], data_node, False, silent, verbose)
        ret = pid_module.pid_unpublish(master_id, version)
        if not ret:
            logger.warning("PID Module did not return success")
    # ensure that dataset id is in correct format, use the set data node as a default
        
    pubCli = publisherClient(cert_fn, hostname, auth=auth, verbose=verbose, silent=silent)

    if do_delete:
        pubCli.delete(dset_id)
    else:
        pubCli.retract(dset_id)
    return(0)

def main():
    return run(sys.argv[1:])


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()

