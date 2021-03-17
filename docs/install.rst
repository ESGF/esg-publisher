Installation
============

You can install esgcet one of two ways: pip or git.  At present esgcet in unavailable via conda (a change is forthcoming).


Conda & Required Packages
-------------------------

We recommend creating a conda env before installing ``esgcet``: ::

    conda create -n esgf-pub -c conda-forge -c esgf-forge pip cmor autocurator esgconfigparser
    conda activate esgf-pub


..  note:: the command above creates a new environment for the publisher.  This is recommended rather than attempting to reuse an existing environment if you wish to upgrade a previous version of the publisher.  If you installed esgcet using conda above, the cmor package (different from tables) should be installed at the time you install esgcet automatically, and having cmor in your env may cause conflicts (but not always).


esgcet Install: (pip or source)
-------------------------------

To install esgcet by pip run the following (note the version tag is requried): ::

    pip install esgcet==5.0.0a11

..  note:: You must specify the version as the v5.0.x is under pre-release.  Installing ``esgcet`` will install the previous major version (v3.xx). 



To install esgcet by cloning our github repository (useful if you want to modiy the software): first, you should ensure you have a suitable python in your environment (see above for information on conda, etc.), and then run: ::

    git clone http://github.com/ESGF/esg-publisher.git -b gen-five-pkg
    cd esg-publisher
    cd pkg
    python3 setup.py install



Now you will be able to call all commands in this package from any directory. A default config file, ``esg.ini`` will populate in ``$HOME/.esg`` where ``$HOME`` is your home directory.

NOTE: if you are intending to publish CMIP6 data, the publisher will run the PrePARE module to check all file metadata.  To enable this procedure, it is necessry to download CMOR tables before the publisher will successfully run. See those pages for more info.



Config
------

The default config file will look like this::

    [DEFAULT]
    note = IMPORTANT: please configure below in the [user] section, that is what the publisher will use to read configured settings. The below are marked as necessary or optional variables.
    version = 5.0.0a2
    data_node = * necessary
    index_node = * necessary
    cmor_path = * necessary, and must be an absolute path (not relative)
    autoc_path = autocurator * optional, default is autocurator conda binary, can be replaced with a file path, relative or absolute
    data_roots = * necessary, must be in json loadable dictionary format
    cert = ./cert.pem * optional, default assumes cert in current directory, override to change
    test = false * optional, default assumes test is off, override to change
    project = none * optional, default will be parsed from mapfile name
    set_replica = false * optional, default assumes replica publication off
    globus_uuid = none * optional
    data_transfer_node = none * optional
    pid_creds = * necessary
    silent = false * optional
    verbose = false * optional

    [example]
    data_node = esgf-data1.llnl.gov
    index_node = esgf-node.llnl.gov
    cmor_path = /export/user/cmor/Tables
    autoc_path = autocurator
    data_roots = {"/esg/data": "esgf_data"}
    cert = ./cert.pem
    test = false
    project = CMIP6
    set_replica = true
    globus_uuid = none
    data_transfer_node = none
    pid_creds = [{"url": "aims4.llnl.gov", "port": 7070, "vhost": "esgf-pid", "user": "esgf-publisher", "password": "<password>", "ssl_enabled": true, "priority": 1}]
    silent = false
    verbose = false


    [user]
    data_node =
    index_node =
    cmor_path =
    autoc_path = autocurator
    data_roots =
    cert = ./cert.pem
    test = false
    project = none
    set_replica = false
    globus_uuid = none
    data_transfer_node = none
    pid_creds =
    silent = false
    verbose = falsee

Fill out the necessary variables, and either leave or override the optional configurations. Note that the section the publisher reads is the ``user`` section, not the default nor example.

If you have an old config file from the previous iteration of the publisher, you can use ``esgmigrate`` to migrate over those settings to a new config file which can be read by the current publisher.
See that page for more info.

Run Time Args
-------------

If you prefer to set certain things at runtime, the ``esgpublish`` command has several optional command line arguments which will override options set in the config file.
For instance, if you use the ``--cmor-tables`` command line argument to set the path to the cmor tables directory, that will override anything written in the config file under ``cmor_path``.
More details can be found in the ``esgpublish`` section.
