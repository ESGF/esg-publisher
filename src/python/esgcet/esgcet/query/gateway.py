from esgcet.config import getConfig
from esgcet.publish import Hessian, RemoteCallException
from lxml import etree
from esgcet.exceptions import *

def getRemoteMetadataService():
    """Get the remote metadata service.

    Returns the service object.
    """
    config = getConfig()
    remoteMetadataServiceUrl = config.get('DEFAULT', 'hessian_service_remote_metadata_url')
    service = Hessian(remoteMetadataServiceUrl, 80)
    return service

def getGatewayDatasetFields():
    """Get the fields associated with a gateway dataset.

    Returns a list of string field names.
    """
    return ['id', 'state', 'name']

def getGatewayDatasetMetadata(datasetName):
    """Get metadata associated with a dataset, from the gateway.

    Returns a tuple of dataset fields.

    datasetName
      The name of the dataset.
    """
    service = getRemoteMetadataService()
    try:
        metadata = service.getDatasetMetadata(datasetName);
    except RemoteCallException, e:
        line0 = `e`.split('\n')[0]
        if line0.find('None')!=-1:
            raise ESGQueryError("Dataset not found: %s"%datasetName)
        else:
            raise
    esgElem = etree.fromstring(metadata)
    datasetElem = esgElem[0]
    result = tuple([datasetElem.get(field) for field in getGatewayDatasetFields()])
    return result
    
def getGatewayDatasetChildren(datasetName, sort=True):
    """Get the child dataset ids contained in a dataset, from the gateway.

    Returns a list of string identifiers of the child datasets.

    datasetName
      The name of the parent dataset.

    sort
      Boolean, sort the result if True.
    """
    service = getRemoteMetadataService()
    try:
        metadata = service.getDatasetHierarchy(datasetName)
    except RemoteCallException, e:
        line0 = `e`.split('\n')[0]
        if line0.find('None')!=-1:
            raise ESGQueryError("Dataset not found: %s"%datasetName)
        else:
            raise
    hierarchy = etree.fromstring(metadata)
    dataset = hierarchy[0]
    result = [child.get("id") for child in dataset]
    if sort:
        result.sort()
    return result

def getGatewayExperiments():
    """Get metadata associated with all experiments, from the gateway.

    Returns headers, experiment_tuples where:
      - header is the list of field names
      - tuples is a list of tuples, each tuple with the same length as header
    """
    service = getRemoteMetadataService()
    exps = service.listExperiments()
    expelem = etree.fromstring(exps)
    header = ['name', 'description']
    result = [(child.get("name"), child[0].text) for child in expelem]
    return header, result

