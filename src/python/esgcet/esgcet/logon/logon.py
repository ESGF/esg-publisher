import os
import socket
import logging
import OpenSSL
import getpass
from esgcet.exceptions import *
from esgcet.messaging import debug, info, warning, error, critical, exception


def check_server(host, port):
    """
    Check whether a server is up and running.

    :param str host: The hostname of the server
    :param int port: The port to check
    :returns: True iff something is running on the given host and port
    :rtype: *boolean*

    """
    args = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
    for family, socktype, proto, canonname, sockaddr in args:
        s = socket.socket(family, socktype, proto)
        try:
            s.connect(sockaddr)
        except socket.error:
            return False
        else:
            s.close()
            return True


def check_cert(config, user=None):
    """
    Check whether a myproxy certificate exists and has not been expired.

    :param config config: Configuration instance, e.g. from getConfig()
    :returns: True iff the certificate exists and has not been expired, otherwise returns False
    :rtype: *boolean*

    """
    myproxy_cert_location = config.get('DEFAULT', 'hessian_service_certfile')

    if not os.path.exists(myproxy_cert_location):
        return False
    else:
        with open(myproxy_cert_location) as c:
            cert = OpenSSL.crypto.load_certificate(OpenSSL.SSL.FILETYPE_PEM, c.read())
        if user:
            if user not in str(cert.get_subject()):
                return False
        if cert.has_expired():
            return False
        else:
            return True


def get_myproxy_value_from_config(config, facet):
    """
    Try to get the value for facet from 'myproxy' section in esg.ini

    :param config config: Configuration instance, e.g. from getConfig()
    :param str facet: Facet to be extracted
    :returns: The value for facet, if available, otherwise returns None
    :rtype: *str*

    """
    myproxy_section = 'myproxy'
    if config.has_section(myproxy_section):
        return config.get(myproxy_section, facet, default=None)
    else:
        return None


def logon(config, myproxy_username=None, myproxy_password=None, myproxy_hostname=None):
    """
    Use MyProxyClient to generate a certificate for publication.
    Generate appropriate directories if not exists

    :param config config: Configuration instance, e.g. from getConfig()
    :param str myproxy_username: Myproxy username
    :param str myproxy_password: Myproxy password
    :param str myproxy_hostname: Myproxy hostname

    """
    from myproxy.client import MyProxyClient

    myproxy_cert_location = config.get('DEFAULT', 'hessian_service_certfile')

    # try to get the myproxy info from ini file if not specified
    if not myproxy_hostname:
        myproxy_hostname = get_myproxy_value_from_config(config, 'hostname')
    if not myproxy_username:
        myproxy_username = get_myproxy_value_from_config(config, 'username')
    if not myproxy_password:
        myproxy_password = get_myproxy_value_from_config(config, 'password')

    myproxy_dir = os.path.dirname(myproxy_cert_location)
    myproxy_certs_dir = os.path.join(myproxy_dir, 'certificates')

    if not os.path.isdir(myproxy_dir):
        os.mkdir(myproxy_dir)
    if not os.path.isdir(myproxy_certs_dir):
        os.mkdir(myproxy_certs_dir)

    if myproxy_hostname is None:
        print '\nEnter myproxy hostname:',
        myproxy_hostname = raw_input()
    if myproxy_username is None:
        print 'Enter myproxy username:',
        myproxy_username = raw_input()
    if myproxy_password is None:
        myproxy_password = getpass.getpass('Enter password for %s: ' % myproxy_username)

    myproxy = MyProxyClient(hostname=myproxy_hostname, caCertDir=myproxy_certs_dir)
    credentials = myproxy.logon(myproxy_username, myproxy_password, bootstrap=True, lifetime=259200)
    myproxy.writeProxyFile(credentials[0], credentials[1], credentials[2], filePath=myproxy_cert_location)
