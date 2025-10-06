Installation
============

We recommend creating a ``conda`` / ``mamba(forge)`` environment or ``venv`` for running the esg publisher.

Pip Install
-----------

Use the following command to install ``esgcet`` into a previously created conda environment: ::

    conda activate esgf-pub
    pip install esgcet 
    esgpublish --version #  Ensure you have upgraded to v5.4.0a


All publisher requirements are installed via ``pip`` except for the CMOR tables (see below).

Installing esgcet via git
-------------------------

To install esgcet by cloning our github repository (useful if you want to modiy the software): first, you should ensure you have a suitable python in your environment, and then run::

    git clone http://github.com/ESGF/esg-publisher.git 
    cd esg-publisher
    cd src/python
    pip install -e .  # You can modify the source in place
    esgpublish --version  # Confirm that v5.4.0a has been installed

Now you will be able to call all commands in this package from any directory.  


NOTE: if you are intending to publish CMIP6Plus or CMIP7 data, the publisher will perform several `semantic relationship` checks of the dataset properties to ensure that the model and experiment being publisher were successfully registered with the WCRP Controlled-vocabulary (CV).  To enable this procedure, it is necessary to download CMOR tables before the publisher will successfully run, as those are required input for the checks.



Config File (esg.yaml)
----------------------

Starting with ``v5.2.0`` the ESGF Publisher uses a .yaml file for configuration.  Download a copy of the default config file ``esg.yaml`` to the default directory,
 or see below regarding migrating a previous config  ::

   wget https://raw.githubusercontent.com/ESGF/esg-publisher/main/src/python/esg.yaml
   mkdir $HOME/.esg
   cp esg.yaml $HOME/.esg

The ``--config`` command-line argument lets you set a configuration file of your choosing other than the default location.

