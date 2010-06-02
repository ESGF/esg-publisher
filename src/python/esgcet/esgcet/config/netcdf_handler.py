"Handle generic netCDF data file metadata"

from esgcet.exceptions import *
from esgcet.config import ProjectHandler
# from Scientific.IO import NetCDF
from cdms2 import Cdunif

import datetime

class NetcdfHandler(ProjectHandler):

    def openPath(self, path):
#         f = NetCDF.NetCDFFile(path)
        f = Cdunif.CdunifFile(path)
        return f

    def closePath(self, fileobj):
        fileobj.close()

    def getContext(self, **context):
        ProjectHandler.getContext(self, **context)
        if self.context.get('creation_time', '')=='':
            self.context['creation_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.context.get('format', '')=='':
            self.context['format'] = 'netCDF'
            conventions = self.context.get('Conventions')
            if conventions is not None:
                self.context['format'] += ', %s'%conventions
        return self.context

    def readContext(self, f):
        "Get a dictionary of key/value pairs from an open file."
        result = {}
        if hasattr(f, 'title'):
            result['title'] = f.title
        if hasattr(f, 'Conventions'):
            result['Conventions'] = f.Conventions
        if hasattr(f, 'source'):
            result['source'] = f.source
        return result

