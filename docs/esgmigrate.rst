esgmigrate
==========

The ``esgmigrate`` command migrates old config settings from the old publisher into a new config file formatted for the current new publisher.
The output will be found in ``~/.esg/esg.ini`` which is the default config file path the publisher will read from.

Usage
-----

``esgmigrate`` is used with the following syntax::

    esgmigrate <ini_directory_path>

Where ``<ini_directory_path>`` is an optional argument specifying a directory to an old ``esg.ini`` file to migrate.
The default directory path is ``/esg/config/esgcet``.
