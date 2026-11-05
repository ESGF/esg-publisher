esgpublish
==========

The ``esgpublish`` command publishes a record from start to finish using the mapfile(s) passed to it. On success, it will display a success message in the output of the last two steps.
If an error occurs, a helpful statement will be printed explaining which step went wrong and why.

Usage
-----

``esgpublish`` is used with the following syntax::

        esgpublish --map <mapfile>

The mapfile (``--map``) is the only truly *required* argument, as others are typically supplied through the config file.
You can also use ``--help`` to see all available options::

        $ esgpublish --help
            usage: esgpublish [-h] [--test] [--set-replica] [--no-replica]
                           [--json JSON] [--data-node DATA_NODE]
                           [--index-node INDEX_NODE] [--certificate CERT]
                           [--project PROJ] [--cmor-tables CMOR_PATH]
                           [--autocurator AUTOCURATOR_PATH] --map MAP [MAP ...]
                           [--config CFG] [--silent] [--verbose] [--verify]
                           [--version] [--xarray] [--stac-api STAC_API]
                           [--no-xarray] [--dry-run] [--save-stac]

            Publish data sets to ESGF databases.

        Key arguments:
          --map MAP             Required. Mapfile, file containing list of mapfiles, or directory.
          --project PROJ        Set/override the project for DRS and feature selection.
          --config CFG          Path to yaml config file (default: ~/.esg/esg.yaml or $ESG_CONFIG_FILE).
          --xarray              Use Xarray to extract metadata (default, overrides autocurator).
          --no-xarray           Bypass Xarray for fast metadata-only scanning (see below).
          --dry-run             Scan and validate without publishing to index APIs (see below).
          --save-stac           Save STAC items as JSON files in current directory (see below).
          --stac-api STAC_API   Override STAC API endpoint (typically set in config file stac_config).
          --test                PID registration test mode (recommended unless doing production).
          --set-replica         Enable replica publication.
          --data-node DATA_NODE Specify data node.
          --index-node INDEX_NODE  Specify index node (legacy Solr).
          --certificate CERT    Certificate file in .pem form for authentication.
          --silent              Enable silent mode.
          --verbose             Enable verbose (debug) mode.
          --verify              Toggle certificate verification (default: off for self-signed support).

.. note::
    The ``--stac-api`` flag is primarily for testing or quick overrides. For production use, configure the STAC API endpoint in the ``stac_config`` section of your ``esg.yaml`` configuration file. See :ref:`esglogin` and the installation documentation for proper STAC configuration.

This command can handle a singular mapfile passed to it, a file containing a list of mapfiles (with full paths), a directory of mapfiles, or a directory of lists of mapfiles.
You do not need to specify how you are passing mapfiles, but all of them must be for the same project in order for them to be published with the correct metadata.
If optional command line arguments are used, they will override anything set in the config file.
NOTE: If, in your config file, you have specified a directory for ``autocurator`` rather than the default command, ie you are using a different ``autocurator`` than the one installed using conda, you must run the following command prior to running ``esgpublish``::

    export LD_LIBRARY_PATH=$CONDA_PREFIX/lib

If you do not run this and are not using the conda installed ``autocurator``, the program will not work.

.. note::
    Using the ``--xarray`` argument will override ``autocurator`` whether specified in the config file or the ``--autocurator`` argument.

.. warning::
    Please do not attempt to run `esg-publisher` commands with a legacy esg.ini file using the ``-i`` argumement.   You will need to migrate the config using :ref:`migrate`.

.. _no_xarray_option:

Fast Metadata-Only Scanning
----------------------------

The ``--no-xarray`` flag enables fast, metadata-only NetCDF4 dataset scanning that bypasses Xarray. This is useful when:

* You have large datasets and only need metadata (no data variable inspection)
* Faster scan times are critical
* Full Xarray/Dask graph construction is unnecessary

Usage::

    esgpublish --map <mapfile> --no-xarray

This mode uses ``netCDF4`` library directly to read only global attributes and coordinate variables, avoiding the overhead of constructing a complete Dask graph. Note that some metadata fields may be incomplete compared to full Xarray scanning.

.. _dry_run_option:

Dry Run Mode
------------

The ``--dry-run`` flag performs a complete scan and metadata extraction without actually publishing to any index APIs. This is useful for:

* Testing publication workflows
* Validating data structure and DRS compliance
* Debugging metadata extraction issues
* Previewing what would be published

Usage::

    esgpublish --map <mapfile> --dry-run

In dry run mode, all scanning and record generation occurs normally, but no records are sent to STAC, Solr, or Globus indexes.

.. _save_stac_option:

Saving STAC Items
-----------------

