import requests
import esgcet.logger as logger

log = logger.Logger()
publog = log.return_logger('Publisher Client')

class publisherClient(object):
    """  REST API wrapper for the esg-seach/ws APIs
        User must supply API parameters in xml form for publish and updates, dataset_ids for retract/delete
    """
    
    def __init__(self, cert_fn, hostname, verify=False, verbose=False, silent=False, auth=True):
        """ cert_fn - Path to certificate file
            hostame - target index node for API
            verbose, silent (bool) - add additional output, suppress INFO messages
        """ 
        self.certFile = cert_fn
        self.keyFile = cert_fn

        urlbase = 'https://{}/esg-search/ws'.format(hostname)

        self.retractUrl = '{}/retract'.format(urlbase)
        self.updateUrl = '{}/update'.format(urlbase)
        self.publishUrl = '{}/publish'.format(urlbase)
        self.deleteUrl = '{}/delete'.format(urlbase)
        self.verbose = verbose
        self.silent = silent
        self.verify = verify
        self.use_cert = auth

    def post_data(self, url, data):
        """ Internal method to post data to a url via requests
            url - the url
            data - the post data payload
        """
        if self.use_cert:
            resp = requests.post(url, data=data, cert=(self.certFile, self.keyFile), verify=self.verify, allow_redirects=True)
        else:
            resp = requests.post(url, data=data, verify=self.verify, allow_redirects=True)
        if not self.silent:
            publog.info(resp.text)
        if resp.status_code != 200:
            publog.error("code = {}".format(resp.status_code))
            exit(-1 * resp.status_code)
        return resp
    
    def publish(self, xmldata):
        """  Invoke the publish API call
            xmldata - xml publication record to post
        """
        try:
            response = self.post_data(self.publishUrl, xmldata)
        except requests.exceptions.SSLError as e:
            publog.exception("SSL error!")
        except Exception as e:
            publog.exception("Some other error!")

    def update(self, xmldata):
        """  Invoke the update API call
            xmldata - xml update record to post
        """

        try:
            response = self.post_data(self.updateUrl, xmldata)

        except requests.exceptions.SSLError as e:
            publog.exception("SSL error!")
        except Exception as e:
            publog.exception("Some other error!")

    def retract(self, object_id):
        """  Invoke the retract API call
            object_id - name of dataset id to retract in master_id.version|data_node form. 
        """
        
        data = { 'id' : object_id }
        if self.verbose:
            publog.info(data)

        try:
            response = self.post_data(self.retractUrl, data)
        except requests.exceptions.SSLError as e:
            publog.exception("SSL error!")
        except Exception as e:
            publog.exception("Some other error!")
        # root = etree.fromstring(response.content)
        # text = root[0].text
        # return (response.status_code, text)

    def delete(self, object_id):
        """  Invoke the delete API call
            object_id - name of dataset id to delete in master_id.version|data_node form. 
        """

        data = { 'id' : object_id }
        if self.verbose:
            publog.info(data)
        try:
            response = self.post_data(self.deleteUrl, data)
        except requests.exceptions.SSLError as e:
            publog.exception("SSL error!")
        except Exception as e:
            publog.exception("Some other error!")
