#
# A Hessian client interface for Python.  The date and long types require
# Python 2.2 or later.
#
# The Hessian proxy is used as follows:
#
# proxy = Hessian("http://hessian.caucho.com/test/basic")
#
# print proxy.hello()
#
# --------------------------------------------------------------------
#
# The Apache Software License, Version 1.1
#
# Copyright (c) 2001-2002 Caucho Technology, Inc.  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# 3. The end-user documentation included with the redistribution, if
#    any, must include the following acknowlegement:
#       "This product includes software developed by the
#        Caucho Technology (http://www.caucho.com/)."
#    Alternately, this acknowlegement may appear in the software itself,
#    if and wherever such third-party acknowlegements normally appear.
#
# 4. The names "Hessian", "Resin", and "Caucho" must not be used to
#    endorse or promote products derived from this software without prior
#    written permission. For written permission, please contact
#    info@caucho.com.
#
# 5. Products derived from this software may not be called "Resin"
#    nor may "Resin" appear in their names without prior written
#    permission of Caucho Technology.
#
# THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESSED OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED.  IN NO EVENT SHALL CAUCHO TECHNOLOGY OR ITS CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# --------------------------------------------------------------------
#
# Credits: hessianlib.py was inspired and partially based on
# xmlrpclib.py created by Fredrik Lundh at www.pythonware.org
#
import string, time
import urllib
from types import *
from struct import unpack
from struct import pack
from esgcet import messaging

__version__ = "0.1"
DEBUG = False  # Set True to print raw request/response


# --------------------------------------------------------------------
# Exceptions

class Error:
    pass


class ProtocolError(Error):
    # Represents an HTTP protocol error
    def __init__(self, url, code, message, headers):
        self.url = url
        self.code = code
        self.message = message
        self.headers = headers

    def __repr__(self):
        return (
            "<ProtocolError for %s: %s %s>" %
            (self.url, self.code, self.message)
        )


class RemoteCallException(Error):
    def __init__(self, message, **detail):
        self.message = message

    def __repr__(self):
        if type(self.message) is DictType:
            if self.message.has_key('detail'):  # Java
                result = ''
                msg = self.message['message']
                code = self.message['code']
                detail = self.message['detail']
                stackTrace = detail['stackTrace']
                result += 'Java %s: %s\n' % (code, msg)
                for item in stackTrace:
                    result += '\tat %s.%s(%s:%d)\n' % (
                    item['declaringClass'], item['methodName'], item['fileName'], item['lineNumber'])
                return result
            elif self.message.has_key('stackTrace'):  # HessianLib
                return 'Remote traceback: ' + self.message['stackTrace']
        else:
            return `self.message`


# --------------------------------------------------------------------
# Wrappers for Hessian data types non-standard in Python
#
#
# Date - wraps a time value in seconds
#
class Date:
    def __init__(self, value=0):
        self.value = value

    def __repr__(self):
        return ("<Date %s at %x>" %
                (time.asctime(time.localtime(self.value)), id(self)))

    def _hessian_write(self, out):
        out.write("d")
        out.write(pack(">q", self.value * 1000.0))


#
# Binary - binary data
#

class Binary:
    def __init__(self, data=None):
        self.data = data

    def _hessian_write(self, out):
        out.write('B')
        out.write(pack('>H', len(self.data)))
        out.write(self.data)


# --------------------------------------------------------------------
# Marshalling and unmarshalling code

