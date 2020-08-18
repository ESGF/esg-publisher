Installation
============

Install esgcet by running ::

    git clone http://github.com/lisi-w/esg-publisher.git -b gen-five-pkg
    cd pkg
    python3 setup.py install

Now you will be able to call all commands in this package from any directory. A default config file, ``esg.ini`` will populate in ``$HOME/.esg`` where ``$HOME`` is your home directory.

Config
------

The default config file will look like this::

    [DEFAULT]
    note = IMPORTANT: please configure below in the [user] section, that is what the publisher will use to read configured settings. The below are marked as necessary or optional variables.
    data_node = * necessary
    index_node = * necessary
    cmor_path = * necessary for all CMIP6 recs
    autoc_path = * necessary
    data_roots = * necessary, dictionary format json loadable
    cert = ./cert.pem * optional, default assumes cert in current directory, override to change
    test = false * optional, default assumes test is off, override to change
    project = none * optional, default will be parsed from mapfile name
    set_replica = false * optional, default assumes replica publication off
    globus_uuid = none * optional
    data_transfer_node = none * optional
    pid_password = * necessary

    [user]
    data_node =
    index_node =
    cmor_path =
    autoc_path =
    data_roots =
    cert = ./cert.pem
    test = false
    project = none
    set_replica = false
    globus_uuid = none
    data_transfer_node = none

Fill out the necessary variables, and either leave or override the optional configurations.

Run Time Args
-------------

If you prefer to set certain things at runtime, the ``esgpublish`` command has several optional command line arguments which will override options set in the config file.
For instance, if you use the ``--cmor-tables`` command line argument to set the path to the cmor tables directory, that will override anything written in the config file under ``cmor_path``.
More details can be found in the :ref:`esgpublish` section.
