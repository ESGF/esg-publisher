.. _configuration:

Configuration
=============

Prepare the configuration files
*******************************

The ESGF publisher needs two sort of configuration files:

esg.ini
    This file is the primary means of configuring the default behavior of the publisher.

esg.<project>.ini
    The project configuration files contain the project specific sections for publication of particular projects, e.g. ``esg.cmip5.ini`` for CMIP5,
    ``esg.cordex.ini`` for CORDEX, etc.

A ``esg.ini`` template and several ``esg.<project>.ini`` files are available from the `ESGF config repo <https://github.com/ESGF/config/tree/master/publisher-configs/ini>`_ on GitHub.

The default location of all publisher related configuration files is ``/esg/config/esgcet/``. The ESGF publisher will automatically read from the files in this directory.
Alternatively, you may specify the location of the ini files via ``-i`` option.

.. note::
    Although it is recommended to generate one configuration file per project the publisher will also work for a single esg.ini that contains all necessary project sections.

.. warning::
    After any modification of the configuration files or the models table you need to update the postgreSQL database by running: ``$ esginitialize -c``



The default config file: esg.ini
--------------------------------

``esg.ini`` contains all basic configs needed for the ESGF publisher, i.e. the ``[DEFAULT]``, ``[initialize]``, ``[extract]``, ``[srmls]`` and ``[hsi]``
sections. This file will be set up during the ESGF installation process.

.. warning::
    Ensure the ``hessian_service_url`` contains the correct index node as this has been known to be overwritten.

#. The ``[DEFAULT]`` section

    - Section name and default configs

        ::

            [DEFAULT]
            checksum = sha256sum | SHA256
            log_format = %(levelname)-10s %(asctime)s %(message)s
            log_level = INFO
            root_id = <your_node>

    - Project options

        Ensure that the project you wish to publish is found in the ``project_options``. Also make sure that it has it's own project specific ini file,
        ``esg.<project>.ini``, e.g. ``esg.cmip5.ini``.

        Format of the project_options:

        ::

            project_options =
                <project_name_1> | <description> | <next_integer_value_from_above_project>
                <project_name_2> | <description> | <next_integer_value_from_above_project>

        Example:

        ::

                project_options =
                    cmip5    | CMIP5    | 1
                    cordex   | CORDEX   | 2
                    obs4MIPs | obs4MIPs | 3
                    test     | TEST     | 4

        .. note::
            The ``project_options`` are updated automatically if you fetch the project ini files by running ``$ esgprep fetch-ini``.

    - Postgres configuration

        ::

            dburl = postgresql://esgcet:<esgcet_password>@localhost:5432/esgcet

    - Thredds configuration

        Ensure that the directory/mountpoint where you store the files for publication is set under ``thredds_dataset_roots``.

        .. warning::
            Dataset roots should never contain one another. If the data for a particular project is contained within a single directory even if
            the node publishes just that project, it should be a subdirectory of the root, not included in the dataset_root directory.

        ::

            thredds_aggregation_services =
                    OpenDAP | /thredds/dodsC/            | gridded
                    LAS     | http://<fqdn>/las/getUI.do | LASat<your_node>
            thredds_authentication_realm = THREDDS Data Server
            thredds_catalog_basename = %(dataset_id)s.v%(version)s.xml
            thredds_dataset_roots =
                    esg_dataroot | /esg/data
                    cmip5        | /data/cmip5
            thredds_error_pattern = Catalog init
            thredds_fatal_error_pattern = **Fatal
            thredds_file_services =
                    HTTPServer | /thredds/fileServer/          | HTTPServer    | fileservice
                    GridFTP    | gsiftp://<fqdn>:2811/         | GRIDFTP       | fileservice
                    OpenDAP    | /thredds/dodsC/               | OpenDAPServer | fileservice
                    Globus     | globus:#DEFAULTENDPOINTNAME#/ | Globus        | fileservice
            thredds_master_catalog_name = Earth System Grid catalog
            thredds_max_catalogs_per_directory = 500
            thredds_offline_services =
                    SRM | srm://<fqdn>:6288/srm/v2/server?SFN=/archive.sample.gov | HRMatPCMDI
            thredds_password = <thredds_password>
            thredds_reinit_error_url = https://localhost:443/thredds/admin/content/logs/catalogInit.log
            thredds_reinit_success_pattern = reinit ok
            thredds_reinit_url = https://localhost:443/thredds/admin/debug?Catalogs/recheck
            thredds_restrict_access = esg-user
            thredds_root = /esg/content/thredds/esgcet
            thredds_root_catalog_name = Earth System Root catalog
            thredds_url = http://<fqdn>/thredds/catalog/esgcet
            thredds_username = dnode_user

        .. note::  It is recommended to have all ``thredds_file_services`` including `HTTPServer`, `GridFTP`, `OpenDAP` and `Globus` unless specific node configuration is needed.

    - Index node configuration

        ::

            hessian_service_certfile = %(home)s/.globus/certificate-file
            hessian_service_keyfile = %(home)s/.globus/certificate-file
            hessian_service_certs_location = %(home)s/.globus/certificates
            hessian_service_debug = false
            hessian_service_polling_delay = 3
            hessian_service_polling_iterations = 10
            hessian_service_port = 443
            hessian_service_remote_metadata_url = http://host/esgcet/remote/hessian/guest/remoteMetadataService
            hessian_service_url = https://<index_fqdn>/esg-search/remote/secure/client-cert/hessian/publishingService


