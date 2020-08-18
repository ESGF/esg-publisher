esgpidcitepub
=============

The ``esgpidcitepub`` command connects to a PID server using credentials defined in the config file. It then assigns a PID to the dataset. This step is necessary for all CMIP6 data records.
The output of this command is the input to both the ``esgupdate`` command as well as the ``esgindexpub`` command.

Usage
-----

``esgpidcitepub`` is used with the following syntax::

    esgpidcitepub <JSON file>

where ``<JSON file>`` is the output of the ``esgmkpubrec`` command.
The output of this command is by default printed to stdout, but can easily be redirected using ``> filename.json``.
This command requires that ``data_node`` is defined in the ``esg.ini`` config file.
