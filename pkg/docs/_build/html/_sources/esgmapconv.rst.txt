esgmapconv
==========

The ``esgmapconv`` command executes the first step of the publishing protocol by converting metadata from a mapfile into json data.
That data is the input to the ``esgmkpubrec`` command.

Usage
-----

``esgmapconv`` is used with the following syntax::

    esgmapconv <mapfile>

where ``<mapfile>`` is the absolute path to a single mapfile. The output will be printed to stdout, but can be easily redirected to a chosen file using ``> filename.json``.