.. _config_project_section:

#. The ``[config:<project>]`` section

    To specify project specific configuration in `esg.ini` you can add a separate config section for each project.
    If PIDs are used by the project, the PID configs are set in that section, the same applies for the Citation. It also overrides the `hessian_service_url`, if specified.

    Example:

    ::

        [config:cmip6]
        hessian_service_url = https://esgf-data.dkrz.de/esg-search/remote/secure/client-cert/hessian/publishingService
        citation_url = http://cera-www.dkrz.de/WDCC/meta/CMIP6/%(dataset_id)s.%(version)s.json # not mandatory for CMIP6
        pid_prefix = 21.14100                   # not mandatory for CMIP6
        pid_exchange_name = esgffed-exchange    # not mandatory for CMIP6
        pid_credentials =
          # hostname                  | port | virtual_host |    username    | password | ssl_enabled
          handle-esgf-trusted.dkrz.de | 5671 |   esgf-pid   | esgf-publisher | <secret> |    true
          pcmdi10.llnl.gov            | 5671 |   esgf-pid   | esgf-publisher | <secret> |    true

    The ``pid_credentials`` are available on `Confluence <https://acme-climate.atlassian.net/wiki/spaces/ESGF/pages/369983978/RabbitMQ+server+config>`_.
    In case you don't have access to that page please contact your tier1 node admin or fetch the credentials with the ESGF node manager as following:

         #. Ensure that the ``/etc/grid-security/hostcert.pem`` is signed by one of the ESGF root CAs (eg. ANL, IPSL, NSC)
         #. [Run as root]:

            ::

                $ source /usr/local/conda/bin/activate esgf-pub
                $ python /usr/local/esgf-node-manager/src/python/client/fetch_pub_credentials.py <node-server>  # e.g. esgf-node.llnl.gov or esgf-data.dkrz.de

         #. Inspect ``/esg/config/esgcet/esg.ini`` – ``[config:cmip6]`` section should be installed with ``pid_credentials``
         #. Please change the order of the lines – put the host closest to your location first

    .. note::
        Please ensure that the firewall is open for all PID hosts on port 5671.

    .. note::
        This option is optional for most projects, except CMIP6.


#. The ``[initialize]`` section

    ::

        [initialize]
        initial_models_table = /esg/config/esgcet/esgcet_models_table.txt
        log_level = INFO


    The ``esgcet_models_table`` is a separate file for the configuration of all models. The default location of this file is ``/esg/config/esgcet/esgcet_models_table.txt``.

    Format of the models table:

    ::

        <project> | <model_1> | <model_url_1> | <model_description>
        <project> | <model_2> | <model_url_2> | <model_description>

    Example:

    ::

        cmip5 | MPI-ESM-P  | | MPI-ESM-P, Max Planck Institute for Meteorology (MPI-M)
        cmip5 | MPI-ESM-LR | | MPI-ESM-LR, Max Planck Institute for Meteorology (MPI-M)
        cmip5 | MPI-ESM-MR | | MPI-ESM-MR, Max Planck Institute for Meteorology (MPI-M)


    If you are defining a new project but using an existing model name, you need to add a new entry to the table file for your new pairing as well.

    .. note::
        After modifying the models table please run ``$ esginitialize -c``  to update the postgres database.

.. _myproxy_section:

#. The ``myproxy`` section

    ``esgpublish`` and ``esgunpublish`` will automatically generate or renew your globus certificate using the credentials specified here.

    ::

        [myproxy]
        hostname = <openid_server>
        username = <esgf_user>
        password = <password>

    .. note::
        If this section is not specified and the globus certificate is not present or valid the user will be prompted for the credentials during ``esgpublish`` and ``esgunpublish``.

    .. note::
        This section is not present by default.

