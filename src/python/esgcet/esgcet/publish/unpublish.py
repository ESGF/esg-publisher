import os
import socket
import string
from esgcet.model import *
from esgcet.config import getConfig
from hessianlib import Hessian, RemoteCallException
from publish import PublicationState, PublicationStatus
from time import sleep
from thredds import updateThreddsMasterCatalog, reinitializeThredds
from las import reinitializeLAS
from utility import issueCallback, getHessianServiceURL, getRestServiceURL, parseSolrDatasetId, getServiceCertsLoc
from esgcet.messaging import debug, info, warning, error, critical, exception
from rest import RestPublicationService

def datasetOrVersionName(name, version, session, deleteAll=False, restInterface=False):
    """
    Determine if the name refers to a dataset or dataset version.

    Returns (deleteAll, datasetObj, [versionObjs], isLatestVersion) where:

    datasetObj is the related dataset object, or None if neither the dataset or version is found;
    [versionObj] is a list of version objects to be deleted. isLatestVersion is True iff this
    version is the latest one for the dataset. It is not considered an error if the version
    does not exist in the local database, since it may still exist in THREDDS and/or the gateway.

    name
      String name to look up.

    session
      A database Session **instance**.

    version
      Version to delete. If version is -1, all version objects for the dataset are returned.

    deleteAll
      Boolean, if True delete all versions of the dataset(s).

    restInterface
      Boolean, if True then name has the form 'master_id.version|data_node'.

    """

    # Parse a SOLR dataset ID if the RESTful interface is used
    if restInterface:
        saveName = name
        name, version, data_node = parseSolrDatasetId(name)
        if data_node is None:
            warning("Dataset: %s, REST interface dataset identifiers should have the form dataset_id|data_node"%saveName)

    # Lookup the dataset
    dset = session.query(Dataset).filter_by(name=name).first()

    deleteAll = (deleteAll or version==-1)
    isLatest = False
    if dset is None:
        dsetVersionObjs = []
    else:                               # It's a dataset

        # Check if this is the latest version
        versionObj = dset.getVersionObj(version=version)
        if versionObj is None:
            warning("Version %d of dataset %s not found"%(version, dset.name))
            isLatest = False
        else:
            isLatest = versionObj.isLatest()
            
        # If this is the only version, delete the entire dataset
        deleteAll = deleteAll or (versionObj is not None and len(dset.versions)==1)

        if deleteAll:
            dsetVersionObjs = dset.versions
        else:
            if versionObj is None:
                dsetVersionObjs = []
            else:
                dsetVersionObjs = [versionObj]

    return (deleteAll, dset, dsetVersionObjs, isLatest)

def deleteGatewayDatasetVersion(versionName, gatewayOperation, service, session, dset=None, data_node=None):
    """
    Delete a dataset version from the gateway.

    Returns (*event_name*, *state_name*) where *event_name* is the
    associated event, such as ``esgcet.model.DELETE_GATEWAY_DATASET_EVENT``,
    and *state_name* is 'SUCCESSFUL' or 'UNSUCCESSFUL'

    versionName
      String dataset identifier (foo.bar.vN).

    gatewayOperation
      DELETE or UNPUBLISH

    service
      Hessian proxy web service

    session
      A database Session **instance**.

    dset
      Parent dataset of the version. If None, don't record the deletion event.

    data_node
        String, the datanode to unpublish (only for unpublication from Solr)

    """

    # Clear publication errors from dataset_status
    if dset is not None:
        dset.clear_warnings(session, PUBLISH_MODULE)

    if gatewayOperation==DELETE:
        successEvent = DELETE_GATEWAY_DATASET_EVENT
        failureEvent = DELETE_DATASET_FAILED_EVENT
    else:
        successEvent = UNPUBLISH_GATEWAY_DATASET_EVENT
        failureEvent = UNPUBLISH_DATASET_FAILED_EVENT

    # Delete
    try:
        if gatewayOperation==DELETE:
            info("Deleting %s"%versionName)
            if service.service_type == 'REST':
                dataset_id = '%s|%s' % (versionName, data_node)
                service.deleteDataset(dataset_id, True, 'Deleting dataset')
            elif data_node:
                try:
                    service.deleteDatasetSingleDataNode(versionName, data_node, True, 'Deleting dataset')
                except:
                    service.deleteDataset(versionName, True, 'Deleting dataset')
            else:
                service.deleteDataset(versionName, True, 'Deleting dataset')
        else:
            info("Retracting %s"%versionName)
            if service.service_type == 'REST':
                dataset_id = '%s|%s' % (versionName, data_node)
                service.retractDataset(dataset_id, True, 'Retracting dataset')
            elif data_node:
                try:
                    service.retractDatasetSingleDataNode(versionName, data_node, True, 'Retracting dataset')
                except:
                    service.retractDataset(versionName, True, 'Retracting dataset')
            else:
                service.retractDataset(versionName, True, 'Retracting dataset')

    except socket.error, e:
        raise ESGPublishError("Socket error: %s\nIs the proxy certificate %s valid?"%(`e`, service._cert_file))
    except RemoteCallException, e:
        fields = `e`.split('\n')
        if dset is not None:
            dset.warning("Deletion/retraction failed for dataset %s with message: %s"%(versionName, string.join(fields[0:2])), ERROR_LEVEL, PUBLISH_MODULE)
            event = Event(dset.name, dset.getVersion(), failureEvent)
        eventName = failureEvent
        stateName = 'UNSUCCESSFUL'
    else:
        if dset is not None:
            event = Event(dset.name, dset.getVersion(), successEvent)
        eventName = successEvent
        stateName = 'SUCCESSFUL'

    if dset is not None:
        dset.events.append(event)

    return eventName, stateName

