Release Notes
=============

v5.1.0-b8
---------

* Change ``set-replica`` semantics with respect to PrePARE and add ``force_prepare`` option.

  #. Default behavior is to run PrePARE for non-replica but not for replica.
  #. Wth ``force_prepare=True``, PrePARE is *always* run.

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

* CRITICAL:  corrected File record ID format to include ``|data_node`` to conform to prior specification
* Support for data root specifications that include the project string in the root
* Bug fixes: citiaton case for command line project path, support tilde for homedir in cmor path property in config file

v5.1.0-b5
---------

* Update to support input4MIPs project
* Added ``--version`` argument
* Additonal arguments for esgunpublish
* Halt publishing if a file listed in the mapfile isn't found by autocurator
