import os
import socket
from time import sleep
from esgcet.model import *
from esgcet.config import getHandlerByName, getConfig
from thredds import generateThredds, generateThreddsOutputPath, updateThreddsMasterCatalog, reinitializeThredds
from las import generateLAS, generateLASOutputPath, updateLASMasterCatalog, reinitializeLAS
from hessianlib import Hessian
from esgcet.exceptions import *
from utility import issueCallback
from esgcet import messaging

class PublicationState(object):

    # Invalid state returned in status
    INVALID_STATE = 0

    # The job completed normally.
    SUCCESSFUL = 1

    # The job completed with errors and or exceptions (including
    # cancellation).
    UNSUCCESSFUL = 2

    # The job never started because the input was invalid (e.g. bogus URI).
    INVALID_INPUT = 3

    # The job is currently processing, and has not completed yet.
    PROCESSING = 4

    # The status of the job is unknown because there is no information on
    # the requested job.
    UNKNOWN = 5

    stateMap = {
        'SUCCESSFUL' : SUCCESSFUL,
        'UNSUCCESSFUL' : UNSUCCESSFUL,
        'INVALID_INPUT' : INVALID_INPUT,
        'PROCESSING' : PROCESSING,
        'UNKNOWN' : UNKNOWN,
        }

class PublicationStatus(object):

    def __init__(self, statusId=None, service=None):
        if service is not None:
            self.state = service.getPublishingStatus(statusId)
            self.message = service.getPublishingResult(statusId)
        else:
            self.state = ''
            self.message = ''

    def getState(self):
        return PublicationState.stateMap.get(self.getStateItem(), PublicationState.INVALID_STATE)

    def setState(self, state):
        self.state = state

    def getMessage(self):
        return self.message

    def setMessage(self, message):
        self.message = message

    def getStateItem(self):
        return self.state

def publishDataset(datasetName, parentId, service, threddsRootURL, session):
    """
    Publish a dataset.

    Returns (*dset*, *statusId*, *state*, *event_name*, *status*) where *dset* is the Dataset
    instance, *statusId* is the web service ID to poll for status, 
    *state* is the initial publication state, *event_name* is the
    associated event, such as ``esgcet.model.PUBLISH_DATASET_EVENT``,
    and *status* is the PublicationStatus instance.

    datasetName
      String dataset identifier.

    parentId
      String persistent identifier of the parent of this dataset. This defines the top-level
      of the hierarchy into which this dataset will be published.

    service
      Hessian proxy web service

    threddsRootURL
      Root THREDDS URL

    session
      A database Session **instance**.

    """
    
    # Lookup the dataset
    dset = session.query(Dataset).filter_by(name=datasetName).first()
    if dset is None:
        raise ESGPublishError("Dataset not found: %s"%datasetName)

    # Clear publication errors from dataset_status
    dset.clear_warnings(session, PUBLISH_MODULE)

    # Get the catalog associated with the dataset
    catalog = session.query(Catalog).filter_by(dataset_name=datasetName).first()
    if catalog is None:
        raise ESGPublishError("No THREDDS catalog found for dataset: %s"%datasetName)
    threddsURL = os.path.join(threddsRootURL, catalog.location)

    # Publish
    try:
        statusId = service.createDataset(parentId, threddsURL, -1, "Published", '', 'Version 1')
    except socket.error, e:
        raise ESGPublishError("Socket error: %s\nIs the proxy certificate %s valid?"%(`e`, service._cert_file))
    status = PublicationStatus(statusId, service)

    # Create the publishing event
    state = status.getState()
    if state==PublicationState.PROCESSING:
        event = Event(dset.name, dset.getVersion(), START_PUBLISH_DATASET_EVENT)
        dset.events.append(event) 
    elif state==PublicationState.SUCCESSFUL:
        event = Event(dset.name, dset.getVersion(), PUBLISH_DATASET_EVENT)
        dset.events.append(event)
    else:
        message = status.getMessage()
        if message[0:7]=='That ID':
            dset.warning("Publication failed for dataset %s with message: %s"%(datasetName, message), WARNING_LEVEL, PUBLISH_MODULE)
            event = Event(dset.name, dset.getVersion(), PUBLISH_STATUS_UNKNOWN_EVENT)
        else:
            dset.warning("Publication failed for dataset %s with message: %s"%(datasetName, message), ERROR_LEVEL, PUBLISH_MODULE)
            event = Event(dset.name, dset.getVersion(), PUBLISH_FAILED_EVENT)
        dset.events.append(event)

    # Save the status ID
    dset.status_id = statusId

    return dset, statusId, state, event.event, status

