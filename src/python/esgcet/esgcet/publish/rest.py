import requests
from lxml import etree
from urlparse import urljoin
from esgcet.exceptions import *
import os

DEFAULT_CERTS_BUNDLE = '/etc/certs/esgf-ca-bundle.crt'

from esgcet.config import getConfig

class RestPublicationService(object):

    def __init__(self, url, certFile, certs_location, keyFile=None, debug=False):
        """

        Create a RESTful ESGF Publication Service proxy. The proxy
        supports both the current and legacy publication services.

        The current API is defined at:
        http://esgf.org/wiki/ESGF_Publishing_Services

        See http://esgf.org/esg-search-site/LegacyPublishingService.html
        for definition of the legacy API.

        url
          Publication service URL. For example, 'https://pcmdi9.llnl.gov/esg-search/ws/'.
          Note that the actual service operation will be appended to the URL.

        certFile
          Client certificate file in PEM format, for client cert authentication.

        keyfile
          Client key file, if different from certFile.

        debug:
          Boolean flag. If True, write debugging information.
        """

        self.service_type = 'REST'
        self.url = url
        if self.url[-1] != '/':
            self.url += '/'
        self.harvestUrl = urljoin(self.url, 'harvest')
        self.deleteUrl = urljoin(self.url, 'delete')
        self.retractUrl = urljoin(self.url, 'retract')

        self.certFile = certFile
        if keyFile is not None:
            self.keyFile = keyFile
        else:
            self.keyFile = certFile
        outdir=os.path.dirname(certFile)
        concat_certs=outdir+'/concatenatedcerts'

        # need to concatenate the certs bundle to the cert to use as the CA context.  Thanks pchengi for the initial fix!
        # check if there is a setting, if none, use a default

        config = getConfig()
        certs_bundle_location = DEFAULT_CERTS_BUNDLE
        try:
            certs_bundle_location = config.get('DEFAULT', 'esg_certificates_bundle')
        except:
            certs_bundle_location = DEFAULT_CERTS_BUNDLE
        

        files=[certFile,certs_bundle_location]
        with open(concat_certs,'w') as outfile:
            for certf in files:
                with open(certf, 'r') as file:
                    outfile.write(file.read())
                    outfile.write('\n')
        self.certs_location = concat_certs
        self.debug = debug
        self.status = 0
        self.message = ''

    def createDataset(self, parentId, threddsURL, resursionLevel, status, schema=None):
        """
        Legacy dataset creation.

        Return 'SUCCESSFUL' if the operation succeeded.

        parentId
          String parent dataset identifier (ignored).

        threddsURL
          String URL of the THREDDS catalog to be harvested.

        resursionLevel
          Integer depth of the catalog (ignored).

        status
          String status (ignored).

        schema
          (Optional) String name of schema to validate against. Example: 'cmip5'.

        """
        status, message = self.harvest(threddsURL, 'THREDDS', schema=schema)
        if status==200:
            result = 'SUCCESSFUL'
        else:
            result = 'UNSUCCESSFUL'
        self.status = status
        self.message = message
        return result

    def deleteDataset(self, datasetId, recursive, message):
        """
        Legacy dataset deletion.

        This method does not return a value.

        datasetId
          String identifier of dataset to delete.

        recursive
          Boolean recursion flag (ignored since datasets are single-depth only.)

        message:
          String message (ignored).

        """
        status, message = self.delete(datasetId)
        if status==200:
            result = 'SUCCESSFUL'
        else:
            result = 'UNSUCCESSFUL'
        self.status = status
        self.message = message
        return result

    def retractDataset(self, datasetId, recursive, message):
        """
        Legacy dataset retraction.

        This method does not return a value.

        datasetId
          String identifier of dataset to delete.

        recursive
          Boolean recursion flag (ignored since datasets are single-depth only.)

        message:
          String message (ignored).

        """
        status, message = self.retract(datasetId)
        if status == 200:
            result = 'SUCCESSFUL'
        else:
            result = 'UNSUCCESSFUL'
        self.status = status
        self.message = message
        return result

    def getPublishingStatus(self, operationHandle):
        """
        Get the status of publication.

        Return the string 'SUCCESSFUL'.

        operationHandle
          String operation handle (ignored).
        """
        if self.status==200:
            result = 'SUCCESSFUL'
        else:
            result = 'UNSUCCESSFUL'
        return result

    def getPublishingResult(self, operationHandle):
        """
        Get the string message result of publication.

        Return the string 'SUCCESSFUL'.

        operationHandle
          String operation handle (ignored).
        """
        return "Status=%d, %s"%(self.status, self.message)

    def harvest(self, uri, metadataRepositoryType, schema=None):
        """
        Request the server to harvest metadata from a repository.

        Returns a tuple of strings: (status_code, error_message).

        uri
          Address of remote metadata catalog or repository.

        metadataRepositoryType
          String repository type. For example, 'THREDDS'.

        schema
          Optional URI of a schema for record validation. For example, 'cmip5'.
        """
        params = {
            'uri' : uri,
            'metadataRepositoryType' : metadataRepositoryType
            }
        if schema is not None:
            params['schema'] = schema

        try:
            response = requests.post(self.harvestUrl, params=params, cert=(self.certFile, self.keyFile), verify=self.certs_location, allow_redirects=True)
        except requests.exceptions.SSLError, e:
            raise ESGPublishError("Socket error: %s\nIs the proxy certificate %s valid?"%(`e`, self.certFile))

        root = etree.fromstring(response.content)
        text = root[0].text
        return (response.status_code, text)

    def delete(self, object_id):
        """
        Delete an object (dataset, file, aggregation) from the SOLR metadata store.

        Returns a tuple of strings: (status_code, error_message).

        object_id
          String identifier of the object. For example,
          'obs4MIPs.NASA-JPL.AIRS.mon.v1|esg-datanode.jpl.nasa.gov'
        """
        data = {
            'id' : object_id
            }

        try:
            response = requests.post(self.deleteUrl, data=data, cert=(self.certFile, self.keyFile), verify=self.certs_location, allow_redirects=True)
        except requests.exceptions.SSLError, e:
            raise ESGPublishError("Socket error: %s\nIs the proxy certificate %s valid?"%(`e`, self.certFile))

        root = etree.fromstring(response.content)
        text = root[0].text
        return (response.status_code, text)
        
    def retract(self, object_id):
        """
        Retract an object (dataset, file, aggregation) from the SOLR metadata store.

        Returns a tuple of strings: (status_code, error_message).

        object_id
          String identifier of the object. For example,
          'obs4MIPs.NASA-JPL.AIRS.mon.v1|esg-datanode.jpl.nasa.gov'
        """
        data = {
            'id' : object_id
            }

        try:
            response = requests.post(self.retractUrl, data=data, cert=(self.certFile, self.keyFile), verify=self.certs_location, allow_redirects=True)
        except requests.exceptions.SSLError, e:
            raise ESGPublishError("Socket error: %s\nIs the proxy certificate %s valid?"%(`e`, self.certFile))

        root = etree.fromstring(response.content)
        text = root[0].text
        return (response.status_code, text)
