import requests

class publisherClient(object):

    def __init__(self, cert_fn, hostname, verbose=False):

        self.certFile = cert_fn
        self.keyFile = cert_fn

        urlbase = 'https://{}/esg-search/ws'.format(hostname)

        self.retractUrl = '{}/retract'.format(urlbase)
        self.updateUrl = '{}/update'.format(urlbase)
        self.publishUrl = '{}/publish'.format(urlbase)
        self.deleteUrl = '{}/delete'.format(urlbase)
        self.verbose = verbose

    def post_data(self, url, data):
        resp =  requests.post(url, data=data, cert=(self.certFile, self.keyFile), \
verify=False, allow_redirects=True)
        if self.verbose:
            print(resp.text)
        return resp

    def publish(self, xmldata):

        try:
            response = self.post_data(self.publishUrl, xmldata)
        except requests.exceptions.SSLError as e:
            print("SSL error!", e )
        except Exception as e:
            print("Some other error!", e )
        print(response.text)

    def update(self, xmldata):

        try:
            response = self.post_data(self.updateUrl, xmldata)

        except requests.exceptions.SSLError as e:
            print("SSL error!", e )
        except Exception as e:
            print("Some other error!", e )
        print(response.text)

    def retract(self, object_id):
        data = { 'id' : object_id }

        try:
            response = self.post_data(self.retractUrl, data)
        except requests.exceptions.SSLError as e:
            print("SSL error!", e )
        except Exception as e:
            print("Some other error!", e )
        # root = etree.fromstring(response.content)
        # text = root[0].text
        # return (response.status_code, text)
        print(response.text)

    def delete(self, object_id):
        
        data = { 'id' : object_id }

        print (data)
        try:
            response = self.post_data(self.deleteUrl, data)
        except requests.exceptions.SSLError as e:
            print("SSL error!", e )
        except Exception as e:
            print("Some other error!", e )
        print(response.text)
