.. _installation:

Installation
============

The esg-publisher requires a pre-installed `ESGF node <http://esgf.llnl.gov>`_ and the installation of `CDAT <http://cdat.llnl.gov/index.html>`_.
By default the installation of the esg-publisher is part of the `ESGF node installation <https://github.com/ESGF/esgf-installer/wiki>`_ that also installs CDAT and generates most of the publisher configs.

If you want to install a new version without upgrading the ESGF node you can use `pip` or install the package from source.

.. note::

	In order to install/upgrade the publisher in the default `esgf-pub` `conda` environment, you must run effectively as the `root` user.


Installation with pip
*********************

::

    $ source /usr/local/conda/bin/activate esgf-pub
    $ pip install --upgrade esgcet
    # Upgrades the esg-publsher (aka `esgcet`) to the latest available version and all prerequisite packages

To install a specific version of the publisher (without upgrading all packages), eg. `v3.5.11`, perform the `source` command as above, and:

::

	$ pip install esgcet==3.5.11


Installation from source
************************

Clone the Github repo and install the esgcet package using setup.py.

ESGF v2.5 or later

::

    $ source /usr/local/conda/bin/activate esgf-pub
    $ git clone https://github.com/ESGF/esg-publisher.git
    $ cd esg-publisher/src/python/esgcet
    $ python setup.py install

ESGF v2.4.x or earlier

::

    $ source /etc/esg.env
    $ git clone https://github.com/ESGF/esg-publisher.git
    $ cd esg-publisher/src/python/esgcet
    $ python setup.py install