The config file will contain the following settings, most required settings are also available as command line arguments:

 * data_node
    * Required. This is the ESGF node (Fully-Qualified Domain Name) at which the data is stored that you are publishing. It will be concatenated with the dataset_id (instance_id) to form the full id for your dataset. 
 * index_node
    * Required. This is the ESGF node (Fully-Qualified Domain Name) where your dataset will be published and indexed. You can then retrieve it or see related metadata by using the ESGF Search API at that index node.
 * cmor_path
    * Required for CMIPx Projects (CMIP6 and later). This is a full absolute path to a directory containing CMOR tables, used by the publisher to verify specific registrations of CMIP data with WCRP, eg. the ``source_id`` and ``experiment_id``. Example: /usr/local/cmip<X>-cmor-tables/Tables  This is either the cmor tables repo cloned from github or prepared using the ``esgfetctables`` tool part of ``esgf-prepare``. <X> is the CMIP-era of tables to check specific to the publish
 * autoc_path
    * Optional. This is the path for the autocurator executable.  The default assumes that you have installed it via conda. If you have not installed it via conda, please replace with a file path to your installed binary.  If set to ``none`` or removed, the publisher will default to scanning data using XArrary.
 * data_roots
    * Required. These are paths where you place your project data for publication, typically within mounted large storage systems, on the local server where running the publisher.  Each entry maps the path to a logical subdirectory within a data url on the datanode.  Please note two configurations (1) these may be different from the data node mounts --or-- (2) may also appear in data node setup within ``esgf-docker`` configuations (Ansible playbooks or Helm charts) if the local publishing node uses the same mounts. Contact your node/site administrator for more info.
 * mountpoint_map
    * Optional. Must be in yaml dictionary format.  Specifies an additonal mapping for the data root mounts that appear in the input mapfiles to the mounted data root on the host running the publisher, in the event mapfile generation occurred on a different host where the data resided at a different mountpoint. Changes specified "aliased" roots in mapfile to actual file roots like so: /source/path/in/mapfiles: "/actual/path/to/data"
 * cert
    * Optional. This is the full path to the certificate file used for publishing if publishing to a legacy ``esg-search`` site requiring authorization.
 * test
    * Optional. This can be set to True or False, and it will run the esgfpid service in test mode. Default assumes False. Override if you are not doing production publishing.
 * project
    * Optional. ESGF project to which your data belongs. Default will be parsed from the mapfile name.
 * non_netcdf
    * Optional. Enable or disable publication settings for non NetCDF data, default assumes False.
 * set_replica
    * Optional. Enable or disable replica publication settings, for sites that publish replica data. Default assumes False, or replica publication off (original data publication).
 * globus_uuid
    * Optional. Specify the UUID for your site Globus endpoint as configured in the Globus webapp.  Default leaves out Globus URL from dataset metadata.
 * data_transfer_node
    * Optional. If you run the GridFTP service, set the hostname of that node, whether it the same as your data node or a sepearte Data Transfer Node for gsiftp urls in file records.  Default of "none" will omit.
 * pid_creds
    * Settings and credentials for RabbitMQ server access for the PID sefvice, required for some projects (CMIP6, input4MIPs). 
 * user_project_config
    * Optional. If using a self-defined project compatible with our generic publisher, put DRS and CONST_ATTR in a dictionary designated by project.
 * silent
    * Optional. Enable or disable silent mode, which suppresses all INFO logging messages.  Errors and messages from sub-modules are not suppressed. Default is False, silent mode disabled.
 * verbose
    * Optional. Enable or disable verbose mode, which outputs additional DEBUG logging messages. Default is False, verbose mode disabled.
 * enable_archive
    * Optional.  Enable the writeout of dataset/file record in xml files to a local file system. (see :ref:`arch_info`)
 * archive_location
    * Optional. (Required when enable_archive = True) Path on local file system to build directory tree and write xml files for record archive. 
 * archive_depth
    * Optional. (Required when enable_archive = True) sets the directory depth of subdirectories to create/use in the xml archive. (see :ref:`arch_info`)
 * globus_index
    * Optional boolean.  Set to **true** if you are publishing to a ESGF2-US ESGF-1.5 Globus Search index.
 * index_UUID
    * Optional. (Required for ESGF-1.5).  Set this value to the ESGF-1.5 index (see `ESGF-1.5 Index list <https://github.com/esgf2-us/esgf-1.5-design/blob/main/indexes.md>`_ for the listing)
 * https_url
    * Optional. (Require for sites that don't run a standard Nginx http server container, eg. use of Globus).  For Globus-enabled sites, this is a template in the form: https://<hostname>.data.globus.org/{}/{}|application/netcdf|HTTPServer.  Get your <hostname> from your site/data node administrator.  The software will populate the ``{}`` fields, leave as is. 

      

Fill out the necessary variables, and either leave or override the optional configurations.
Example config settings can be found in the default esg.ini config file which will be created at ``$HOME/.esg/esg.yaml`` when you install ``esgcet``.
Note that while the ``cmor_path`` variable points to a directory, other filepaths must be complete, such as ``autoc_path`` and ``cert``. This applies to the command line arguments for these as well.
Additionally, a *required* setting if omitted can be satisfied via inclusion as ccommand line arguments.


If you have an old config file from the previous iteration of the publisher, you can use ``esgmigrate`` to migrate over those settings to a new config file which can be read by the current publisher.
See that page for more info.

Project Configuration
---------------------

You may define a custom project in several ways.  First, using the
``user_project_config`` setting, specify an alternate *DRS* and constant attribute values (``CONST_ATTR``) for your project.
``DRS:`` is followed an array with the components.
``version`` is *always* the ultimate component of the dataset and should not be listed among the DRS components.  If you wish to specify a custom set of *Global Atributes* 
you may do so using the .yaml section ``GA:``

If your project desires to use the features of CMIP6 included extracted Global Attributes use the ``cmip6_clone``
config file property and assign to your custom project name within the ``user_project_config``.  The project name must be overridden using ``CONST_ATTR`` ``project setting`` (see example below).  If you CMIP6 project wishes to register PIDs, you must assign a ``pid_prefix`` within 
config settings.   

Example Config
^^^^^^^^^^^^^^

The following contains example ``.yaml`` code and configures the *primavera* project as a user-defined `cloned` project:

..  code-block:: yaml

   cmip6_clone: primavera
   cmor_path: /path/to/cmip6-cmor-tables/Tables
   data_node: esgf-fake-test.llnl.gov
   data_roots:
      /mounted/path/to/data: data_in_url
   data_transfer_node: aimsdtn2.llnl.gov
   force_prepare: 'false'
   globus_uuid: 415a6320-e49c-11e5-9798-22000b9da45e
   index_node: esgf-fedtest.llnl.gov
   pid_creds:
      aims4.llnl.gov:
         password: password
         port: 7070
         priority: 1
         ssl_enabled: true
         user: esgf-publisher
         vhost: esgf-pid
   project: none
   set_replica: 'true'
   silent: 'false'
   skip_prepare: 'true'
   test: 'true'
   user_project_config:
      primavera:
         CONST_ATTR:
            project: primavera
         pid_prefix: '21.14100'
   verbose: 'false'
   https_url:  https://hostname.data.globus.org/{}/{}|application/netcdf|HTTPServer


Run Time Args
-------------

If you prefer to set your configuration to publish at runtime, the ``esgpublish`` command has several optional command line arguments which will override options set in the config file.  
For instance, if you use the ``--cmor-tables`` command line argument to set the path to the cmor tables directory, that will override anything written in the config file under ``cmor_path``.

If you used the old (v4 or earlier) version of the publisher, you should note that the command line argument ``--config`` which points to your config file must be a complete path, not the directory as it was in the previous version.
More details can be found in the ``esgpublish`` section.  Some settings are not available on the command line and must be placed in the config file, such as the xml "archive" utility.
