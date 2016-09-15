.. _installation:

Installation
============

The esg-publisher requires a pre-installed `ESGF node <http://esgf.llnl.gov>`_ and the installation of `uvcdat <http://uvcdat.llnl.gov/index.html>`_.
By default the installation of the esg-publisher is part of the `ESGF node installation <https://github.com/ESGF/esgf-installer/wiki>`_ that also installs uvcdat and generates most of the publisher configs.

If you want to install a new version without upgrading the ESGF node you can install the package from source.

Installation from source
************************

Clone the Github repo and install the esgcet package using setup.py.

::

    $ source /etc/esg.env
    $ git clone https://github.com/ESGF/esg-publisher.git
    $ cd esg-publisher/src/python/esgcet
    $ python setup.py install
