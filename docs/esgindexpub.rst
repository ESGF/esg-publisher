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

<<<<<<< HEAD
    usage: esgindexpub [-h] [--index-node INDEX_NODE] [--certificate CERT] 
                        --pub-rec JSON_DATA [--config CFG] [--silent]
=======
    usage: esgindexpub [-h] [--index-node INDEX_NODE] [--certificate CERT]
                        --pub-rec JSON_DATA [--ini CFG] [--silent]
>>>>>>> refactor-esgf
                        [--verbose] [--no-auth] [--verify]

    Publish data sets to ESGF databases.

    optional arguments:
        -h, --help            show this help message and exit
        --index-node INDEX_NODE
                              Specify index node.
        --certificate CERT, -c CERT
                              Use the following certificate file in .pem form for publishing (use a myproxy login to generate).
        --pub-rec JSON_DATA   JSON file output from esgpidcitepub or esgmkpubrec.
        --config CFG, -cfg CFG     Path to config file.
        --silent              Enable silent mode.
        --verbose             Enable verbose mode.
        --no-auth             Run publisher without certificate, only works on certain index nodes.
        --verify              Toggle verification for publishing, default is off.
        --xml-list            Publish directly from xml files listed (supply a file containing paths to the files).

Use the command line option ``-h`` to see the message above.  Note that the ``--xml-list`` option is intended to be used following the use of the "enable_archive" setting and the presence of "archived" publication records in xml format (see :ref:`arch_info`).  Before use of the ``esgindxpub`` command in this context, create a list of these files to supply to the command.
