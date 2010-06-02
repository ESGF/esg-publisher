import os
import socket
import string
from esgcet.model import *
from esgcet.config import getConfig
from hessianlib import Hessian, RemoteCallException
from publish import PublicationState, PublicationStatus
from time import sleep
from thredds import updateThreddsMasterCatalog, reinitializeThredds
from las import updateLASMasterCatalog, reinitializeLAS
from utility import issueCallback
from esgcet.messaging import debug, info, warning, error, critical, exception

def retractDataset(datasetName, service, session):

    """
    Retract a dataset. This leaves certain metadata on the gateway database, but reduces the visibility
    of the dataset at the gateway portal.

    Returns (*event_name*, *state_name*) where *dset* is the Dataset
    instance, *statusId* is the web service ID to poll for status, 
    *state* is the initial publication state, *event_name* is the
    associated event, such as ``esgcet.model.UNPUBLISH_GATEWAY_DATASET_EVENT``,
    and *status* is the associated PublicationStatus instance.

    datasetName
      String dataset identifier.

    service
      Hessian proxy web service

    session
      A database Session **instance**.

    """
    
    # Lookup the dataset
    dset = session.query(Dataset).filter_by(name=datasetName).first()
    if dset is None:
        raise ESGPublishError("Dataset not found: %s"%datasetName)

    # Clear publication errors from dataset_status
    dset.clear_warnings(session, PUBLISH_MODULE)

    # Delete
    try:
        service.retractDataset(datasetName, 'Retracting dataset')
    except socket.error, e:
        raise ESGPublishError("Socket error: %s\nIs the proxy certificate %s valid?"%(`e`, service._cert_file))
    except RemoteCallException, e:
        fields = `e`.split('\n')
        dset.warning("Retraction failed for dataset %s with message: %s"%(datasetName, string.join(fields[0:2])), ERROR_LEVEL, PUBLISH_MODULE)
        event = Event(dset.name, dset.getVersion(), UNPUBLISH_DATASET_FAILED_EVENT)
        stateName = 'UNSUCCESSFUL'
    else:
        event = Event(dset.name, dset.getVersion(), UNPUBLISH_GATEWAY_DATASET_EVENT)
        stateName = 'SUCCESSFUL'

    dset.events.append(event)

    return event.event, stateName

def deleteDataset(datasetName, service, session):
    """
    Delete a dataset from the gateway.

    Returns (*event_name*, *state_name*) where *event_name* is the
    associated event, such as ``esgcet.model.DELETE_GATEWAY_DATASET_EVENT``,
    and *state_name* is 'SUCCESSFUL' or 'UNSUCCESSFUL'

    datasetName
      String dataset identifier.

    service
      Hessian proxy web service

    session
      A database Session **instance**.

    """
    
    # Lookup the dataset
    dset = session.query(Dataset).filter_by(name=datasetName).first()
    if dset is not None:

        # Clear publication errors from dataset_status
        dset.clear_warnings(session, PUBLISH_MODULE)

        # Delete
        try:
            service.deleteDataset(datasetName, True, 'Deleting dataset')
        except socket.error, e:
            raise ESGPublishError("Socket error: %s\nIs the proxy certificate %s valid?"%(`e`, service._cert_file))
        except RemoteCallException, e:
            fields = `e`.split('\n')
            dset.warning("Deletion failed for dataset %s with message: %s"%(datasetName, string.join(fields[0:2])), ERROR_LEVEL, PUBLISH_MODULE)
            event = Event(dset.name, dset.getVersion(), DELETE_DATASET_FAILED_EVENT)
            stateName = 'UNSUCCESSFUL'
        else:
            event = Event(dset.name, dset.getVersion(), DELETE_GATEWAY_DATASET_EVENT)
            stateName = 'SUCCESSFUL'

        dset.events.append(event)

        return event.event, stateName

    else:                               # Try to delete on the gateway only
        warning("Dataset not found in data node database: %s"%datasetName)
        
        # Delete
        try:
            service.deleteDataset(datasetName, True, 'Deleting dataset')
        except socket.error, e:
            raise ESGPublishError("Socket error: %s\nIs the proxy certificate %s valid?"%(`e`, service._cert_file))
        except RemoteCallException, e:
            fields = `e`.split('\n')
            warning("Deletion failed for dataset %s with message: %s"%(datasetName, string.join(fields[0:2])), ERROR_LEVEL, PUBLISH_MODULE)
            stateName = 'UNSUCCESSFUL'
        else:
            stateName = 'SUCCESSFUL'

        return DELETE_GATEWAY_DATASET_EVENT, stateName

