.. _esgdd:

esgadd
========

Use this command to add assets to an existing dataset. This command can be used to add individual (NetCDF) files as assets or to add aggregated assets such as reference files, zarr stores, kerchunk references, virtualizarr references, or icechunk references.  The STAC Item (ESGF Dataset) ID must be provided for the dataset to which the assets will be added.
If the assets being added are replicated on Globus, the UUID of the Globus collection and the datanode that will be used to identify the replicated assets can be specified if not present in your configuration file. 
NetCDF files are assumed to be already stored on the file system of the datanode.  The path to the files will be mapped via the ``prefix`` option.  These mappings are specified in the ``data_roots`` value in your configuration file and have been configured in the esgf-docker or Globus share configuration.  
Aggregated assets are assumed to be already accessible at a URL and the URL must be provided with the ``--agg-url`` option.

Command Usage
-------------

``esgadd`` is used with the following::


        usage: esgadd [-h] [--stac-api STAC_API] [--pub-rec JSON_DATA]
                    [--globus-collection-uuid REP_GLOBUS] [--datanode REP_DATANODE]
                    [--agg-url REP_PATH] [--prefix REP_PREFIX] --config CFG [--silent]
                    [--verbose] [--agg AGG] [--dataset-id DATASET_ID]

    Publish data sets to ESGF STAC Transaction API.

    options:
    -h, --help            show this help message and exit
    --stac-api STAC_API   Specify STAC Transaction API.
    --pub-rec JSON_DATA   JSON file output from esgpidcitepub or esgmkpubrec.
    --globus-collection-uuid REP_GLOBUS
                            UUID of Globus collection to access replicated item
    --datanode REP_DATANODE
                            Datanode that will be used to identify replicated assets of the
                            item
    --agg-url REP_PATH    Url of reference file or other aggregated asset to add
    --prefix REP_PREFIX   Url path prefix that proceeds the dataset DRS in the url
    --config, -cfg CFG    Path to yaml config file.
    --silent              Enable silent mode.
    --verbose             Enable verbose mode.
    --agg AGG             Add an aggregtion of the specified type
                            [zarr|kerchunk|virtualizarr|icechunk]. --rep-path is the url for
                            the item
    --dataset-id DATASET_ID
                            ID of the dataset to add the asset (aggregate or files)
            usage: esglogin [-h] [--config CFG]

