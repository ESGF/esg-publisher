.. _usage:

Usage
=====

Preliminary
***********

Set up default environment for scripts:

::

    $ source /etc/esg.env

Publication and unpublication to an index node also requires a valid globus certificate.
By running ``esgpublish`` or ``esgunpublish`` a globus certificate will be generated automatically. Please specify your credentials for the certificate either by filling out the user prompts
during the publication or add the credential information to your ``esg.ini`` file, see :ref:`myproxy section <myproxy_section>`.


In case the certificate generation fails for some reason, please create the certificate manually, see :ref:`myproxy_logon`.

Publication
***********

The data publication has three components:

    #. A local **postgres database**
    #. Local **Thredds (TDS) catalogs**
    #. A **Solr Index**, either local or on another ESGF node

To be visible in the federation you need to publish to all three components and use one of the federated Indexes.

**Some basics**:

    Show the help message and all options of ``esgpublish``:

    ::

        $ esgpublish -h

    The publisher takes a directory containing mapfiles or a single mapfile as input. If a mapfile directory is specified, it is scanned recursively and all containing mapfiles are published.

    ::

        $ esgpublish --project <project_name> --map <mapfile or mapfile_directory>

    Use ``esg-node`` to show or change the index node you are publishing to:

    ::

        $ esg-node --get-index-peer
        $ esg-node --set-index-peer <index_fqdn>


Publish to local postgres database
----------------------------------

This step will scan the data files using the `uvcdat toolbox <http://uvcdat.llnl.gov/index.html>`_ , validate the facet values using ``esg.<project>.ini`` and publish
all data from the mapfile(s) to the local postgres database.

::

   $ esgpublish [optional: -i <path_to_ini_files>] --project <project_name>  --map <input_mapfile or mapfile_directory> --service fileservice [--set-replica]


.. note::
    ``--service fileservice`` will add the services specified as ``fileservice`` in esg.ini's ``thredds_file_services``.

Example:

::

   $ esgpublish --project cmip5 --service fileservice --map /esg/mapfiles

    INFO       2016-08-09 13:59:37,073 Creating dataset: cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r1i1p1
    INFO       2016-08-09 13:59:37,079 Scanning /esg/data/cmip5/output1/MPI-M/MPI-ESM-P/historical/day/atmos/day/v20120315/clt/clt_day_MPI-ESM-P_historical_r1i1p1_19500101-19591231.nc
    INFO       2016-08-09 13:59:37,161 Scanning /esg/data/cmip5/output1/MPI-M/MPI-ESM-P/historical/day/atmos/day/v20120315/clt/clt_day_MPI-ESM-P_historical_r1i1p1_19600101-19691231.nc
    ...
    INFO       2016-08-09 13:59:37,383 New dataset version = 20120315
    INFO       2016-08-09 13:59:37,385 Adding file info to database
    INFO       2016-08-09 13:59:37,587 Aggregating variables


For the above example this will add two datasets and several files in the postgres database:

::

   esgcet=# SELECT * FROM dataset WHERE name LIKE 'cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day%';

      id  |                             name                              | project | ...
    ------+---------------------------------------------------------------+---------+-----
     3161 | cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r1i1p1 | cmip5   | ...
     3162 | cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r2i1p1 | cmip5   | ...
    (2 rows)

    esgcet=# SELECT * FROM file WHERE dataset_id=3161 OR dataset_id=3162;

      id   | dataset_id |                              base                        | format
    -------+------------+----------------------------------------------------------+--------
     92804 |       3161 | clt_day_MPI-ESM-P_historical_r1i1p1_19500101-19591231.nc | netCDF
     92805 |       3161 | clt_day_MPI-ESM-P_historical_r1i1p1_19600101-19691231.nc | netCDF
      ...  |       ...  |                         ...                              |  ...
     93912 |       3162 | zg_day_MPI-ESM-P_historical_r2i1p1_19820101-19821231.nc  | netCDF
      ...  |       ...  |                         ...                              |  ...
    (1132 rows)



Publish to local Thredds server
-------------------------------

The publication of the Thredds catalogs will use the local postgres database as input and generate one catalog per dataset in XML format, added to the default location ``/esg/content/thredds/esgcet``
It is recommended to set a umask so files are world readable, directories accessible, i.e. ``r-x``.
Also make sure the (unix-) user you use for publication has write access to the THREDDS catalogs in ``/esg/content/thredds/esgcet/``.

