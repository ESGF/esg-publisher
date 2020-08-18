.. esgcet documentation master file, created by
   sphinx-quickstart on Mon Aug 17 15:42:32 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

The esgcet package for ESGF Publication
=======================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. sidebar:: ESGCET
   :subtitle: Navigation
   
   This is my side bar.
   This is a link to installation.
   .. _installation:

Esgcet is a package of publisher commands for publishing to the `ESGF
<https://esgf-node.llnl.gov/projects/esgf-llnl/>`_ search database.


Installation
------------

Install esgcet by running ::

        git clone http://github.com/lisi-w/esg-publisher.git -b gen-five-pkg
        cd pkg
        python3 setup.py install

Usage
-----

There are 6 commands. The first one, ``esgpublish`` is used with the following syntax::

        esgpublish --map <mapfile>

You can also use ``--help`` to see::

        $ esgpublish --help
        usage: esgpublish [-h] [--test] [--set-replica] [--no-replica] [--json JSON] [--data-node DATA_NODE] [--index-node INDEX_NODE] [--certificate CERT] [--project PROJ]
                          [--cmor-tables CMOR_PATH] [--autocurator AUTOCURATOR_PATH] --map MAP
        
        Publish data sets to ESGF databases.

        optional arguments:
          -h, --help            show this help message and exit
          --test                PID registration will run in 'test' mode. Use this mode unless you are performing 'production' publications.
          --set-replica         Enable replica publication.
          --no-replica          Disable replica publication.
          --json JSON           Load attributes from a JSON file in .json form. The attributes will override any found in the DRS structure or global attributes.
          --data-node DATA_NODE
                                Specify data node.
          --index-node INDEX_NODE
                                Specify index node.
          --certificate CERT, -c CERT
                                Use the following certificate file in .pem form for publishing (use a myproxy login to generate).
          --project PROJ        Set/overide the project for the given mapfile, for use with selecting the DRS or specific features, e.g. PrePARE, PID.
          --cmor-tables CMOR_PATH
                        Path to CMIP6 CMOR tables for PrePARE. Required for CMIP6 only.
          --autocurator AUTOCURATOR_PATH
                                Path to autocurator repository folder.
          --map MAP             mapfile or file containing a list of mapfiles.

This command publishes a data record from start to finish using the mapfile passed to it, or a file containing a list of mapfiles (with full paths). The next 5 commands break up the several steps and give the option to execute them one at a time:
1. ``esgmapconv``
2. ``esgmkpubrec``
3. ``esgpidcitepub``
4. ``esgupdate``
5. ``esgindexpub``

The usage for each of these can be seen by executing each command without arguments.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