#
# HessianWriter - writes Hessian data from Python objects
#
class HessianWriter:
    dispatch = {}

    def write_call(self, method, params):
        self.refs = {}
        self.ref = 0
        self.__out = []
        self.write = write = self.__out.append

        write("c\x01\x00m");
        write(pack(">H", len(method)));
        write(method);
        for v in params:
            self.write_object(v)
        write("z");
        try:
            result = string.join(self.__out, "")
        except UnicodeDecodeError:
            print "Error joining string %s" % self.__out
            raise
        del self.__out, self.write, self.refs
        return result

    def write_object(self, value):
        try:
            f = self.dispatch[type(value)]
        except KeyError:
            raise TypeError, "cannot write %s objects" % type(value)
        else:
            f(self, value)

    def write_int(self, value):
        self.write('I')
        self.write(pack(">l", value))

    dispatch[IntType] = write_int

    def write_long(self, value):
        self.write('L')
        self.write(pack(">q", value))

    dispatch[LongType] = write_long

    def write_double(self, value):
        self.write('D')
        self.write(pack(">d", value))

    dispatch[FloatType] = write_double

    def write_string(self, value):
        self.write('S')
        self.write(pack('>H', len(value)))
        self.write(value)

    dispatch[StringType] = write_string

    def write_unicode(self, value):
        try:
            svalue = str(value)
        except UnicodeDecodeError:
            print "Error translating string to ASCII: %s" % value
            raise
        self.write('S')
        self.write(pack('>H', len(svalue)))
        self.write(svalue)

    dispatch[UnicodeType] = write_unicode

    def write_boolean(self, value):
        if value:
            self.write('T')
        else:
            self.write('F')

    dispatch[BooleanType] = write_boolean

    def write_reference(self, value):
        # check for and write circular references
        # returns 1 if the object should be written, i.e. not a reference
        i = id(value)
        if self.refs.has_key(i):
            self.write('R')
            self.write(pack(">L", self.refs[i]))
            return 0
        else:
            self.refs[i] = self.ref
            self.ref = self.ref + 1
            return 1

    def write_list(self, value):
        if self.write_reference(value):
            # self.write("Vt\x00\x00I");
            self.write("Vl")
            self.write(pack('>l', len(value)))
            for v in value:
                self.write_object(v)
            self.write('z')

    dispatch[TupleType] = write_list
    dispatch[ListType] = write_list

    def write_map(self, value):
        if self.write_reference(value):
            self.write("Mt\x00\x00")
            for k, v in value.items():
                self.write_object(k)
                self.write_object(v)
            self.write("z")

    dispatch[DictType] = write_map

    def write_instance(self, value):
        # check for special wrappers
        if hasattr(value, "_hessian_write"):
            value._hessian_write(self)
        else:
            fields = value.__dict__
            if self.write_reference(fields):
                self.write("Mt\x00\x00")
                for k, v in fields.items():
                    self.write_object(k)
                    self.write_object(v)
                self.write("z")

    dispatch[InstanceType] = write_instance


#
# Parses the results from the server
#
class HessianParser:
    def __init__(self, f):
        self._f = f
        self._peek = -1
        # self.read = f.read
        self._refs = []

    def read(self, len):
        if self._peek >= 0:
            value = self._peek
            self._peek = -1
            return value
        else:
            value = self._f.read(len)
            return value

    def parse_reply(self):
        # parse header 'c' x01 x00 'v' ... 'z'
        read = self.read
        if read(1) != 'r':
            self.error()
        major = read(1)
        minor = read(1)

        value = self.parse_object()

        if read(1) == 'z':
            return value
        self.error()  # actually a fault

    def parse_object(self):
        # parse an arbitrary object based on the type in the data
        code = self.read(1)
        if code != 's':
            return self.parse_object_code(code)
        else:

            # Parse chunked string: ('s' b16 b8 data)* 'S' b16 b8 data
            result = self.parse_object_code(code)
            code = self.read(1)
            while code == 's':
                result += self.parse_object_code(code)
                code = self.read(1)

            if code == 'S':
                result += self.parse_object_code(code)
                return result
            else:
                raise "Hessian protocol error: chunked string terminated with code: %s, should have been 'S'" % `code`

    def parse_object_code(self, code):
        # parse an object when the code is known
        read = self.read

        if code == 'N':
            return None

        elif code == 'T':
            return True

        elif code == 'F':
            return False

        elif code == 'I':
            return unpack('>l', read(4))[0]

        elif code == 'L':
            return unpack('>q', read(8))[0]

        elif code == 'D':
            return unpack('>d', read(8))[0]

        elif code == 'd':
            ms = unpack('>q', read(8))[0]

            return Date(int(ms / 1000.0))

        elif code == 'S' or code == 'X' or code == 's':
            return self.parse_string()

        elif code == 'B':
            # return Binary(self.parse_string())
            return self.parse_string()

        elif code == 'V':
            self.parse_type()  # skip type
            self.parse_length()  # skip length
            list = []
            self._refs.append(list)
            ch = read(1)
            while ch != 'z':
                list.append(self.parse_object_code(ch))
                ch = read(1)
            return list

        elif code == 'M':
            self.parse_type()  # skip type
            map = {}
            self._refs.append(map)
            ch = read(1)
            while ch != 'z':
                key = self.parse_object_code(ch)
                value = self.parse_object()
                map[key] = value
                ch = read(1)
            return map

        elif code == 'R':
            return self._refs[unpack('>l', read(4))[0]]

        elif code == 'r':
            self.parse_type()  # skip type
            url = self.parse_type()  # reads the url
            return Hessian(url)

        elif code == 'f':
            result = self.parse_object_code('M')  # parse faults as maps
            return RemoteCallException(result)

        else:
            raise "UnknownObjectCode %s" % `code`

    def parse_string(self):
        f = self._f
        len = unpack('>H', f.read(2))[0]
        return f.read(len)

    def parse_type(self):
        f = self._f
        code = self.read(1)
        if code != 't':
            self._peek = code
            return ""
        len = unpack('>H', f.read(2))[0]
        return f.read(len)

    def parse_length(self):
        f = self._f
        code = self.read(1);
        if code != 'l':
            self._peek = code
            return -1;
        len = unpack('>l', f.read(4))
        return len

    def error(self):
        raise "FOO"


