from esgcet.pub_client import publisherClient
import sys, json

from esgcet.pid_cite_pub import ESGPubPidCite

import esgcet.logger as logger

log = logger.Logger()


def run(args):

    dset_id = args[0]
    do_delete = args[1]
    data_node = args[2]
    hostname = args[3]
    cert_fn = args[4]
    auth = args[5]
    verbose = args[6]    
    silent = args[7]
    #  args[8]  are the pid_creds see below
    dataset = {}

    logger = log.return_logger('Unpublish', silent, verbose)

    second_split = []
    if '|' in dset_id:
        first_split = dset_id.split('|')
        second_split = first_split[0].split('.')
        data_node = first_split[1]
    else:
        second_split = dset_id.split('.')
        dset_id_new = '{}|{}'.format(dset_id, data_node)
        dset_id = dset_id_new

    if len(args) > 8:
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


def main():
    run(sys.argv[1:])


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()

