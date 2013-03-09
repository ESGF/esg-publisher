from esgcet.config import getConfig
from esgcet.publish import Hessian, RemoteCallException
from lxml import etree
from esgcet.exceptions import *

def getRemoteMetadataService(serviceUrl=None):
    """Get the remote metadata service.

    Returns the service object.
    """
    config = getConfig()
    if serviceUrl is None:
        remoteMetadataServiceUrl = config.get('DEFAULT', 'hessian_service_remote_metadata_url')
    else:
        remoteMetadataServiceUrl = serviceUrl
    serviceDebug = config.getboolean('DEFAULT', 'hessian_service_debug')
    service = Hessian(remoteMetadataServiceUrl, 80, debug=serviceDebug)
    return service

def getGatewayDatasetFields():
    """Get the fields associated with a gateway dataset.

    Returns a list of string field names.
    """
    return ['id', 'state', 'name', 'source_catalog_uri']

def getGatewayDatasetMetadata(datasetName, serviceUrl=None):
    """Get metadata associated with a dataset, from the gateway.

    Returns a tuple of dataset fields.

    datasetName
      The name of the dataset.
    """
    service = getRemoteMetadataService(serviceUrl=serviceUrl)
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
    
def getGatewayDatasetChildren(datasetName, sort=True, serviceUrl=None):
    """Get the child dataset ids contained in a dataset, from the gateway.

    Returns a list of string identifiers of the child datasets.

    datasetName
      The name of the parent dataset.

    sort
      Boolean, sort the result if True.
    """
    service = getRemoteMetadataService(serviceUrl=serviceUrl)
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

def getGatewayExperiments(serviceUrl=None):
    """Get metadata associated with all experiments, from the gateway.

    Returns headers, experiment_tuples where:
      - header is the list of field names
      - tuples is a list of tuples, each tuple with the same length as header
    """
    service = getRemoteMetadataService(serviceUrl=serviceUrl)
    exps = service.listExperiments()

    """Note: expelem is something like:

    <esg:ESG xmlns:esg="http://www.earthsystemgrid.org/">
      <esg:experiment name="IPCC AR4 1pct_to2x">
        <esg:description>One percent/year CO2 increase to doubling</esg:description>
      </esg:experiment>
      <esg:experiment name="amip"/>
    </esg:ESG>


    The experiment has an optional child element 'description'.
    """
    
    expelem = etree.fromstring(exps)
    header = ['name', 'description']
    result = []
    for child in expelem:
        name = child.get("name")
        if len(child)>0:
            description = child[0].text
        else:
            description = ""
        result.append((name, description))
    return header, result

def getGatewayDatasetFiles(datasetName, serviceUrl=None):
    """Get the files contained in a dataset, from the gateway.
    
    Returns headers, file_tuples where:
      - header is the list of field names
      - file_tuples is a list of tuples, each tuple with the same length as header

    datasetName
      The name of the parent dataset.

    """
    service = getRemoteMetadataService(serviceUrl=serviceUrl)
    filesXML = service.getDatasetFiles(datasetName)
    filesElem = etree.fromstring(filesXML)
    header = ['name', 'id', 'size']
    result = []
    for file in filesElem.iter("{http://www.earthsystemgrid.org/}file"):
        result.append((file.get("name"), file.get("id"), file.get("size")))
    return header, result

def getGatewayDatasetAccessPoints(datasetName, serviceUrl=None):
    """Get the file access points of files contained in a dataset, from the gateway.
    
    Returns headers, url_tuples where:
      - header is the list of field names
      - url_tuples is a list of tuples, each tuple with the same length as header

    datasetName
      The name of the parent dataset.

    """
    service = getRemoteMetadataService(serviceUrl=serviceUrl)
    filesXML = service.getDatasetFiles(datasetName)
    filesElem = etree.fromstring(filesXML)

    capabilityDict = {}
    for capability in filesElem.iter("{http://www.earthsystemgrid.org/}data_access_capability"):
        capabilityDict[capability.get("name")] = (capability.get("type"), capability.get("base_uri"))

    header = ['name', 'id', 'size', 'capability', 'url', 'checksum', 'algorithm']
    result = []
    for file in filesElem.iter("{http://www.earthsystemgrid.org/}file"):
        for checksumElem in file.iter("{http://www.earthsystemgrid.org/}checksum"):
            checksum = checksumElem.get("value")
            algorithm = checksumElem.get("algorithm")
            break
        else:
            checksum = ''
            algorithm = ''
        for fileAccessPoint in file.iter("{http://www.earthsystemgrid.org/}file_access_point"):
            capabilityName = fileAccessPoint.get("data_access_capability")
            uri = fileAccessPoint.get("uri")
            capabilityType, baseUri = capabilityDict[capabilityName]
            url = baseUri+uri
            result.append((file.get("name"), file.get("id"), file.get("size"), capabilityType, url, checksum, algorithm))
    return header, result