DELETE = 1
UNPUBLISH = 2
NO_OPERATION = 3
def deleteDatasetList(datasetNames, Session, gatewayOperation=UNPUBLISH, thredds=True, las=False, deleteInDatabase=False, progressCallback=None):
    """
    Delete or retract a list of datasets:

    - Delete the dataset from the gateway.
    - Remove the catalogs from the THREDDS catalog (optional).
    - Reinitialize the LAS server and THREDDS server.
    - Delete the database entry (optional).

    Returns a dictionary: datasetName => status

    datasetNames
      A list of string dataset names.

    Session
      A database Session.

    gatewayOperation
      An enumeration. If:
      - publish.DELETE: Remove all metadata from the gateway database.
      - publish.UNPUBLISH: (Defauult) Remove metadata that allows dataset discovery from the gateway.
      - publish.NO_OPERATION: No gateway delete/retract operation is called.

    thredds
      Boolean flag: if true (the default), delete the associated THREDDS catalog and reinitialize server.

    las  
      Boolean flag: if true (the default), reinitialize server.

    deleteInDatabase
      Boolean flag: if true (default is False), delete the database entry.
    
    progressCallback
      Tuple (callback, initial, final) where ``callback`` is a function of the form ``callback(progress)``, ``initial`` is the initial value reported, ``final`` is the final value reported.

    """

    if gatewayOperation not in (DELETE, UNPUBLISH, NO_OPERATION):
        raise ESGPublishError("Invalid gateway operation: %d"%gatewayOperation)
    deleteOnGateway = (gatewayOperation==DELETE)
    operation = (gatewayOperation!=NO_OPERATION)

    session = Session()
    resultDict = {}
    config = getConfig()

    # Delete the dataset from the gateway.
    if operation:

        # Create the web service proxy
        serviceURL = config.get('DEFAULT', 'hessian_service_url')
        servicePort = config.getint('DEFAULT','hessian_service_port')
        serviceDebug = config.getboolean('DEFAULT', 'hessian_service_debug')
        serviceCertfile = config.get('DEFAULT', 'hessian_service_certfile')
        serviceKeyfile = config.get('DEFAULT', 'hessian_service_keyfile')
        servicePollingDelay = config.getint('DEFAULT','hessian_service_polling_delay')
        spi = servicePollingIterations = config.getint('DEFAULT','hessian_service_polling_iterations')
        threddsRootURL = config.get('DEFAULT', 'thredds_url')
        service = Hessian(serviceURL, servicePort, key_file=serviceKeyfile, cert_file=serviceCertfile, debug=serviceDebug)

        for datasetName in datasetNames:
            try:
                if deleteOnGateway:
                    info("Deleting: %s"%datasetName)
                    eventName, stateName = deleteDataset(datasetName, service, session)
                else:
                    info("Retracting: %s"%datasetName)
                    eventName, stateName = retractDataset(datasetName, service, session)
            except RemoteCallException, e:
                fields = `e`.split('\n')
                error("Deletion/retraction failed for dataset %s with message: %s"%(datasetName, string.join(fields[0:2], '\n')))
                continue
            except ESGPublishError, e:
                fields = `e`.split('\n')
                error("Deletion/retraction failed for dataset %s with message: %s"%(datasetName, string.join(fields[-2:], '\n')))
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
        for datasetName in datasetNames:
            catalog = session.query(Catalog).filter_by(dataset_name=datasetName).first()
            if catalog is not None:
                path = os.path.join(threddsRoot, catalog.location)
                if os.path.exists(path):
                    info("Deleting THREDDS catalog: %s"%path)
                    os.unlink(path)
                session.delete(catalog)

        session.commit()
        updateThreddsMasterCatalog(Session)
        result = reinitializeThredds()

    # Delete the database entry (optional).
    if deleteInDatabase:
        for datasetName in datasetNames:
            dset = session.query(Dataset).filter_by(name=datasetName).first()
            if dset is not None:
                info("Deleting existing dataset: %s"%datasetName)
                event = Event(dset.name, dset.getVersion(), DELETE_DATASET_EVENT)
                dset.events.append(event)
                dset.deleteChildren(session)            # For efficiency
                session.delete(dset)
            else:
                info("Database entry not found for: %s"%datasetName)
        
    session.commit()
    session.close()

    return resultDict
