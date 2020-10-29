from esgcet.pub_client import publisherClient
import sys, json
from esgcet.settings import INDEX_NODE, CERT_FN, DATA_NODE


def run(args):

    dset_id = args[0]
    do_delete = args[1]
    data_node = args[2]
    hostname = args[3]
    cert_fn = args[4]


    # ensure that dataset id is in correct format, use the set data node as a default
    if not '|' in dset_id:

        dset_id_new = '{}|{}'.format(dset_id, data_node)
        dset_id = dset_id_new
        
    pubCli = publisherClient(cert_fn, hostname)

    if do_delete:
        pubCli.delete(dset_id)
    else:
        pubCli.retract(dset_id)

def main():
    run(sys.argv[1:])


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()

