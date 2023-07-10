Release Notes
=============

v5.2.0
------

* Migrated configuration from `.ini` format to `.yaml`.  Use `esgmigrate` to convert existing `.ini` files.
* Added XArray for NetCDF file reading.  Disable autocurator in settings to use or add `--xarray`
* Additionally refactoring done to support the above features.

b5.1.0-b13
----------

* **BUGFIX**: corrected file URL format for PID/Handle publishing (previously published URLs via v5.* were malformed).
* CMIP6 Cloned project support 
* **NOTE**:  this version is unavailable on Conda (``esgf-forge`` channel), please use ``pip install esgcet`` and confirm the upgrade with ``esgpublish --version``.

b5.1.0-b11
----------

* Updated arguments for esgunpublish
* XML archive functionality (see :ref:`arch_info`.)
* bugfix for use of lower case cmip6 (should become case-insensitive)

b5.1.0-b10
----------

* **CRTICAL**:  esgunpublish checks dataset id argument for publication prior to unpublication to prevent server-side erroneus deletions.

v5.1.0-b9
---------

* Improved Controlled-vocabulary agreement checks and upgraded rules (for CMIP6)
*  Bug fix for input4MIPs (omit CMOR tables load)

v5.1.0-b8
---------

* Change ``set-replica`` semantics with respect to PrePARE and add ``force_prepare`` option.

  #. Default behavior is to run PrePARE for non-replica but not for replica.
  #. With ``force_prepare=True``, PrePARE is *always* run.

* esgunpublish now unpublishes PID from handle database.
* Allow for custom gridftp ports (specify with ``<hostname>:<port>``).
* Correct file instance_id and master_id.

v5.1.0-b7
---------

* Bug fix and refactoring: improved data root handling for paths that contain multiple instances of the project name in the path
* Bug fix for the skip_prepare argument (applies to CMIP6 replica publishing to bypass PrePARE)
* Feature to ensure that file tracking_ids are never duplicated within a dataset

v5.1.0-b6
---------

* **CRITICAL**:  corrected File record ID format to include ``|data_node`` to conform to prior specification
* Support for data root specifications that include the project string in the root
* Bug fixes: citiaton case for command line project path, support tilde for homedir in cmor path property in config file

v5.1.0-b5
---------

* Update to support input4MIPs project
* Added ``--version`` argument
* Additonal arguments for esgunpublish
* Halt publishing if a file listed in the mapfile isn't found by autocurator
