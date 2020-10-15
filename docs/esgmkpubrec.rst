esgmkpubrec
===========

The ``esgmkpubrec`` command uses the output data from ``esgmapconv`` to populate metadata for the dataset and file records.
This command also requires the output of the `autocurator
<https://github.com/lisi-w/autocurator>`_ command, which populates additional metadata using the mapfile and puts it into a separate json file.
This output is the input to the ``esgpidcitepub`` command.

Usage
-----

``esgmkpubrec`` is used with the following syntax::

    esgmkpubrec --scan-file <scan file> --map-data <JSON file>

where ``<JSON file>`` is the aforementioned output from ``esgmapconv`` and ``<scan file>`` is the output of ``autocurator<https://github.com/lisi-w/autocurator>`_.
The output is again defaulted to stdout, but can easily be redirected using the ``--out-file`` option.

The other command line options are as follows::

    usage: esgmkpubrec [-h] [--set-replica] [--no-replica] --scan-file SCAN_FILE [--json JSON] [--data-node DATA_NODE] [--index-node INDEX_NODE] --map-data MAP_DATA [--ini CFG]
                   [--out-file OUT_FILE]

    Publish data sets to ESGF databases.

    optional arguments:
        -h, --help            show this help message and exit
        --set-replica         Enable replica publication.
        --no-replica          Disable replica publication.
        --scan-file SCAN_FILE
                              JSON output file from autocurator.
        --json JSON           Load attributes from a JSON file in .json form. The attributes will override any found in the DRS structure or global attributes.
        --data-node DATA_NODE
                              Specify data node.
        --index-node INDEX_NODE
                              Specify index node.
        --map-data MAP_DATA   Mapfile json data converted using esgmapconv.
        --ini CFG, -i CFG     Path to config file.
        --out-file OUT_FILE   Optional output file destination. Default is stdout.