#
# Encapsulates the method to be called
#
class _Method:
    def __init__(self, invoker, method):
        self._invoker = invoker
        self._method = method

    def __call__(self, *args):
        return self._invoker(self._method, args)


class ResponseProxy:
    def __init__(self, response):
        self._response = response

    def read(self, len):
        result = self._response.read(len)
        if DEBUG:
            messaging.info(`result`)
        return result

    def close(self):
        self._response.close()


# --------------------------------------------------------------------
# Hessian is the main class.  A Hessian proxy is created with the URL
# and then called just as for a local method
#
# proxy = Hessian("http://www.caucho.com/hessian/test/basic")
# print proxy.hello()
#
class Hessian:
    """Represents a remote object reachable by Hessian"""

    def __init__(self, url, port=None, key_file=None, cert_file=None, debug=False):
        """
        Create a Hessian proxy.

        url
          String of the form http[s]://host/path. Note that the port is specified separately.

        port
          Defaults to 80 for http, 443 for https.

        key_file
          Key file in PEM format, if the scheme is https and client authentication is to be used.

        cert_file
          User certificate in PEM format, if the scheme is https and client authentication is to be used.

        debug
          True iff debug info is to be printed.

        """
        # Creates a Hessian proxy object
        global DEBUG

        self.service_type = 'HESSIAN'
        self._url = url
        self._port = port
        self._key_file = key_file
        self._cert_file = cert_file
        # print "Using key file = %s, cert file = %s"%(key_file, cert_file)
        messaging.debug("Using key file = %s, cert file = %s" % (key_file, cert_file))
        if debug:
            DEBUG = True

        # get the uri
        scheme, uri = urllib.splittype(url)
        if scheme not in ["http", "https"]:
            raise IOError, "unsupported Hessian protocol"

        self._scheme = scheme
        self._host, self._uri = urllib.splithost(uri)

    def __invoke(self, method, params):
        # call a method on the remote server

        request = HessianWriter().write_call(method, params)

        # ----------------------------------------------------------------------
        # Patch for HTTP proxy support starts here.  Stephen.Pascoe@stfc.ac.uk
        #
        import httplib, os, urlparse, ssl

        if self._scheme == "http":
            proxy_url = os.environ.get('http_proxy')
            if proxy_url is not None:
                if DEBUG:
                    messaging.info('Proxy detected at %s' % proxy_url)
                proxy_parts = urlparse.urlparse(proxy_url)
                proxy_host = proxy_parts.hostname
                proxy_port = proxy_parts.port
                if proxy_port is None:
                    proxy_port = 80
                h = httplib.HTTPConnection(proxy_host, port=proxy_port)
            else:
                h = httplib.HTTPConnection(self._host, port=self._port)
        else:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
            conn_args = {'port' : self._port,
                         'key_file' : self._key_file,
                         'cert_file': self._cert_file,
                         'context': ctx}
            h = httplib.HTTPSConnection(self._host, **conn_args)

            # test the connection - may need unverified with test index nodes
            # (hopefully not with operational nodes)
            try:
                h.request("HEAD", "/")
                h.getresponse()
            except ssl.SSLError:
                messaging.warning('SSL error - disabling SSL verification')
                conn_args['context'] = ssl._create_unverified_context()
                h = httplib.HTTPSConnection(self._host, **conn_args)

        req_headers = {'Host': self._host,
                       'User-Agent': "hessianlib.py/%s" % __version__,
                       'Content-Length': str(len(request)),
                       }

        if DEBUG:
            messaging.info('Sending request: %s' % `request`)
        h.request("POST", self._url, request, req_headers)
        #
        # End Patch from Stephen.Pascoe@stfc.ac.uk
        # ----------------------------------------------------------------------

        response = h.getresponse()
        headers = response.getheaders()
        errcode = response.status
        errmsg = response.reason
        # errcode, errmsg, headers = h.getreply()

        if errcode != 200:
            raise ProtocolError(self._url, errcode, errmsg, headers)

        # return self.parse_response(h.getfile())
        if DEBUG:
            messaging.info('Got response:')
        responseProxy = ResponseProxy(response)
        return self.parse_response(responseProxy)

    def parse_response(self, f):
        # read response from input file, and parse it

        parser = HessianParser(f)
        value = parser.parse_reply()
        f.close()

        # Raise a fault reply
        if isinstance(value, Error):
            raise value

        return value

    def _hessian_write(self, out):
        # marshals the proxy itself
        out.write("rt\x00\x00S")
        out.write(pack(">H", len(self._url)))
        out.write(self._url)

    def __repr__(self):
        return "<HessianProxy %s>" % self._url

    __str__ = __repr__

    def __getattr__(self, name):
        # encapsulate the method call
        return _Method(self.__invoke, name)


#
# Testing code.
#
if __name__ == "__main__":

    proxy = Hessian("http://hessian.caucho.com/test/test")

    try:
        print proxy.hello()
    except Error, v:
        print "ERROR", v
