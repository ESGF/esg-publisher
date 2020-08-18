esgmkpubrec
===========

The ``esgmkpubrec`` command uses the output data from ``esgmapconv`` to populate metadata for the dataset and file records.
This command also requires the output of the `autocurator
<https://github.com/lisi-w/autocurator>`_ command, which populates additional metadata using the mapfile and puts it into a separate json file.
This output is the input to the ``esgpidcitepub`` command.

Usage
-----

``esgmkpubrec`` is used with the following syntax::

    esgmkpubrec <JSON file> <scan file>

where ``<JSON file>`` is the aforementioned output from ``esgmapconv`` and ``<scan file>`` is the output of ``autocurator<https://github.com/lisi-w/autocurator>`_.
The output is again defaulted to stdout, but can easily be redirected using ``> filename.json``.
This command requires that ``data_node``, ``index_node``, and ``replica`` are all defined in the ``esg.ini`` config file.
