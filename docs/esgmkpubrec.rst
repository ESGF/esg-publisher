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

    usage: esgmkpubrec [-h] [--set-replica] [--no-replica] [--json JSON] --scan-file SCAN_FILE --map-data MAP_DATA [--out-file OUT_FILE] [--data-node DATA_NODE] [--index-node INDEX_NODE] [--project PROJ] [--ini CFG] [--silent] [--verbose]


    Publish data sets to ESGF databases.

    optional arguments:
        -h, --help                 show this help message and exit
        --set-replica              Enable replica publication.
        --no-replica               Disable replica publication.
        --json JSON                Load attributes from a JSON file in .json form. The attributes will override any found in the DRS structure or global attributes.
        --scan-file SCAN_FILE      JSON output file from autocurator.
        --map-data MAP_DATA        Mapfile json data converted using esgmapconv.
        --out-file OUT_FILE        Optional output file destination. Default is stdout.
        --data-node DATA_NODE      Specify data node.
        --index-node INDEX_NODE    Specify index node.
        --project PROJ             Set/overide the project for the given mapfile, for use with selecting the DRS or specific features, e.g. PrePARE, PID.
        --ini CFG, -i CFG          Path to config file.
        --silent                   Enable silent mode.
        --verbose                  Enable verbose mode.


NOTE: ``esgmkpubrec`` has customized settings and features depending on the project. If the project is undefined, it will use default settings which may not work for your project and could result in errors. It is highly recommended to specify your project, and also use the config file to specify if it is non-netcdf data.
