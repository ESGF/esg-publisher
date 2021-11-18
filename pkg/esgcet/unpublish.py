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

    dparts = dset_id.split('.')

    if '|' in dparts[-1]:

        lastsplit = dparts[-1].split('|')
        dataset["version"] = lastsplit[0][1:]
        data_node = lastsplit[1]
    else:
        dataset["version"] = dparts[-1][1:]

    dataset['data_node'] = data_node
    dataset['master_id'] = '.'.join(dparts[0:-1])

    if len(args) > 8:
        pid_module = ESGPubPidCite(dataset, args[8], data_node, False, silent, verbose)
        ret = pid_module.pid_unpublish()
        if not ret:
            logger.warning("PID Module did not return success")
    # ensure that dataset id is in correct format, use the set data node as a default
    if not '|' in dset_id:

        dset_id_new = '{}|{}'.format(dset_id, data_node)
        dset_id = dset_id_new
        
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

