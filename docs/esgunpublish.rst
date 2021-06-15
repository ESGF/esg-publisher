esgunpublish
============

The ``esgunpublish`` command retracts, or, upon specification, deletes a specified dataset. The output of this command is either a success or failure message
accompanied with the id of the dataset that was retracted. Exercise caution when deleting datasets as, if replicas have been made or if you will be republishing,
you should retract rather than delete outright.

Usage
-----

``esgunpublish`` is used with the following syntax::

    esgunpublish --dset-id <dataset_id>

You can also specify certain command line options rather than defining them in a config file::

    usage: esgunpublish [-h] [--index-node INDEX_NODE] [--data-node DATA_NODE]
                    [--certificate CERT] [--delete] --dset-id DSET_ID
                    [--ini CFG]

    Unpublish data sets from ESGF databases.

    optional arguments:
        -h, --help            show this help message and exit
        --index-node INDEX_NODE
                              Specify index node.
        --data-node DATA_NODE
                              Specify data node.
        --certificate CERT, -c CERT
                              Use the following certificate file in .pem form for
                              unpublishing (use a myproxy login to generate).
        --delete              Specify deletion of dataset (default is retraction).
        --dset-id DSET_ID     Dataset ID for dataset to be retracted or deleted.
        --ini CFG, -i CFG     Path to config file.

You can see this message above by running ``esgunpublish -h``.