DELETE = 1
UNPUBLISH = 2
NO_OPERATION = 3
UNINITIALIZED = 4
def deleteDatasetList(datasetNames, Session, gatewayOperation=UNPUBLISH, thredds=True, las=False, deleteInDatabase=False, progressCallback=None,
                      deleteAll=False, republish=False, reinitThredds=True, restInterface=False, pid_connector=None, project_config_section=None, data_node=None):
    """
    Delete or retract a list of datasets:

    - Delete the dataset from the gateway.
    - Remove the catalogs from the THREDDS catalog (optional).
    - Reinitialize the LAS server and THREDDS server.
    - Delete the database entry (optional).

    if republish is False:
      Returns a status dictionary: datasetName => status
    else
      Returns a tuple (status_dictionary, republishList), where republishList is a list of (dataset_name, version) tuples to be republished.

    datasetNames
      A list of )dataset_name, version) tuples.

    Session
      A database Session.

    gatewayOperation
      An enumeration. If:
      - publish.DELETE: Remove all metadata from the gateway database.
      - publish.UNPUBLISH: (Default) Remove metadata that allows dataset discovery from the gateway.
      - publish.NO_OPERATION: No gateway delete/retract operation is called.

    thredds
      Boolean flag: if true (the default), delete the associated THREDDS catalog and reinitialize server.

    las  
      Boolean flag: if true (the default), reinitialize server.

    deleteInDatabase
      Boolean flag: if true (default is False), delete the database entry.
    
    progressCallback
      Tuple (callback, initial, final) where ``callback`` is a function of the form ``callback(progress)``, ``initial`` is the initial value reported, ``final`` is the final value reported.

    deleteAll
      Boolean, if True delete all versions of the dataset(s).

    republish
      Boolean, if True return (statusDictionary, republishList), where republishList is a list of datasets to be republished.

    reinitThredds
      Boolean flag. If True, create the TDS master catalog and reinitialize the TDS server.

    restInterface
      Boolean flag. If True, publish datasets with the RESTful publication services.

    pid_connector
        esgfpid.Connector object to register PIDs

    project_config_section
        Name of the project config section in esg.ini (for user specific project configs)

    data_node
        String, the datanode to unpublish (only for unpublication from Solr)

    """
    if gatewayOperation == UNINITIALIZED:
        raise ESGPublishError("Need to set mandatory --delete|--retract|--skip-index argument!")

    if gatewayOperation not in (DELETE, UNPUBLISH, NO_OPERATION):
        raise ESGPublishError("Invalid gateway operation: %d"%gatewayOperation)
    deleteOnGateway = (gatewayOperation==DELETE)
    operation = (gatewayOperation!=NO_OPERATION)

    session = Session()
    resultDict = {}
    config = getConfig()

    # Check the dataset names and cache the results for the gateway, thredds, and database phases
    nameDict = {}
    for datasetName,version in datasetNames:
        isDataset, dset, versionObjs, isLatest = datasetOrVersionName(datasetName, version, session, deleteAll=deleteAll, restInterface=restInterface)
        if dset is None:
            warning("Dataset not found in node database: %s"%datasetName)
        nameDict[datasetName] = (isDataset, dset, versionObjs, isLatest)

    # Delete the dataset from the gateway.
    if operation:

        # Create the web service proxy
        threddsRootURL = config.get('DEFAULT', 'thredds_url')
        serviceCertfile = config.get('DEFAULT', 'hessian_service_certfile')
        serviceKeyfile = config.get('DEFAULT', 'hessian_service_keyfile')
        if not restInterface:
            serviceURL = getHessianServiceURL(project_config_section=project_config_section)
            servicePort = config.getint('DEFAULT','hessian_service_port')
            serviceDebug = config.getboolean('DEFAULT', 'hessian_service_debug')
            service = Hessian(serviceURL, servicePort, key_file=serviceKeyfile, cert_file=serviceCertfile, debug=serviceDebug)
        else:
            service_certs_location = getServiceCertsLoc()
            serviceURL = getRestServiceURL(project_config_section=project_config_section)
            serviceDebug = config.getboolean('DEFAULT', 'rest_service_debug', default=False)
            service = RestPublicationService(serviceURL, serviceCertfile, service_certs_location, keyFile=serviceKeyfile, debug=serviceDebug)

        for datasetName,version in datasetNames:
            if version > -1:
                datasetToUnpublish = '%s.v%s' % (datasetName, version)
            else:
                if service.service_type == 'REST':
                    error('Cannot unpublish multiple versions using REST. Please specify a single dataset version ("dataset_id#1"). Skipping %s' % datasetName)
                    continue
                datasetToUnpublish = datasetName
            isDataset, dset, versionObjs, isLatest = nameDict[datasetName]
            try:
                eventName, stateName = deleteGatewayDatasetVersion(datasetToUnpublish, gatewayOperation, service, session, dset=dset, data_node=data_node)
            except RemoteCallException, e:
                fields = `e`.split('\n')
                error("Deletion/retraction failed for dataset/version %s with message: %s"%(datasetToUnpublish, string.join(fields[0:2], '\n')))
                continue
            except ESGPublishError, e:
                fields = `e`.split('\n')
                error("Deletion/retraction failed for dataset/version %s with message: %s"%(datasetToUnpublish, string.join(fields[-2:], '\n')))
                continue
            info("  Result: %s"%stateName)
            resultDict[datasetName] = eventName

    # Reinitialize the LAS server.
    if las:
        result = reinitializeLAS()

    # Remove the catalogs from the THREDDS catalog (optional),
    # and reinitialize the THREDDS server.
    if thredds:
        threddsRoot = config.get('DEFAULT', 'thredds_root')
        for datasetName,version in datasetNames:
            isDataset, dset, versionObjs, isLatest = nameDict[datasetName]
            if dset is None:
                continue
            for versionObj in versionObjs:
                # send unpublication info to handle server
                if pid_connector:
                    pid_connector.unpublish_one_version(drs_id=datasetName, version_number=versionObj.version)
                catalog = session.query(Catalog).filter_by(dataset_name=dset.name, version=versionObj.version).first()
                if catalog is not None:
                    path = os.path.join(threddsRoot, catalog.location)
                    if os.path.exists(path):
                        info("Deleting THREDDS catalog: %s"%path)
                        os.unlink(path)
                        event = Event(dset.name, versionObj.version, DELETE_THREDDS_CATALOG_EVENT)
                        dset.events.append(event)
                    session.delete(catalog)

        session.commit()
        if reinitThredds:
            updateThreddsMasterCatalog(Session)
            result = reinitializeThredds()

    # Delete the database entry (optional).
    if republish:
        republishList = []
    if deleteInDatabase:
        for datasetName,version in datasetNames:
            isDataset, dset, versionObjs, isLatest = nameDict[datasetName]
            if dset is None:
                continue
            if isDataset:
                info("Deleting existing dataset: %s"%datasetName)
                event = Event(dset.name, dset.getVersion(), DELETE_DATASET_EVENT)
                dset.events.append(event)
                dset.deleteChildren(session)            # For efficiency
                session.delete(dset)
            else:
                if len(versionObjs)>0:
                    versionObj = versionObjs[0]

                    # If necessary, republish the most recent version after this one.
                    if isLatest and republish:
                        nextVersion = dset.versions[-2].version
                        republishList.append((datasetName, nextVersion))
                    info("Deleting existing dataset version: %s (version %d)"%(datasetName, versionObjs[0].version))
                    event = Event(dset.name, versionObj.version, DELETE_DATASET_EVENT)
                    dset.events.append(event)
                    session.delete(versionObj)
                    if isLatest:
                        dset.deleteVariables(session)
            session.commit()

    session.commit()
    session.close()

    if republish:
        return (resultDict, republishList)
    else:
        return resultDict