::

   $ esgpublish [optional: -i <path_to_ini_files>] --project <project_name>  --map <input_mapfile or mapfile_directory> --service fileservice --noscan --thredds [--no-thredds-reinit]


.. note::
    ``--noscan`` skips the netcdf scan of each file. This is useful since the scan was already done in the previous publication step to the database.

.. note::
    If you use a mapfile_directory as input the thredds catalog is reinitialized/rechecked only once, after all mapfiles have been processed. If you prefer to pass only one mapfile per
    esgpublish call and you are publishing a series of mapfiles its unnecessary to have THREDDS reinitialize the catalog on each call to ``esgpublish``. Use the additional argument
    ``--no-thredds-reinit`` to all calls and finish the publication with ``$ esgpublish --thredds-reinit`` to reinitialize/recheck the catalog.

Example:

::

    $ esgpublish --project cmip5 --service fileservice --map /esg/mapfiles --noscan --thredds

    INFO       2016-08-09 14:07:21,767 Writing THREDDS catalog /esg/content/thredds/esgcet/13/cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r1i1p1.v20120315.xml
    INFO       2016-08-09 14:07:21,767 Writing THREDDS catalog /esg/content/thredds/esgcet/13/cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r2i1p1.v20120315.xml
    INFO       2016-08-09 14:07:21,945 Writing THREDDS ESG master catalog /esg/content/thredds/esgcet/catalog.xml
    INFO       2016-08-09 14:07:21,993 Reinitializing THREDDS server

For the above example this will generate two Thredds catalogs and add the catalog entry to the postgres database:

::

    $ ls /esg/content/thredds/esgcet/13

    /esg/content/thredds/esgcet/13/cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r1i1p1.v20120315.xml
    /esg/content/thredds/esgcet/13/cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r2i1p1.v20120315.xml

::

    esgcet=# SELECT * FROM catalog WHERE dataset_name LIKE 'cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day%';

                                 dataset_name                      | version  |                                       location                                 | rootpath
    ---------------------------------------------------------------+----------+--------------------------------------------------------------------------------+----------
     cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r1i1p1 | 20120315 | 13/cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r1i1p1.v20120315.xml | cmip5
     cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r2i1p1 | 20120315 | 13/cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r2i1p1.v20120315.xml | cmip5

.. note::
    You can check for the Thredds catalogs on your local Thredds server: http://<fqdn>/thredds/catalog/esgcet/catalog.html

Publish to index node
---------------------

The publication to the Index node will read the Thredds catalogs and publish the datasets to Solr using ESGF's `esg-search <https://github.com/ESGF/esg-search>`_.

::

   $ esgpublish [optional: -i <path_to_ini_files>] --project <project_name> --map <input_mapfile or mapfile_directory> --service fileservice --noscan --publish


Example:

::

    $ esgpublish --project cmip5 --service fileservice --map /esg/mapfiles --noscan --publish

    INFO       2016-08-09 14:10:23,767 Publishing: cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r1i1p1
    INFO       2016-08-09 14:10:28,116   Result: SUCCESSFUL
    INFO       2016-08-09 14:10:28,767 Publishing: cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r2i1p1
    INFO       2016-08-09 14:10:31,116   Result: SUCCESSFUL