The ``--save-stac`` flag saves generated STAC items to the current working directory as JSON files named ``<dataset-id>.json``. This is useful for:

* Validating STAC item structure before publishing
* Debugging STAC conversion errors
* Archiving STAC items for external use
* Testing STAC item generation

Usage::

    esgpublish --map <mapfile> --save-stac

Each dataset will produce a corresponding ``<dataset-id>.json`` file containing the complete STAC item that would be (or was) published to the STAC API.

Dataset Size Considerations
---------------------------

When publishing datasets, be aware of the following size limitations:

Maximum Recommended File Count
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The publisher will issue a warning if a dataset contains more than **1000 files**. This limit is set by the ``MAX_RECOMMENDED_FILE_COUNT`` constant in ``settings.py``.

**Why this limit exists:**

* **Event payload size limits**: Publishing events sent to backend systems have maximum payload size constraints. Each file in a dataset adds to the event payload.
* **Backend record size limits**: Index databases and search APIs have practical limits on individual record sizes.
* **STAC item size**: Each file becomes an asset in the STAC item JSON. Large numbers of assets can create unwieldy STAC items that exceed API and client size limits.
* **Performance**: Large datasets with many files take longer to process, publish, and query.

**Recommendations for large datasets:**

* **Use aggregation**: Consider using Kerchunk, Zarr, or other aggregation formats to represent multiple files as a single virtual dataset.
* **Split datasets**: Divide datasets by time periods, variables, or other logical boundaries to keep individual datasets under the recommended limit.
* **Optimize granularity**: Balance between too many small datasets and too few large datasets. Datasets with 100-500 files are typically optimal for performance.

The warning is informational - publishing will continue, but you may encounter issues with backend systems if the file count is significantly higher than the recommended maximum.

.. _kerchunk_generation:

Kerchunk and VirtualiZarr Aggregation Generation
-------------------------------------------------

The ``esgpublish`` command can automatically generate Kerchunk or VirtualiZarr reference files during the publishing process. These aggregation files allow efficient access to NetCDF datasets without data duplication by creating virtual datasets from reference metadata.

What are Kerchunk and VirtualiZarr?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* **Kerchunk**: Creates JSON reference files that map chunk locations in NetCDF files, enabling cloud-optimized access to existing NetCDF data through Zarr-compatible readers
* **VirtualiZarr**: A newer approach that creates similar reference structures with improved performance and additional features

Both allow you to:

* Access multiple NetCDF files as a single virtual dataset
* Enable cloud-optimized data access without data migration
* Reduce storage requirements (reference files are small compared to actual data)
* Improve performance for analysis workflows

Configuration
^^^^^^^^^^^^^

To enable automatic Kerchunk/VirtualiZarr generation, add a ``kerchunk`` section to your ``esg.yaml`` configuration file:

.. code-block:: yaml

    kerchunk:
      generation: true                    # Enable generation
      backend: "kerchunk"                 # or "virtualizarr"
      inline_threshold: 0                 # Threshold for inlining small chunks (bytes)
      filter_frequency: "mon"             # Only process monthly and coarser frequencies
      data_dir:
        /path/to/output: "https://example.com/kerchunk"  # Local dir: public URL

**Configuration Options:**

* ``generation`` (boolean, required): Set to ``true`` to enable reference file generation
* ``backend`` (string, required): Choose ``"kerchunk"`` or ``"virtualizarr"``
* ``inline_threshold`` (integer, optional): Size threshold in bytes for inlining chunk data directly in the reference file (default: 0). Set to 0 to store all data as references
* ``filter_frequency`` (string, optional): Only generate references for datasets at or coarser than this temporal frequency. Valid values: ``"subhr"``, ``"1hr"``, ``"3hr"``, ``"6hr"``, ``"day"``, ``"mon"`` (default), ``"yr"``, ``"dec"``, ``"fx"``. If not specified, defaults to ``"mon"`` (monthly and coarser)
* ``data_dir`` (mapping, required): Maps local output directory to the public URL where reference files will be accessible

  * Key: Absolute path where reference files should be written
  * Value: Public HTTPS URL where these files will be served

**Required Configuration:**

The following must also be set in your config file for kerchunk generation to work:

* ``data_roots``: Maps local data paths to URL path components (used for constructing file URLs in references)
* ``data_node``: Your data node hostname (used to build HTTPS URLs to NetCDF files)

Example Configuration
^^^^^^^^^^^^^^^^^^^^^

Complete example showing all required and optional settings:

