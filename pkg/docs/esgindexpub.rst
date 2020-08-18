esgindexpub
===========

The ``esgindexpub`` command publishes the data record using the metadata produced by the other commands to the ``index_node`` defined in the config file.
The output of this command will display published data along with a success message upon success.

Usage
-----

``esgindexpub`` is used with the following syntax::

    esgindexpub <JSON file>

where ``<JSON file>`` is the output of the ``esgpidcitepub`` command.
This command assumes that ``index_node`` and ``cert`` are defined in the ``esg.ini`` config file.
