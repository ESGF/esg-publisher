# ESGF Publisher

`v5.1.0b10` is the latest Pre-release version of the ESGF Publisher.  We recommend everyone to upgrade and test this version for CMIP6 data.

See: https://esg-publisher.readthedocs.io/en/latest

### Release notes:

#### v5.1.0-b9,10

* CRTICAL: esgunpublish checks dataset id argument for publication prior to unpublication to prevent server-side erroneus deletions.
* Improved Controlled-vocabulary agreement checks and upgraded rules (for CMIP6)
* Bug fix for input4MIPs (omit CMOR tables load)

#### v5.1.0-b8

* Change ``set-replica`` semantics with respect to PrePARE and add ``force_prepare`` option
   - default behavior is to run PrePARE for non-replica but not for replica
   - with ``force_prepare=True``, PrePARE is *always* run
* esgunpublish now unpublishes PID from handle database
* Allow for custom gridftp ports (specify with ``<hostname>:<port>``)
* Correct file instance_id and master_id

#### v5.1.0-b7

* Bug fix and refactoring: improved data root handling for paths that contain multiple instances of the project name in the path
* Bug fix for the skip_prepare argument (applies to CMIP6 replica publishing to bypass PrePARE)
* Feature to ensure that file tracking_ids are never duplicated within a dataset

#### v5.1.0b6

* **CRITICAL:** corrected File record ID format to include |data_node to conform to prior specification
* Support for data root specifications that include the project string in the root
* Bug fixes: citiaton case for command line project path, support tilde for homedir in cmor path property in config file

#### v5.1.0b5

* Update to support input4MIPs project
* Added `--version` argument
* Additonal arguments for esgunpublish
* Halt publishing if a file listed in the mapfile isn’t found by autocurator (it will not through an error as)

#### v5.1.0b1

* Refactored classses for improved code reuse (among other features)
* `--no-auth` mode for testing with esgf-docker publisher API


#### v5.0.0a12

* Cleans up output (verbose, silent) modes for some of the functionality

#### v5.0.0a11 

* Corrects error with activity check

#### v5.0.0a10

* Properly updates File record latest=false when replacing a version
* Fixes issue of Globus/GridFTP url defaults: the default is for no urls if the settings aren't populated

## Legacy version v3.*, v4.* (python3 pre-release)


https://esgf.github.io/esg-publisher 

Requirements:  most requirements are listed in requirements.txt.  Other requirements must be deployed via conda, include cdms2, cdtime and cmor (for CMIP6, other projects coming soon).  

Installation:  the most convenient method to install is via pip.  To capture all dependencies, consider installation of the predetermined conda environment: https://github.com/ESGF/esgf-devOps/blob/master/esgf-pub_env.yml

29 October 2019 version 3.7.3

* Bugfixes and version compatibility updates

22 March 2019 version 3.7.0

* Remove calls to esgfetchini and the esgprep requirement.  Install esgprep separately with pip.

13 March 2019 version 3.6.2

* Skip THREDDS reinit during esgsetup - solves installation issue for successful status code return
* PrePARE to run on each input file rather than first in dataset
* Fix some package versions, eg. requests, SQLAlchemy
* Version information from esgpublish

18 December 2018  version 3.5.6

* process files in sorted order
* bugfix for certs location config
* new config option to skip validation of standard names

26 June 2018 - version 3.5.2

* REST API is default for both publish and unpublish ; support to use the ESGF CA bundle
* Switching data specs versions during operations
* esgtest_publish supports download test and skip-unpublish modes of operation
* new processing modes:
   - --skip-aggregation  
   - --commit-every  allows for more frequent database commits to aid in reducing memory footprints

Note - logging controlled now by the [DEFAULT] section of esg.ini. If you have upgraded the publisher with a previous version of the file, you may notice that the old setting is WARNING, in which case, INFO level messages may not appear.  Thus, the publisher may run successfully without any output.  



16 August 2017 - version 3.2.6

* Support for CMIP6 
- integration of PrePARE
- PID creation via RabbitMQ
- cdf2cim included
- handler for non-netCDF and skip variable scan for multiple cases

29 August 2016 - version 3.1.0

* Changes to support CMIP6
  - Configuration option to extract global attributes
  - Check for CMOR version in datafiles
  - CF checker integration
  - CMIP6-CV check integration (requires CMOR install)
* Included documentation (requires sphinx, sphinx_rtd_theme)

03 August 2016 - version 3.0.1

* Setup.py inclusion of esgprep utility - see http://esgf-prepare.readthedocs.io/ for more information
* Use of project-specific esg.ini files read from the default location
* Support for multiple mapfiles within a single directory
* support for comma or space-delimited facets


Previous versions:

06 July 2015 - version 2.13.0

 * Support for multithreaded checksumming
 * Version pick up in esgscan and use in esgpublish
 * esgfind_excludes to find files in the thredds exclude property
 * Add optional facet values with esgadd_facetvalues for published datasets
 * ACME file handler to support publication of netCDF + other formats in single data set

14 January 2015 - version 2.12.2

 * Warning message for esgscan_directory failues
 * --nodbwrite flag to enable "dry run" for fileO validation without writing to postgreSQL database
 * Additional utility scripts: 
      meta_synchro.py - metadata syncronization checks for PGSQL, Thredds and SOLR
     gen_versions.py, add_checksums_to_map.sh  - used for replica publication (at LLNL/PCMDI)
    

