esgpidcitepub
=============

The ``esgpidcitepub`` command connects to a PID server using credentials defined in the config file. It then assigns a PID to the dataset. This step is necessary for all CMIP6 data records.
The output of this command is the input to both the ``esgupdate`` command as well as the ``esgindexpub`` command.

Usage
-----

``esgpidcitepub`` is used with the following syntax::

    esgpidcitepub --pub-rec <JSON file>

where ``<JSON file>`` is the output of the ``esgmkpubrec`` command.
The output of this command is by default printed to stdout, but can easily be redirected using the ``--out-file`` option.

The other command line options are as follows::

        usage: esgpidcitepub [-h] [--data-node DATA_NODE --pub-rec JSON_DATA
                             [--ini CFG] [--out-file OUT_FILE]

        Publish data sets to ESGF databases.

        optional arguments:
            -h, --help            show this help message and exit
            --data-node DATA_NODE
                                  Specify data node.
            --pub-rec JSON_DATA   Dataset and file json data; output from esgmkpubrec.
            --ini CFG, -i CFG     Path to config file.
            --out-file OUT_FILE   Optional output file destination. Default is stdout.

You can also define the above options (aside from ``--pub-rec``) in the config file if you choose.
