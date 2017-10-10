"Handle generic netCDF data file metadata"

from esgcet.model import cleanup_time_units
from esgcet.exceptions import *
from esgcet.config import ProjectHandler, FormatHandler, getConfig, splitLine
try:
    import cdat_info
    cdat_info.ping = False
except:
    pass
from cdms2 import Cdunif
from cdms2 import open as cdms_open


import datetime

_invalidVarAttrs = set(['_FillValue', 'assignValue', 'getValue', 'getitem', 'getslice', 'setitem', 'setslice', 'typecode'])
_invalidGlobalAttrs = set(['close', 'createDimension', 'createVariable', 'flush', 'readDimension', 'sync'])
class CdunifFormatHandler(FormatHandler):
    """
    Generic file accessed with Cdunif / netCDF-3 interface.
    """

    def __init__(self, file, path):
        self.file = file
        self.variables = file.variables
        self.path = path


    @staticmethod
    def open(path, mode='r'):
        cf = Cdunif.CdunifFile(path)
        f = CdunifFormatHandler(cf, path)
        return f

    @staticmethod
    def getFormatDescription():
        return 'netCDF'

    def inquireVariableList(self):
        """
        Inquire the variable names.

        Returns a list of string variable names.
        """
        return self.variables.keys()

    def inquireVariableDimensions(self, variableName):
        """
        Inquire the dimension names of a variable.

        Returns a list of string dimension names of the variable.
        """
        return self.variables[variableName].dimensions

    def inquireAttributeList(self, variableName=None):
        """
        Inquire global or variable attribute names.

        Returns a list of attribute names.

        variableName
          String variable name. If None, return the global attribute list.
        """
        if variableName is not None:
            attset = set(dir(self.variables[variableName]))
            attlist = list(attset.difference(_invalidVarAttrs))
        else:
            attset = set(dir(self.file))
            attlist = list(attset.difference(_invalidGlobalAttrs))
        return attlist

    def getAttribute(self, attributeName, variableName, *args):
        """
        Get the value of a global or variable attribute.

        Returns the attribute value, as an int, float, or 1-d numpy array.

        attributeName
          String name of the attribute.

        variableName:
          String name of the variable. If None, get a global attribute.
        """
        if variableName is not None:
            result = getattr(self.variables[variableName], attributeName, *args)
        else:
            result = getattr(self.file, attributeName, *args)
        # Clean up GFDL time units
        if attributeName=="units":
            result = cleanup_time_units(result)
        return result

    def hasVariable(self, variableName):
        """
        Returns True iff a file has the given variable.

        variableName:
          String name of the variable.
        """
        return self.variables.has_key(variableName)

    def hasAttribute(self, attributeName, variableName=None):
        """
        Returns True iff a file or variable has an attribute.

        attributeName
          String name of the attribute.

        variableName:
          String name of the variable. If None, check a global attribute.
        """
        if variableName is not None:
            result = hasattr(self.variables[variableName], attributeName)
        else:
            result = hasattr(self.file, attributeName)
        return result

    def inquireVariableShape(self, variableName):
        """
        Get the shape of the variable multidimensional array.

        Returns a tuple of ints.

        variableName
          String name of the variable.
        """
        return self.variables[variableName].shape

    def getVariable(self, variableName, index=None):
        """
        Get the value of the variable.

        Returns a numpy array.

        variableName
          String name of the variable.

        index
          Integer index to select along the first dimension. If None, return all values.
          
        """
        variable = self.variables[variableName]
        try:
            if index is not None:
                result = variable[index]
            else:
                result = variable[:]
            return result
        except ValueError:
            return None        

    def close(self):
        """
        Close the file.
        """
        self.file.close()

class NetcdfHandler(ProjectHandler):

    def getContext(self, **context):
        ProjectHandler.getContext(self, **context)


        if self.context.get('creation_time', '')=='':
            self.context['creation_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.context.get('format', '')=='':
            self.context['format'] = self.formatHandlerClass.getFormatDescription()
            conventions = self.context.get('Conventions')
            if conventions is not None:
                self.context['format'] += ', %s'%conventions
        return self.context

    def readContext(self, cdfile):
        "Get a dictionary of key/value pairs from an open file."
        f = cdfile.file

        result = {}
        if hasattr(f, 'title'):
            result['title'] = f.title
        if hasattr(f, 'Conventions'):
            result['Conventions'] = f.Conventions
        if hasattr(f, 'source'):
            result['source'] = f.source
        if hasattr(f, 'history'):
            result['history'] = f.history

        config = getConfig()
        projectSection = 'project:' + self.name

        config_key = "extract_global_attrs"

        if config.has_option(projectSection, config_key):
            cdms_file = cdms_open(self.path)
            for key in splitLine(config.get(projectSection, config_key), ','):
                
                # check for mapped keys
                if ':' in key:
                    parts = key.split(':')
                    value = cdms_file.__getattribute__(parts[0])
                    result[parts[1]] = value

                else:
                    result[key] = cdms_file.__getattribute__(key)

        return result

BasicHandler = NetcdfHandler