#. Other sections, e.g. for scanning the files and the offline services

    ::

        [extract]
        log_level = INFO
        validate_standard_names = True

        [srmls]
        offline_lister_executable = %(home)s/work/Esgcet/esgcet/scripts/srmls.py
        srm_archive = /garchive.nersc.gov
        srm_server = srm://somehost.llnl.gov:6288/srm/v2/server
        srmls = /usr/local/esg/bin/srm-ls

        [hsi]
        hsi = /usr/local/bin/hsi

The project specific config files: esg.<project>.ini
----------------------------------------------------

#. Set the section name

    Each project specific configuration file starts with a section name following the ``[project:<project_name>]`` syntax.

    .. warning::
        Please note: The <project_name> is case sensitive and needs to match the file name and the project name you specify with ``--project``,
        e.g. ``esg.cmip5.ini``, ``[project:cmip5]``, ``--project cmip5``.

#. Set the ``categories`` to be used for the project

    The ``categories`` define the facet fields. All facets listed as ``enum`` will be checked against the :ref:`facet_options, facet_map or
    facet_pattern <facet_options>`. Facets that are listed as ``string`` will not be checked unless they are part of the ``directory_format``.

    Format of the categories:

    ::

        name | category_type | is_mandatory | is_thredds_property | display_order

    If the value for ``is_thredds_property`` is set to ``true`` the facet will appear in the Thredds Catalog and in the Index.

    Example:

    ::

        categories =
            project        | enum   | true  | true  | 0
            product        | enum   | true  | true  | 1
            institute      | string | true  | true  | 2
            model          | enum   | true  | true  | 3
            experiment     | enum   | true  | true  | 4
            time_frequency | enum   | true  | true  | 5
            realm          | enum   | true  | true  | 6
            cmor_table     | enum   | true  | true  | 7
            ensemble       | string | true  | true  | 8
            description    | text   | false | false | 99

    You can also set a default value for particular categories, e.g.:

    ::

        category_defaults =
            project | cmip5


#. The ``directory_format``

    Ensure that the ``directory_format`` is spelled out for the project, check carefully for typos. Data files must be found in the rightmost set of subdirectories specified,
    the not-project-specific root part in front of the project-specific DRS elements can be specified as ``%(root)``, all project related elements must be defined separately,
    following the ``%(name)s`` syntax, e.g.:

    ::

        directory_format = %(root)/%(project)s/%(model)s/%(experiment)s/%(realm)s
        or
        directory_format = /some_mountpoint/data/%(project)s/%(model)s/%(experiment)s/%(realm)s

    Example:

    ::

        /some_mountpoint/data/cmip5/CESM/historical/atmos/blah.nc   - valid
        /some_mountpoint/data/cmip5/CESM/historical/atmos/1/blah.nc - not valid
        /some_mountpoint/data/cmip5/CESM/historical/blah.nc         - not valid

    In the example above, ``/some_mountpoint/data`` must be included in the ``thredds_dataset_roots`` entry in the ``[DEFAULT]`` section of esg.ini.


#. Ensure that you have a ``dataset_id`` and optional a ``dataset_name_format``

    The ``dataset_id`` is project specific and may mirror the directory structure to a point.

    ::

        dataset_id = %(project)s.%(model)s.%(experiment)s.%(realm)s

    .. note::
        The facets used for the ``dataset_id`` must be a subset of those used in the ``directory_format``. In other words, the facet names
        for the ``dataset_id`` must appear as variables within the ``directory_format`` using the same corresponding names with the ``%(name)s`` syntax or
        must be derived from some other category using a ``category_map`` entry in ``esg.<project>.ini``. An error or undefined behavior, such as the sudden absence
        of that facet value from the ``dataset_id``, might result otherwise.

    The ``dataset_name_format`` is a description of the dataset and will appear in the Thredds catalogs and in the Index.

    ::

        dataset_name_format = project=%(project_description)s, model=%(model_description)s, experiment=%(experiment_description)s, time_frequency=%(time_frequency)s


    .. _facet_options:

