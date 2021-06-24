esgmapconv
==========

The ``esgmapconv`` command executes the first step of the publishing protocol by converting metadata from a mapfile into json data.
That data is the input to the ``esgmkpubrec`` command.

Usage
-----

``esgmapconv`` is used with the following syntax::

    esgmapconv --map <mapfile>

where ``<mapfile>`` is the absolute path to a single mapfile. The output will be printed to stdout, but can be easily redirected to a chosen file using the ``--out-file`` option.

You can also use the other command line options for additional configuration::

        usage: esgmapconv [-h] [--project PROJ] --map MAP [--out-file OUT_FILE] [--ini CFG]

        Publish data sets to ESGF databases.

        optional arguments:
            -h, --help           show this help message and exit
            --project PROJ       Set/overide the project for the given mapfile, for use with selecting the DRS or specific features, e.g. PrePARE, PID.
            --map MAP            Mapfile ending in .map extension, contains metadata about the record.
            --out-file OUT_FILE  Output file for map data in JSON format. Default is printed to standard out.
            --ini CFG, -i CFG    Path to config file.

Using the command line option ``-h`` will display the above message.
The above options (excluding ``--map``) can be defined in the config file instead of the command line if you choose.