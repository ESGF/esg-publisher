esgupdate
=========

The ``esgupdate`` command checks to see if the dataset being published is already in our database. If it is, it uses the metadata produced by the other commands to update the record.
The output is the published data along with a success message upon success.

Usage
-----

``esgupdate`` is used with the follwing syntax::

    esgupdate --pub-rec <JSON file>

where ``<JSON file>`` is the output of the ``esgpidcitepub`` command.

Additional command line options are as follows::

        usage: esgupdate [-h] [--index-node INDEX_NODE] [--certificate CERT]
                         --pub-rec JSON_DATA [--ini CFG] [--silent]
                         [--verbose] [--no-auth] [--verify]

        Publish data sets to ESGF databases.

        optional arguments:
            -h, --help            show this help message and exit
            --index-node INDEX_NODE
                                  Specify index node.
            --certificate CERT, -c CERT
                                  Use the following certificate file in .pem form for publishing (use a myproxy login to generate).
            --pub-rec JSON_DATA   JSON file output from esgpidcitepub or esgmkpubrec.
            --ini CFG, -i CFG     Path to config file.
            --silent              Enable silent mode.
            --verbose             Enable verbose mode.
            --no-auth             Run publisher without certificate, only works on certain index nodes.
            --verify              Toggle verification for publishing, default is off.


You can also define most of these options in the config file if you choose.
