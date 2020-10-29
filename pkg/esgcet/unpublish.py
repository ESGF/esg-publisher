from esgcet.pub_client import publisherClient
import sys, json
from esgcet.settings import INDEX_NODE, CERT_FN, DATA_NODE

# TODO 1 Get from config file instead of settings (or args)
hostname = INDEX_NODE
cert_fn = CERT_FN
data_node = DATA_NODE

ARGS = 1

def run(args):

    if len(args) < (ARGS):
        print("Missing required arguments")
        exit(0)

    if len(args) > 1 and '--delete' in args:
        do_delete = True
    else:
        do_delete = False

    dset_id =  args[-1]

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

