esgupdate
=========

The ``esgupdate`` command checks to see if the dataset being published is already in our database. If it is, it uses the metadata produced by the other commands to update the record.
The output is the published data along with a success message upon success.

Usage
-----

``esgupdate`` is used with the follwing syntax::

    esgupdate <JSON file>

where ``<JSON file>`` is the output of the ``esgpidcitepub`` command.
This command assumes that ``index_node`` and ``cert`` are defined in the ``esg.ini`` config file.
