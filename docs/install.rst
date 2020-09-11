Installation
============

Before installing esgcet, please clone and install autocurator from its git repository::

    git clone http://github.com/sashakames/autocurator.git
    cd autocurator
    make

You can install esgcet one of two ways: conda, or git.
To install esgcet by cloning our github repository, run::

    git clone http://github.com/lisi-w/esg-publisher.git -b gen-five-pkg
    cd esg-publisher
    cd pkg
    python3 setup.py install

To install esgcet using conda, run::

    conda create -n esgf-pub -c esgf-forge -c conda-forge esgcet pip libnetcdf cmor

Now you will be able to call all commands in this package from any directory. A default config file, ``esg.ini`` will populate in ``$HOME/.esg`` where ``$HOME`` is your home directory.
Setup will also make autocurator in ``$HOME/autocurator`` and put the CMOR tables necessary for PrePARE into ``$HOME/cmor/Tables`` by cloning and both repositories. If these directories already exist,
that part will fail but the package will still install, just be sure to edit the paths for CMOR and autocurator in the config file as needed.

Conda & Required Packages
-------------------------

We recommend creating a conda env before installing ``esgcet`` ::

    conda create -n esgf-pub-v5 -c conda-forge pip requests libnetcdf cmor

NOTE: if you installed esgcet using conda above, cmor should be installed at the time you install esgcet automatically, and having cmor in your env may cause conflicts (but not always).
Also, if you created the env above to install esgcet, this step is not necessary.

You will also need to install ``esgfpid`` using pip::

    pip install esgfpid

Config
------

The default config file will look like this::

    [DEFAULT]
    note = IMPORTANT: please configure below in the [user] section, that is what the publisher will use to read configured settings. The below are marked as necessary or optional variables.
    data_node = * necessary
    index_node = * necessary
    cmor_path = ~/cmor/Tables * optional, default is where it is installed in setup
    autoc_path = ~/autocurator * optional, default is where it is installed in setup
    data_roots = * necessary, dictionary format json loadable
    cert = ./cert.pem * optional, default assumes cert in current directory, override to change
    test = false * optional, default assumes test is off, override to change
    project = none * optional, default will be parsed from mapfile name
    set_replica = false * optional, default assumes replica publication off
    globus_uuid = none * optional
    data_transfer_node = none * optional
    pid_creds = * necessary
    silent = false * optional
    verbose = false * optional

    [user]
    data_node =
    index_node =
    cmor_path = ~/cmor/Tables
    autoc_path = ~/autocurator
    data_roots =
    cert = ./cert.pem
    test = false
    project = none
    set_replica = false
    globus_uuid = none
    data_transfer_node = none
    pid_creds =
    silent = false
    verbose = false

Fill out the necessary variables, and either leave or override the optional configurations.

Run Time Args
-------------

If you prefer to set certain things at runtime, the ``esgpublish`` command has several optional command line arguments which will override options set in the config file.
For instance, if you use the ``--cmor-tables`` command line argument to set the path to the cmor tables directory, that will override anything written in the config file under ``cmor_path``.
More details can be found in the ``esgpublish`` section.
