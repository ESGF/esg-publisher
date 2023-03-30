.. _migrate:

esgmigrate
==========

The ``esgmigrate`` command migrates old config settings from the old publisher into a new config file formatted for the current new publisher.
The output will be found in ``$HOME/.esg/esg.yaml`` which is the default config file path the publisher will read from.

Usage
-----

``esgmigrate`` is used with the following syntax::

    esgmigrate

By default, esgmigrate will attempt to read the old config file at ``/esg/config/esgcet`` and will write the new config file to ``$HOME/.esg/esg.yaml``.
To override these defaults, use the optional command line arguments below.

Additional command line options are as follows::

        usage: esgmigrate [-h] [--old-config CFG] [--silent] [--verbose]
                          [--project PROJECT] [--destination DEST]

        Migrate old config settings into new format.

        optional arguments:
            -h, --help          show this help message and exit
            --old-config CFG    Full path to old config file to migrate.
            --silent            Enable silent mode.
            --verbose           Enable verbose mode.
            --project PROJECT   Name of a particular legacy project to migrate.
            --destination DEST  Destination for new config file.

Note that ``--old-config`` should point to a directory, not the file itself; however, ``--destination`` should be a complete file path including the file name.
