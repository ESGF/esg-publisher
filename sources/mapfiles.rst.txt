.. _mapfiles:

Mapfile preparation
===================

Set up default environment for scripts
**************************************

ESGF v2.5 or later

::

    $ source /usr/local/conda/bin/activate esgf-pub

ESGF v2.4.x or earlier

::

    $ source /etc/esg.env

Generate your mapfile(s) using the esgprep utitlity
***************************************************

.. Note:: This documentation refers to esgprep v2.8.x, which featured a significant command-line interface refactor.  For previous versions (v2.7.x) or earlier, instead of using the ``esgmapfile`` command, use ``esgprep mapfile``

Basic usage of esgmapfile
------------------------------

The `esgprep toolbox <https://github.com/ESGF/esgf-prepare>`_ is a standalone tool to generate mapfiles, fetch the project specific configuration files,
check the vocabulary, etc. It will be installed during the esg-publisher setup.

.. seealso:: The full documentation of esgprep toolbox can be found on github: http://esgf.github.io/esgf-prepare/.

The basic command to generate the mapfile(s):

::

    $ esgmapfile [optional: -i <ini_directory> --outdir <output_mapfile>] --project <project_name> <target_path_for_data_files>

This will recursively scan the ``target_path_for_data_files`` and build datasets. If datasets with multiple versions are found it will produce only the latest.
By default it will produce one mapfile per dataset using the syntax ``{dataset_id}.{version}.map`` as filename and the current working directory as output location.


Example: Generate a set of mapfiles

::

    $ esgmapfile --project cmip5 /esg/data/cmip5/output1/MPI-M/MPI-ESM-P/historical/day/atmos/day --outdir /esg/mapfiles

This will produce two mapfiles, i.e.:

::

    $ ls /esg/mapfiles

    cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r1i1p1.v20120315.map
    cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r2i1p1.v20120315.map

    $ less /esg/mapfiles/cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r1i1p1.v20120315.map

    cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r1i1p1#20120315 | /esg/data/cmip5/output1/MPI-M/MPI-ESM-P/historical/day/atmos/day/r1i1p1/v20120315/ta/ta_day_MPI-ESM-P_historical_r1i1p1_19910101-19911231.nc | 403684988 | mod_time=1329808188.000000 | checksum=b644aa3ac81de2ece6098409e1bcd62982c1dd6e9154a3d4ffb71639cba3e721 | checksum_type=SHA256
    cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r1i1p1#20120315 | /esg/data/cmip5/output1/MPI-M/MPI-ESM-P/historical/day/atmos/day/r1i1p1/v20120315/wap/wap_day_MPI-ESM-P_historical_r1i1p1_19790101-19791231.nc | 403685160 | mod_time=1329795098.000000 | checksum=9e5b8e0ecc676e4a484a1c1359ae8bf71aa06f639e88564d649be49bb9a101d3 | checksum_type=SHA256
    cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r1i1p1#20120315 | /esg/data/cmip5/output1/MPI-M/MPI-ESM-P/historical/day/atmos/day/r1i1p1/v20120315/tas/tas_day_MPI-ESM-P_historical_r1i1p1_18500101-18591231.nc | 269357732 | mod_time=1329500471.000000 | checksum=c2926960f90cce3f2884476fa07f5d6ac7d4e83918708259136039f6b904357b | checksum_type=SHA256
    cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r1i1p1#20120315 | /esg/data/cmip5/output1/MPI-M/MPI-ESM-P/historical/day/atmos/day/r1i1p1/v20120315/wap/wap_day_MPI-ESM-P_historical_r1i1p1_19660101-19661231.nc | 403685160 | mod_time=1329780069.000000 | checksum=e0408268c30bd7996ff8553d648bcb48e11f69c8d7428f236ef713d560582542 | checksum_type=SHA256
    cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r1i1p1#20120315 | /esg/data/cmip5/output1/MPI-M/MPI-ESM-P/historical/day/atmos/day/r1i1p1/v20120315/ua/ua_day_MPI-ESM-P_historical_r1i1p1_19930101-19931231.nc | 403684892 | mod_time=1329810439.000000 | checksum=eb448c6b42ab83ec31259b5e6f9d7cfd2bfbce54a2d335c477524173db80ce6c | checksum_type=SHA256
    cmip5.output1.MPI-M.MPI-ESM-P.historical.day.atmos.day.r1i1p1#20120315 | /esg/data/cmip5/output1/MPI-M/MPI-ESM-P/historical/day/atmos/day/r1i1p1/v20120315/sfcWind/sfcWind_day_MPI-ESM-P_historical_r1i1p1_18900101-18991231.nc | 269357640 | mod_time=1329549793.000000 | checksum=de73970345c8175a49b3c4130dc393599817bf3186a8ed6237c742534ed6ffe4 | checksum_type=SHA256

.. _tech_note:

Adding a Technical Note to the mapfile
--------------------------------------

To add a Technical Note to the data (e.g. for obs4MIPs) please run

::

    $ esgmapfile --project <project_name> --tech-notes-url <tech_notes_url> --tech-notes-title <tech_notes_title> <target_path_for_data_files>

Example:

::

    $ esgmapfile --project obs4MIPs --tech-notes-url http://esgf-test.dkrz.de/thredds/fileServer/tech_note.pdf --tech-notes-title 'obs4MIPs Tech Note' /esg/data/obs4MIPs

    $ less obs4MIPs_test.v20160811.map

    obs4MIPs_test#20160811 | /esg/data/obs4MIPs/testfile1.nc | 50989760 | mod_time=1402486592.000000 | checksum=a5ddace30826a440207cdb0bf0f0ea9fd3f2c699a90aef5f71cbbd8f84c50a56 | checksum_type=SHA256 | dataset_tech_notes=http://esgf-test.dkrz.de/thredds/fileServer/tech_note.pdf | dataset_tech_notes_title=obs4MIPs Tech Note
    obs4MIPs_test#20160811 | /esg/data/obs4MIPs/testfile2.nc | 2116695 | mod_time=1402486544.000000 | checksum=37c2e002d67c3408c43be373ced777ed85c78fbe31fee823840b1285f83b9870 | checksum_type=SHA256 | dataset_tech_notes=http://esgf-test.dkrz.de/thredds/fileServer/tech_note.pdf | dataset_tech_notes_title=obs4MIPs Tech Note


Further options of esgmapfile
----------------------------------


- \--mapfile <{dataset_id}.{version}.map>
    Specifies template for the output mapfile(s) name. Substrings {dataset_id}, {version}, {job_id} or {date} (in YYYYDDMM) will be substituted where found. If {dataset_id} is not present in mapfile name, then all datasets will be written to a single mapfile.
- \--all-versions
    Generates mapfile(s) with all versions found in the directory recursively scanned.
- \--version <version_number>
    Generates mapfile(s) scanning datasets with the corresponding version number only. If directly specified in positional argument, use the version number from supplied directory.
- \--latest-symlink
    Generates mapfile(s) following latest symlinks only. This sets the {version} token to "latest" into the mapfile name but picked up the pointed version to build the dataset identifier.
- \--outdir <output_mapfile>
    Mapfile(s) output directory. A "mapfile_drs" can be defined per each project section in esg.<project>.ini files and joined to build a mapfiles tree.
- \--max-threads <4>
    Number of maximal threads to simultaneously process several files (useful if checksum calculation is enabled). Set to one seems sequential processing.
