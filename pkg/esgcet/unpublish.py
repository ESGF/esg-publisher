from pub_client import publisherClient
import sys, json
from settings import INDEX_NODE, CERT_FN

hostname = INDEX_NODE
cert_fn = CERT_FN

ARGS = 1

def main(args):

    if len(args) < (ARGS):
        print("Missing required arguments")
        exit(0)

    if len(args) > 1 and '--delete' in args:
        do_delete = True
    else:
        do_delete = False

    dset_id =  args[-1]

    pubCli = publisherClient(cert_fn, hostname)

    if do_delete:
        pubCl.delete(dset_id)
    else:
        pubCli.retract(dset_id)

if __name__ == '__main__':
    main(sys.argv[1:])