def publishDatasetList(datasetNames, Session, parentId=None, handlerDictionary=None, publish=True, thredds=True, las=False, progressCallback=None, service=None, perVariable=None):
    """
    Publish a list of datasets:

    - For each dataset, write a THREDDS catalog.
    - Add the new catalogs to the THREDDS catalog tree and reinitilize the THREDDS server.
    - Reinitialize the LAS server.
    - Publish each dataset to the gateway.

    Returns a dictionary: datasetName => status
    
    datasetNames
      A list of string dataset names.

    Session
      A database Session.

    parentId
      The string persistent identifier of the parent of the datasets. If None (the default),
      the parent id for each dataset is generated from ``handler.getParentId()``. This function
      can be overridden in the project handler to implement a project-specific dataset hierarchy.

    handlerDictionary
      A dictionary mapping dataset_name => handler.

    publish
      Boolean flag: if true (the default), contact the gateway to publish this dataset.

    thredds
      Boolean flag: if true (the default), write the associated THREDDS catalog.

    las
      Boolean flag: if true (the default), write the associated LAS catalog.

    progressCallback
      Tuple (callback, initial, final) where ``callback`` is a function of the form ``callback(progress)``, ``initial`` is the initial value reported, ``final`` is the final value reported.

    service
      String service name. If omitted, the first online/offline service in the configuration is used.

    perVariable
      Boolean, overrides ``variable_per_file'' config option.

    """

    session = Session()
    resultDict = {}

    # Get handlers for each dataset
    if handlerDictionary is None:
        handlers = {}
        for datasetName in datasetNames:
            dset = session.query(Dataset).filter_by(name=datasetName).first()
            if dset is None:
                raise ESGPublishError("Dataset not found: %s"%datasetName)
            handler = getHandlerByName(dset.project, None, Session)
            handlers[datasetName] = handler
    else:
        handlers = handlerDictionary

    if thredds:
        for datasetName in datasetNames:
            handler = handlers[datasetName]
            threddsOutputPath = generateThreddsOutputPath(datasetName, Session, handler)
            threddsOutput = open(threddsOutputPath, "w")
            generateThredds(datasetName, Session, threddsOutput, handler, service=service, perVariable=perVariable)
            threddsOutput.close()
            try:
                os.chmod(threddsOutputPath, 0664)
            except:
                pass

        updateThreddsMasterCatalog(Session)
        result = reinitializeThredds()

    if las:    
##         for datasetName in datasetNames:
##             handler = handlers[datasetName]
##             lasOutputPath = generateLASOutputPath(datasetName, Session, handler)
##             lasOutput = open(lasOutputPath, "w")
##             generateLAS(datasetName, Session, lasOutput, handler)
##             lasOutput.close()
##             try:
##                 os.chmod(lasOutputPath, 0664)
##             except:
##                 pass

