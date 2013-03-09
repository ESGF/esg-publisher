""" Publisher / Replica Client API """

from sqlalchemy import create_engine
from publish import publishDatasetList
from esgcet.config import loadConfig, registerHandlers
from wrappers import esgpublishWrapper, initdb, esgscanWrapper

def scanDirectory(directoryList, project, outputMapfile, datasetId=None, append=False, filter='.*\.nc$', offline=False, service=None, readFiles=False):
    """
    Scan one or more directories, and generate a mapfile. The mapfile may then be input to ``generateReplicaThreddsCatalog``.
    No return value.

    directoryList
      A list of directory names to scan.

    project
      String project name. 

    outputMapfile
      String path of the output map file to be generated. If None, output to standard output. If append is True, the map is appended to the existing file.

    datasetId=None
      String dataset identifier. If not specified, the dataset is generated as specified in the publisher configuration file.

    append=False
      Boolean flag. If True, append the result to the existing outputMapfile.

    filter='.*\.nc$'
      String regular expression defining which files (contained in a directory in the directoryList) should be included in the output mapfile. By default only netCDF files are included.

    offline=False
      Boolean flag. If True, the dataset(s) are flagged as offline, meaning that no attempt is made to open and scan metadata from the files. The service argument defines how offline datasets are listed.

    service=None
      A service identifier, matching a service identifier in the publisher configuration file. Used to determine how offline datasets should be listed.

    readFiles=False
      If True, read metadata from the data files themselves rather than the directory names.

    """
    if append:
        appendPath = outputMapfile
        outputMapfile = None
    else:
        appendPath = None
    esgscanWrapper(directoryList, projectName=project, outputPath=outputMapfile, datasetName=datasetId, appendPath=appendPath, fileFilt=filter, offline=offline, service=service, readFiles=readFiles)

def generateReplicaThreddsCatalog(mapfile, operation, sourceCatalogDictionary, sourceGateway=None, datasetId=None, offline=False, service=None, comment=None, version=None, project=None, readFiles=False):
    """
    Scan a collection of files as defined in a mapfile, and generate THREDDS catalogs of the resulting datasets. A dictionary of catalogs is returned. The catalogs are not written to the THREDDS catalog directory, but are returned as strings. This allows the generated catalogs to be compared with the corresponding source catalogs.

    Returns a dictionary mapping datasetId => String THREDDS catalog.

    mapfile
      String path to a dataset mapfile, as input to ''readDatasetMap''.

    operation
      Define how the dataset(s) should be created relative to existing dataset(s) with the same identifier.
      One of the following, as defined in esgcet.publish:

      CREATE_OP: Create new replica dataset(s)
      UPDATE_OP: Append to existing dataset(s)
      REPLACE_OP: Replace existing dataset(s)

    sourceCatalogDictionary
      A dictionary mapping datasetId => String source THREDDS catalog. The source catalogs contain extra metadata not obtainable from the data files.

    sourceGateway=None
      String identifier of the source gateway, such as "ESG-PCMDI" or "ESG-NCAR".

    offline=False
      Boolean flag, if True the dataset(s) are flagged as offline, and no attempt is made to scan files for metadata.

    service=None
      String service name, matching a service identifier in the configuration file. Specifies the file lister to be used.

    comment=None
      String comment.

    version=None
      Integer version.

    project=None
      String project name.

    readFiles=False
      If True, read metadata from the data files themselves rather than the directory names.
    """
    resultThreddsDictionary = {}
    esgpublishWrapper(datasetMapfile=mapfile, publishOp=operation, masterGateway=sourceGateway, datasetName=datasetId, offline=offline, service=service, message=comment, thredds=True, las=False, publish=False, threddsCatalogDictionary=resultThreddsDictionary, version=version, reinitThredds=False, projectName=project, readFiles=readFiles)
    return resultThreddsDictionary

def publishCatalogs(threddsCatalogDictionary, parentDatasetIdDictionary, thredds=True, las=True, publish=True):
    """
    Add one or more THREDDS catalogs to the THREDDS catalog directory, reinitialize THREDDS, and publish the catalogs to the gateway.

    Returns a dictionary mapping (datasetName, version) => status, as returned from ``publish.publishDatasetList``. If ``publish`` is False, the return dictionary is empty. 

    threddsCatalogDictionary
      Dictionary of THREDDS catalogs, as returned from ``generateReplicaThreddsCatalog``. The dictionary maps datasetId => String THREDDS catalog.

    parentDatasetIdDictionary
      Dictionary mapping datasetId => parent dataset identifier in the gateway hierarchy.

    thredds=True
      Boolean flag. If True, copy the catalogs to the THREDDS catalog directory and reinitialize the TDS server.

    las=True
      Boolean flag. If True, reinitialize the LAS server.

    publish=True
      Boolean flag. If True, publish the catalog(s) to the gateway.
    
    """
    # Load the configuration and set up a database connection
    config, Session = initdb()

    # Register project handlers
    registerHandlers()

    datasetNames = threddsCatalogDictionary.keys()
    result = publishDatasetList(datasetNames, Session, publish=publish, thredds=thredds, las=las, parentId=parentDatasetIdDictionary, threddsCatalogDictionary=threddsCatalogDictionary, reinitThredds=None, readFromCatalog=True)
    return result

