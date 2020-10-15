esgindexpub
===========

The ``esgindexpub`` command publishes the data record using the metadata produced by the other commands to the ``index_node`` defined in the config file.
The output of this command will display published data along with a success message upon success.

Usage
-----

``esgindexpub`` is used with the following syntax::

    esgindexpub --pub-rec <JSON file>

where ``<JSON file>`` is the output of the ``esgpidcitepub`` command.

You can also use the other command line options to configure some variables outside of the config file (or to define where to find the config file)::

    usage: esgindexpub [-h] [--index-node INDEX_NODE] [--certificate CERT] --pub-rec JSON_DATA [--ini CFG]

    Publish data sets to ESGF databases.

    optional arguments:
        -h, --help            show this help message and exit
        --index-node INDEX_NODE
                              Specify index node.
        --certificate CERT, -c CERT
                              Use the following certificate file in .pem form for publishing (use a myproxy login to generate).
        --pub-rec JSON_DATA   JSON file output from esgpidcitepub or esgmkpubrec.
        --ini CFG, -i CFG     Path to config file.

Use the command line option ``-h`` to see the message above.