#. Generate a ``<facet>_options`` list, a ``<facet>_map`` or a ``<facet>_pattern`` for each facet

    The metadata for each facet that is part of the ``directory_format`` (except for `version` and `variable`) is checked against the values in `facet_options`, `facet_map` or `facet_pattern`.

    - ``<facet>_options``

        This is a simple list that contains all possible values for a facet, e.g.:

        ::

            model_options = MPI-ESM-LR, MPI-ESM-MR, MPI-ESM-P
            time_frequency_options = 3hr, 6hr, day, fx, mon, monClim, subhr, yr

        .. warning::
            The option list for the experiments does not follow the above syntax. Each experiment has the format: ``<project> | <experiment> | <experiment_description>``

            Example:

            ::

                experiment_options =
                    cmip5 | 1pctCO2     | 1 percent per year CO2
                    cmip5 | abrupt4xCO2 | Abrupt 4xCO2
                    cmip5 | amip        | AMIP
                    cmip5 | amip4K      | AMIP plus 4K anomaly
                    cmip5 | amip4xCO2   | 4xCO2 AMIP
                    cmip5 | amipFuture  | AMIP plus patterned anomaly
                    cmip5 | aqua4K      | Aqua planet plus 4K anomaly
                    cmip5 | aqua4xCO2   | 4xCO2 aqua planet

    - ``<facet>_map``

        Using a ``<facet>_map`` is recommended if the facet is not part of the ``directory_structure`` and needs to be mapped to another value, e.g. for CORDEX:

        ::

            rcm_name_map = map(project, rcm_model : rcm_name)
                cordex | AWI-HIRHAM5      | HIRHAM5
                cordex | GERICS-REMO2009  | REMO2009
                cordex | KNMI-RACMO22E    | RACMO22E
                cordex | MPI-CSC-REMO2009 | REMO2009
                cordex | UCLM-PROMES      | PROMES

        .. note::
            All <facet>_maps needs to be listed in the project ini file, e.g. ``maps = rcm_name_map, las_time_delta_map``.

    - ``<facet>_pattern``

        A pattern should be used for facets that follow a known syntax, e.g. the ensemble facet:

        ::

            ensemble_pattern = r%(digit)si%(digit)sp%(digit)s

        .. note::
            The <facet>_pattern currently supports ``%(digit)s`` and ``%(string)s`` where ``%(digit)s`` matches any number and ``%(string)s`` one or more character(s).

#. Project Handler

    You can either use the publisher's default handler, a pre-installed project handler or generate a custom handler.

    .. note::
        The setup and configuration of a custom handler needs expert knowledge. For most projects the default handler will be sufficient.
        The handlers for major projects like CMIP5 are pre-installed and for some minor projects you can find
        `customized handlers <https://github.com/ESGF/config/tree/master/publisher-configs/handlers>`_ on github.

    To use the default handler please add the following to your project configuration file:

    ::

       project_handler_name = basic_builtin

    For the pre-installed project handler for CMIP5 add the following:

    ::

        handler = esgcet.config.ipcc5_handler:IPCC5Handler

    For creating a new customized handler you can run the following command that will generate the basic package:

    ::

        $ esgsetup --handler

    Now you can customize the handler by editing the ``project_handler.py`` file and install the handler package with:

    ::

        $ cd <handler_name>
        $ python setup.py install

    In your ``esg.<project>.ini`` file simply add whatever you have specified for the ``project_handler_name`` during the setup.

    ::

        project_handler_name = <project_handler_name>


#. The ``thredds_exclude_variables`` and ``variable_per_file``.

    As mentioned above it is not needed to create a ``variable_options`` list. Instead we need to add a ``thredds_exclude_variables`` list that lists all
    variables that might be part of the file content but are not the `target` variable.

    ::

        thredds_exclude_variables = a, a_bnds, alev1, alevel, alevhalf, alt40, b, ...

    The ``variable_per_file`` should be always set to ``true``. If this is set to false no aggregations will be generated and all variables that are part of the dataset are wrongly assigned to every file.

    ::

        variable_per_file = true

    .. warning::
        If a excludes variable is missing in the ``thredds_exclude_variables`` and ``variable_per_file`` is set to true this might result in publishing the same file multiple times to Thredds.

    If a variable can be `taget` variable **and** `exclude` variable it must be listed in the ``variable_locate``.
    The ``variable_locate`` is a list of variable and begin-of-filename pairs, following the syntax:

    ::

        variable_locate = <var1>,<begin_of_filename1> | <var2>,<begin_of_filename2>

    Example:

    ::

        variable_locate = ps,ps_ | basin,basin_

