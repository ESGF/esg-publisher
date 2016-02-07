"""
Wrapper for urllib2.urlopen, which handles looking up a local copy of 
host keys for self-signed certificates.
"""

import os
import urllib2
import urlparse


HTTPError = urllib2.HTTPError

def urlopen(url, conf, **kwargs):

    found_host_cert = False
    if conf:
        hostname = urlparse.urlparse(url).netloc

        host_certs_dir = conf.get('host_certs_dir')
        host_certs_file = os.path.join(host_certs_dir,
                                       "%s.pem" % hostname)

        if os.path.exists(host_certs_file):
            kwargs['cafile'] = host_certs_file
            found_host_cert = True

    try:
        fh = urllib2.urlopen(url, **kwargs)
    except urllib2.URLError as e:
        if "CERTIFICATE_VERIFY_FAILED" in str(e) and not found_host_cert:
            print """
(In utils/urlopen.py): 
  SSL certificate verify failed for URL %s.
  Maybe self-signed?
  Consider copying hostcert.pem to %s 
  in order to use as trusted certificate.
""" % (url, host_certs_file)
            raise
    
    return fh
