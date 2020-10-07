esgpublish
==========

The ``esgpublish`` command publishes a record from start to finish using the mapfile(s) passed to it. On success, it will display a success message in the output of the last two steps.
If an error occurs, a helpful statement will be printed explaining which step went wrong and why.

Usage
-----

``esgpublish`` is used with the following syntax::

        esgpublish --map <mapfile>

You can also use ``--help`` to see::

        $ esgpublish --help
        usage: esgpublish [-h] [--test] [--set-replica] [--no-replica] [--json JSON] [--data-node DATA_NODE] [--index-node INDEX_NODE] [--certificate CERT] [--project PROJ]
                          [--cmor-tables CMOR_PATH] [--autocurator AUTOCURATOR_PATH] --map MAP

        Publish data sets to ESGF databases.

        optional arguments:
          -h, --help            show this help message and exit
          --test                PID registration will run in 'test' mode. Use this mode unless you are performing 'production' publications.
          --set-replica         Enable replica publication.
          --no-replica          Disable replica publication.
          --json JSON           Load attributes from a JSON file in .json form. The attributes will override any found in the DRS structure or global attributes.
          --data-node DATA_NODE
                                Specify data node.
          --index-node INDEX_NODE
                                Specify index node.
          --certificate CERT, -c CERT
                                Use the following certificate file in .pem form for publishing (use a myproxy login to generate).
          --project PROJ        Set/overide the project for the given mapfile, for use with selecting the DRS or specific features, e.g. PrePARE, PID.
          --cmor-tables CMOR_PATH
                        Path to CMIP6 CMOR tables for PrePARE. Required for CMIP6 only.
          --autocurator AUTOCURATOR_PATH
                                Path to autocurator repository folder.
          --map MAP             mapfile or file containing a list of mapfiles.
          --ini CFG, -i CFG     Path to config file.

This command can handle a singular mapfile passed to it, or a file containing a list of mapfiles (with full paths).
If optional command line arguments are used, they will override anything set in the config file.
NOTE: If, in your config file, you have specified a directory for ``autocurator`` rather than the default command, ie you are using a different ``autocurator`` than the one installed using conda, you must run the following command prior to running ``esgpublish``::

    export LD_LIBRARY_PATH=$CONDA_PREFIX/lib

If you do not run this and are not using the conda installed ``autocurator``, the program will not work.