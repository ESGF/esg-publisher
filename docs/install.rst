Installation
============


Conda & Required Packages
-------------------------

We recommend creating a conda env before installing ``esgcet`` ::

    conda create -n esgf-pub -c conda-forge -c esgf-forge pip libnetcdf cmor autocurator esgconfigparser

NOTE: if you install esgcet using conda below, the cmor package (different from tables) should be installed at the time you install esgcet automatically, and having cmor in your env may cause conflicts (but not always).

You will also need to install ``esgfpid`` using pip::

    pip install esgfpid

NOTE: you will need a functioning version of ``autocurator`` in order to run the publisher, in addition to downloading the CMOR tables. See those pages for more info.


Installing esgcet
-----------------

You can install esgcet one of two ways: conda, or git.


To install esgcet using conda, activate the environment you created above and run::

    conda install -c esgf-forge -c conda-forge esgcet

To install esgcet by cloning our github repository (useful if you want to modiy the software): first, you should ensure you have a suitable python in your environment (see below for information on conda, etc.), and then run::

    git clone http://github.com/lisi-w/esg-publisher.git -b refactor
    cd esg-publisher
    cd pkg
    python3 setup.py install



Now you will be able to call all commands in this package from any directory. A default config file, ``esg.ini`` will populate in ``$HOME/.esg`` where ``$HOME`` is your home directory.

NOTE: if you are intending to publish CMIP6 data, the publisher will run the PrePARE module to check all file metadata.  To enable this procedure, it is necessry to download CMOR tables before the publisher will successfully run. See those pages for more info.


Config
------

The config file will contain the following settings:

 * data_node
    * Required. This is the ESGF node at which the data is stored that you are publishing. It will be concatenated with the dataset_id to form the full id for your dataset.
 * index_node
    * Required. This is the ESGF node where your dataset will be published and indexed. You can then retrieve it or see related metadata by using the ESGF Search API at that index node.
 * cmor_path
    * Required for CMIP6. This is a full absolute path to a directory containing CMOR tables, used by the publisher to run PrePARE to verify the structure of CMIP6 data.
 * autoc_path
    * Optional. This is the path for the autocurator executable. The default assumes that you have installed it via conda. If you have not installed it via conda, please replace with a file path to your installed binary.
 * data_roots
    * Required. Must be in a json string loadable by python. Maps file roots to names.
 * mountpoint_map
    * Optional. Must be in yaml dictionary format. Changes specified sym link file roots in mapfile to actual file roots like so: /symlink/dir: "/actual/path"
 * cert
    * Optional. This is the full path to the certificate file used for publishing. Default assumes a file "cert.pem" in your current directory. Replace to override.
 * test
    * Optional. This can be set to True or False, and it will run the esgfpid service in test mode. Default assumes False. Override if you are not doing production publishing.
 * project
    * Optional. ESGF project to which your data belongs. Default will be parsed from the mapfile name.
 * non_netcdf
    * Optional. Enable or disable publication settings for non NetCDF data, default assumes False.
 * set_replica
    * Optional. Enable or disable replica publication settings. Default assumes False, or replica publication off.
 * globus_uuid
    * Optional. Specify Globus UUID. Default leaves out Globus URL from dataset metadata.
 * data_transfer_node
    * Optional. Specify the Data Transfer Node for your dataset. Default is none.
 * pid_creds
    * Required for some projects (CMIP6, input4MIPs). Input esgfpid credentials as a dictionary.
 * user_project_config
    * Optional. If using a self-defined project compatible with our generic publisher, put DRS and CONST_ATTR in a dictionary designated by project.
 * silent
    * Optional. Enable or disable silent mode, which represses all INFO logging messages. Default is False, silent mode disabled.
 * verbose
    * Optional. Enable or disable verbose mode, which outputs additional DEBUG logging messages. Default is False, verbose mode disabled.

Fill out the necessary variables, and either leave or override the optional configurations.
Example config settings can be found in the default esg.ini config file which will be created at ``$HOME/.esg/esg.yaml`` when you install ``esgcet``.
Note that while the ``cmor_path`` variable points to a directory, other filepaths must be complete, such as ``autoc_path`` and ``cert``. This applies to the command line arguments for these as well.

If you have an old config file from the previous iteration of the publisher, you can use ``esgmigrate`` to migrate over those settings to a new config file which can be read by the current publisher.
See that page for more info.

Run Time Args
-------------

If you prefer to set certain things at runtime, the ``esgpublish`` command has several optional command line arguments which will override options set in the config file.
For instance, if you use the ``--cmor-tables`` command line argument to set the path to the cmor tables directory, that will override anything written in the config file under ``cmor_path``.
If you used the old version of the publisher, you should note that the command line argument ``--config`` which points to your config file must be a complete path, not the directory as it was in the previous version.
More details can be found in the ``esgpublish`` section.