#. Enable and disable the LAS access

    `The Live Access Server <http://www.ferret.noaa.gov/LAS/home>`_ (LAS) is part of the ESGF Installation and can be used to visualize the data.

    If LAS is enabled the publisher will generate and publish a LAS-link for each dataset and aggregation.

    ::

        # disable LAS
        las_configure = false

        # enable LAS
        las_configure = true

    For LAS you also need a ``las_time_delta_map``, e.g.:

    ::

        las_time_delta_map = map(time_frequency : las_time_delta)
            yr      | 1 year
            mon     | 1 month
            day     | 1 day
            6hr     | 6 hours
            3hr     | 3 hours
            subhr   | 1 minute
            monClim | 1 month
            fx      | fixed

#. (Optional) The ``skip_aggregations`` option:

    If ``skip_aggregations`` is set to ``true``, aggregations will not be created. By default this option is set to ``false``.

.. _policies:

Prepare user and permissions for publication
********************************************

Publish to an index node at another side
----------------------------------------

Please coordinate with that site's node administrator.


Publish to your own index node
------------------------------

#. Verify publishing permissions: ``/esg/config/esgf_policies_local.xml``

    Specifications for datasets are given by regular expression. This could include a data_node or a project, institution, model, etc.
    If you want to publish within a specified collection, ensure that an entry exists for that with a specified ESGF group, publisher role,
    and Write action.

    Example for publication of CMIP5 data only:

    .. code-block:: html
        :linenos:

        <policy resource=".*cmip5.*" attribute_type="cmip5_publisher" attribute_value="publisher" action="Write"/>

    Example for publication of all projects from a particular ESGF node:

    .. code-block:: html
        :linenos:

        <policy resource=".*esgf-test.dkrz.de.*" attribute_type="cmip5_publisher" attribute_value="publisher" action="Write"/>

    .. note::
        Make sure you have the correct permission for both policies files:

        ::

            -rw-r----- 1 tomcat tomcat 5840 Aug  8 10:32 /esg/config/esgf_policies_local.xml
            -rw-r----- 1 tomcat tomcat 1381 Mar 21  2016 /esg/config/esgf_policies_common.xml



#. Group, role and permission in the Postgres database:

    For publication you need to create an ESGF account and add the appropriate role and group to that user. Therefore you have to modify the postgres database:

    ::

        # login to the escet database
        $ psql -U dbsuper esgcet

        # add a new group named cmip5_publisher
        esgcet=# INSERT INTO esgf_security.group VALUES(3, 'cmip5_publisher', 'CMIP5 Publisher', true, true);

        # update permission table
        esgcet=# INSERT INTO esgf_security.permission VALUES(2, 3, 4, true);

    For the example above the tables in esgcet should look like:

    ::

        esgcet=# SELECT * FROM esgf_security.user;

        id | firstname | middlename | lastname |     email     |  username    | ...
        ---+-----------+------------+----------+---------------+--------------+-----
        2  | Publish   |            | User     | email@address | publish_user | ...

        esgcet=# SELECT * FROM esgf_security.group;

            id | name            | description     | visible | automatic_approval
        ----+-----------------+-----------------+---------+--------------------
            3  | cmip5_publisher | CMIP5 Publisher | t       | t

        esgcet=# SELECT * FROM esgf_security.role;

            id | name      | description
        ----+-----------+----------------
            4  | publisher | Data Publisher

        esgcet=# SELECT * FROM esgf_security.permission;

            user_id | group_id | role_id | approved
        ---------+----------+---------+----------
            2       | 3        | 4       | t

#. Ensure that the ESGF group has an entry in the ``/esg/config/esgf_ats_static.xml`` file for the attribute service for that group, e.g.:

    .. code-block:: html
        :linenos:

        <attribute type="cmip5_publisher"
            attributeService="https://<fqdn>/esgf-idp/saml/soap/secure/attributeService.htm"
            description="Publisher group for CMIP5 data"
            registrationService="https://<fqdn>/esgf-idp/secure/registrationService.htm"/>

.. _myproxy_logon:

Myproxy Logon
-------------

For publication to an index node you need to have a valid globus certificate for an user with `Write` permissions.

::

    $ mkdir $HOME/.globus   # if not already present
    $ myproxy-logon [ -b ] -s <openid_server> -l <esgf_username> -p 7512 -t 72 -o $HOME/.globus/certificate-file

.. note::
    The certificate is valid for 72 hours when specified by ``-t``. If you are publishing for the first time, you will need to use ``-b`` to bootstrap it's trustroots with the server.

.. note::
    Please get the ``openid_server`` and ``esgf_username`` from your ESGF OpenID, e.g.

    ::

        openid:        https://pcmdi.llnl.gov/esgf-idp/openid/publish_user
        openid_server: pcmdi.llnl.gov
        esgf_username: publish_user