.. code-block:: yaml

    data_node: esgf-node.example.org
    data_roots:
      /data/archive/: "esgf_dataroot"   # Local path prefix: URL path component

    kerchunk:
      generation: true
      backend: "virtualizarr"            # Use VirtualiZarr
      inline_threshold: 100              # Inline chunks < 100 bytes
      filter_frequency: "day"            # Process daily and coarser
      data_dir:
        /data/kerchunk: "https://esgf-node.example.org/kerchunk"

Usage
^^^^^

Once configured, kerchunk generation happens automatically during normal publishing:

.. code-block:: bash

    esgpublish --map dataset.map --config ~/.esg/esg.yaml

The publisher will:

1. Process each dataset in the mapfile
2. Check if the dataset's temporal frequency meets the filter criteria
3. Generate reference files using the specified backend
4. Save reference files to the configured ``data_dir`` location
5. Include reference file URLs in the published STAC metadata as aggregation assets

Output files are named: ``<dataset-id>.v<version>.json.<backend>``

Adding Pre-Generated References
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you've already generated reference files outside the publishing workflow, you can add them to existing datasets using :ref:`esgdd`:

.. code-block:: bash

    esgadd --dataset-id <dataset-id> --agg kerchunk --agg-url https://example.com/refs.json
    # or
    esgadd --dataset-id <dataset-id> --agg virtualizarr --agg-url https://example.com/refs.json

For more information: `Kerchunk <https://fsspec.github.io/kerchunk/>`_, `VirtualiZarr <https://virtualizarr.readthedocs.io/>`_, `Zarr <https://zarr.readthedocs.io/>`_

CMIP6 Variable Metadata Remapping
----------------------------------

The publisher can optionally enrich STAC items with standardized CMIP6 variable metadata from the esgvoc vocabulary service. This is useful when NetCDF file metadata is incomplete or needs to be validated against the official CMIP6 controlled vocabulary.

What Gets Added
^^^^^^^^^^^^^^^

When enabled, the following properties are added to STAC items for CMIP6 datasets:

* ``cmip6:variable_units`` - Physical units from the CMIP6 vocabulary (e.g., "Pa", "K", "kg m-2 s-1")
* ``cmip6:cf_standard_name`` - CF standard name from the CMIP6 vocabulary (e.g., "air_pressure_at_mean_sea_level")

These properties are only added when values are available in the vocabulary. If a variable is not found or has no units/standard_name, the properties are omitted.

Configuration
^^^^^^^^^^^^^

Add to the ``stac_config`` section of your ``esg.yaml`` configuration file:

.. code-block:: yaml

    stac_config:
      stac_api: https://discovery.west.esgf.io
      cmip6_variable_remap: true  # Enable variable metadata remapping (default: false)

The feature is **disabled by default** to avoid adding overhead when not needed.

Usage
^^^^^

Once configured, remapping happens automatically during normal publishing:

.. code-block:: bash

    esgpublish --map dataset.map --config ~/.esg/esg.yaml

The publisher will:

1. Process CMIP6 datasets normally
2. For each dataset, query the esgvoc API for the variable metadata
3. Add the standardized properties to the STAC item if found
4. Log a debug message on success or warning if variable not found

Example STAC Output
^^^^^^^^^^^^^^^^^^^

With remapping enabled, a CMIP6 STAC item will include:

.. code-block:: json

    {
      "properties": {
        "cmip6:variable_id": "psl",
        "cmip6:variable_units": "Pa",
        "cmip6:cf_standard_name": "air_pressure_at_mean_sea_level"
      }
    }

Use Cases
^^^^^^^^^

* **Quality Control**: Validate that NetCDF file metadata matches the official vocabulary
* **Metadata Completion**: Fill in missing units or standard names
* **Standardization**: Ensure consistent metadata across datasets from different institutions
* **Discovery**: Improve search and filtering by standard names and units

The feature queries the esgvoc vocabulary service which maintains the authoritative CMIP6 controlled vocabulary. For more information about esgvoc, see: https://github.com/ESGF/esgf-vocab

.. _arch_info:

Archiving Info
--------------

Dataset records (metadata) can be preserved in xml form for future use if the need arises to rebuild an index.
(This functionality replaces the ability to reharvest THREDDS catalog that was available with the prior ESGF/publisher architecture).  XML files are created for both the dataset and every file record: one file per each record, eg. if there are *two* files for a dataset, *three* xml files are generated in total.
There are three config file options that must be set in order to enable the archive:

* enable_archive
   * Set to True to enable the feature
* archive_location
   * Path on local file system to build directory tree and write xml files for record archive.
* archive_depth
   * Controls the directory depth of subdirectories to create/use in the xml archive

The ``esgindexpub`` subcommand has the ``--xml-list`` option.  Supply a file containing a list of paths to xml files within the archive in order to push the recods to the index node.