.. note::
    The data should now be visible in the Index (http://<index_fqdn>/esg-search/search?) and in CoG: http://<index_fqdn>.

Publish to postgres, Thredds and the Index in one step
------------------------------------------------------

.. warning::
    It is not recommended to publish to all components in one step. Please use this call only in case you are sure your configuration is set up correctly.

::

   $ esgpublish [optional: -i <path_to_ini_files>] --project <project_name> --map <input_mapfile or mapfile_directory> --service fileservice --thredds --publish


Adding a Technical Note to a dataset
------------------------------------

Some projects require to add a Technical Note to the datasets (e.g. obs4MIPs). This can be done by adding the tech note information to the mapfile, see section :ref:`tech_note`.
The publisher will automatically use the information in the mapfile to publish the Technical Note to the postgres, Thredds and Solr.


Useful options
--------------

- Echo all SQL commands:

    ::

        $ esgpublish --project <project> --map <map> --echo-sql

- Specify the directory containing all configuration files, By default it is set to `/esg/config/esgcet`.

    ::

        $ esgpublish --project <project> --map <map> --i <init_directory>


- Name of output log file. Overrides the configuration log_filename option. Default is standard output.

    ::

        $ esgpublish --project <project> --map <map> --log <log_file>

- Specify the version number. This option is only needed if the version is not included in the mapfile (using the ``dataset_name#version`` syntax).

    ::

        $ esgpublish --project <project> --map <map> --new-version <version_number>

- This will skip the scan of the files. Assumes that the scan has already been done and all information was added to the database. Use this option only with ``--thredds`` or ``--publish``.

    ::

        $ esgpublish --project <project> --map <map> --noscan [--thredds] [--publish]

- Skip the reinitialization/recheck of the Thredds catalogs. This option can be used if you run a series of `esgpublish` calls with a single mapfile as input. Finish the publication with ``--thredds-reinit`` to reinitialize/recheck the catalog. This option is not necessary if you pass a mapfile_directory as input, in this case the thredds catalog is reinitialized/rechecked only once, after all mapfiles have been processed.

    ::

        $ esgpublish --project <project> --map <map> --no-thredds-reinit
        $ esgpublish --thredds-reinit

- Publish the dataset to the index node. Needs Thredds catalogs of the dataset. (Use ``--noscan`` to skip the scan of the files.)

    ::

        $ esgpublish --project <project> --map <map> --publish [--noscan]

- Set a `replica` flag to the data.

    ::

        $ esgpublish --project <project> --map <map> --set-replica

- Create the Thredds catalogs and reinitialize/recheck the Thredds Server  unless ``--no-thredds-reinit`` is set. (Use ``--noscan`` to skip the scan of the files.)

    ::

        $ esgpublish --project <project> --map <map> --thredds [--noscan]

- Publish a single dataset to Thredds or the index, assumes the file information are already in database.

    ::

        $ esgpublish --project <project> --use-existing <dataset_name[#version]>

- Like `use-existing`, but read the list of dataset names from a file, containing one dataset name per line.

    ::

        $ esgpublish --project <project> --use-list <dataset_list>

- Use the version indicated in the version_list. version_list is a file, each line of which has the form: ``dataset_id | version``. Not needed if you use the ``dataset#version`` syntax in the mapfile(s).

    ::

        $ esgpublish --project <project> --map <map> --version-list <version_list>



Unpublication
*************

.. warning::
    If you unpublish a dataset passing only the dataset_name it will unpublish all versions of the dataset.
    To unpublish a single version use the ``dataset_name#version`` syntax, e.g.: ``cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r1i1p1#20120315``.

You could either use a ``mapfile directory``, a single ``mapfile`` a ``dataset`` or a ``dataset_list`` as input for the data unpublication:

- Using a mapfile directory or a single mapfile

    ::

        $ esgunpublish --project <project> --map <input_mapfile or mapfile_directory>

- Using a list

    ::

        $ esgunpublish --project <project> --use-list <list-of-datasets-filename>

    .. note::
        To obtain the a list of datasets, there are several alternatives.  On the command line you can use ``$ esglist_datasets --no-header --select name <project>``

- Using a single dataset_name

    ::

        $ esgunpublish --project <project> dataset_name[#version]



Delete from Index and Thredds
-----------------------------

Delete the data from Index, remove the THREDDS catalog, reinitialize/recheck the Thredds Server but keep the data on postgres.

::

    $ esgunpublish --project cmip5 --map /esg/mapfiles


Delete from Index
-----------------

Delete the data from Index but keep the Thredds catalogs and postgres entries.

::

    $ esgunpublish --project cmip5 --map /esg/mapfiles --skip-thredds


Delete from Thredds
-------------------

Delete the Thredds Catalogs, but keep the data available on the Index node and on the postgres database.

::

    $ esgunpublish --project cmip5 --map /esg/mapfiles --skip-index

Delete from all components
--------------------------

The data will be removed from postgres, Thredds and the Index node.

::

    $ esgunpublish --project cmip5 --map /esg/mapfiles --database-delete

.. warning::
    Use ``--database-delete`` to unpublish test data only. It is highly recommended to keep a history of all production data in postgres.