##         updateLASMasterCatalog(Session)
        try:
            result = reinitializeLAS()
        except Exception, e:
            messaging.error("Error on LAS reinitialization: %s, new datasets not added."%e)

    if publish:

        # Create the web service proxy
        config = getConfig()
        serviceURL = config.get('DEFAULT', 'hessian_service_url')
        servicePort = config.getint('DEFAULT','hessian_service_port')
        serviceDebug = config.getboolean('DEFAULT', 'hessian_service_debug')
        serviceCertfile = config.get('DEFAULT', 'hessian_service_certfile')
        serviceKeyfile = config.get('DEFAULT', 'hessian_service_keyfile')
        servicePollingDelay = config.getint('DEFAULT','hessian_service_polling_delay')
        spi = servicePollingIterations = config.getint('DEFAULT','hessian_service_polling_iterations')
        threddsRootURL = config.get('DEFAULT', 'thredds_url')
        service = Hessian(serviceURL, servicePort, key_file=serviceKeyfile, cert_file=serviceCertfile, debug=serviceDebug)

        results = []
        lenresults = len(datasetNames)
        n = spi * lenresults
        j = 0
        for datasetName in datasetNames:
            if parentId is None:
                parentIdent = handler.getParentId(datasetName)
            else:
                parentIdent = parentId
            messaging.info("Publishing: %s, parent = %s"%(datasetName, parentIdent))
            dset, statusId, state, evname, status = publishDataset(datasetName, parentIdent, service, threddsRootURL, session)
            messaging.info("  Result: %s"%status.getStateItem())
            results.append((dset, statusId, state))
            resultDict[datasetName] = evname

            # Poll each dataset again
            j += 1
            if state not in (PublicationState.PROCESSING, PublicationState.SUCCESSFUL):
                issueCallback(progressCallback, j*spi, n, 0, 1)
                continue

            for i in range(spi):
                if state==PublicationState.SUCCESSFUL:
                    evname = PUBLISH_DATASET_EVENT
                    event = Event(dset.name, dset.getVersion(), evname)
                    dset.events.append(event)
                    resultDict[dset.name] = evname
                    issueCallback(progressCallback, j*spi, n, 0, 1)
                    break
                elif state==PublicationState.PROCESSING:
                    sleep(float(servicePollingDelay))
                    status = PublicationStatus(statusId, service)
                    messaging.info("  Result: %s"%status.getStateItem())
                    state = status.getState()
                    issueCallback(progressCallback, (j-1)*spi+i+1, n, 0, 1)
                else:
                    evname = PUBLISH_FAILED_EVENT
                    message = status.getMessage()
                    dset.warning("Publication failed for dataset %s with message: %s"%(datasetName, message), ERROR_LEVEL, PUBLISH_MODULE)
                    event = Event(dset.name, dset.getVersion(), evname)
                    dset.events.append(event)
                    resultDict[dset.name] = evname
                    issueCallback(progressCallback, j*spi, n, 0, 1)
                    break

    session.commit()
    session.close()

    return resultDict

def pollDatasetPublicationStatus(datasetName, Session, service=None):
    """
    Get the current dataset publication status by polling the gateway.

    Returns the current dataset publication status.
    
    datasetNames
      A list of string dataset names.

    Session
      A database Session.

    service
      Web service proxy instance. If None, the service is created.

    """

    session = Session()
    dset = session.query(Dataset).filter_by(name=datasetName).first()
    if dset is None:
        messaging.error("Dataset not found: %s"%datasetName)
        session.close()
        return PUBLISH_FAILED_EVENT
    
    status = dset.get_publication_status()
    if status!=START_PUBLISH_DATASET_EVENT:
        session.close()
        return status

    if service is None:
        config = getConfig()
        serviceURL = config.get('DEFAULT', 'hessian_service_url')
        servicePort = config.getint('DEFAULT','hessian_service_port')
        serviceDebug = config.getboolean('DEFAULT', 'hessian_service_debug')
        serviceCertfile = config.get('DEFAULT', 'hessian_service_certfile')
        serviceKeyfile = config.get('DEFAULT', 'hessian_service_keyfile')
        service = Hessian(serviceURL, servicePort, key_file=serviceKeyfile, cert_file=serviceCertfile, debug=serviceDebug)
    
    try:
        statusObj = PublicationStatus(dset.status_id, service)
    except socket.error, e:
        raise ESGPublishError("Socket error: %s\nIs the proxy certificate %s valid?"%(`e`, service._cert_file))

    # Clear publication errors from dataset_status
    dset.clear_warnings(session, PUBLISH_MODULE)

    pubState = statusObj.getState()
    if pubState==PublicationState.SUCCESSFUL:
        status = PUBLISH_DATASET_EVENT
        event = Event(dset.name, dset.getVersion(), status)
        dset.events.append(event)
    elif pubState!=PublicationState.PROCESSING:
        message = statusObj.getMessage()
        if message[0:7]=='That ID':
            dset.warning("Publication failed for dataset %s with message: %s"%(datasetName, message), WARNING_LEVEL, PUBLISH_MODULE)
            status = PUBLISH_STATUS_UNKNOWN_EVENT
        else:
            dset.warning("Publication failed for dataset %s with message: %s"%(datasetName, message), ERROR_LEVEL, PUBLISH_MODULE)
            status = PUBLISH_FAILED_EVENT
        event = Event(dset.name, dset.getVersion(), status)
        dset.events.append(event)

    session.commit()
    session.close()
    return status
