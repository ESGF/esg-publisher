"""-*- Python -*-
Format handler template.

To create a format handler:

    - Modify the methods in CustomFormatHandler as needed. See the documentation
      for FormatHandler class.
      
      Note: The handler class name is arbitrary, provided it matches
      the setup.py 'handler' entry point of the esgcet.format_handlers group.

      Note: This template extends the default netCDF/Cdunif handler. To start
      from scratch, inherit from FormatHandler instead, and implement
      the methods.
      
    - Install the handler package:

        python setup.py --verbose install
        
    - In esg.ini, associate the format and handler name, e.g.:

        [project:my_project]
        ...
        format_handler = <format_handler_name>
"""
from esgcet.exceptions import *
from esgcet.config import FormatHandler, CdunifFormatHandler, getConfig
from cdms2 import Cdunif

import pdb


class MultipleFormatHandler(CdunifFormatHandler):

    def __init__(self, cdf, path):
        
        self.attr_only = False
        if (cdf is None ):
            self.noncd = True
            self.file = {}
            self.path = path
        else:
            # load config and set it based on 
            config = getConfig()
            projectSection = 'project:dream'
            variables_none = config.get(projectSection, "variables_none", default="false")

            if variables_none == "false":
                self.noncd = False
                CdunifFormatHandler.__init__(self, cdf, path)
            elif variables_none == "attr":
                CdunifFormatHandler.__init__(self, cdf, path)
                self.attr_only = True
                self.noncd = True
            else:  # assume "true"
                self.noncd = True
                self.file = {}
                self.path = path
                self.attr_only = False

    @staticmethod
    def open(path, mode='r'):
        """
        Open a file.

        Returns an instance of the format handler. 

        path
          String path name.

        mode
          String mode. Since only mode='r' (read-only) is currently used, it is optional.
          """
        f = None
#        pdb.set_trace()
        
        if (path[-3:] == ".nc"):  

            cf = Cdunif.CdunifFile(path)

            f = MultipleFormatHandler(cf, path)
        else:
            f = MultipleFormatHandler(None, path)
        return f

    @staticmethod
    def getFormatDescription():
        """Get a desription of the format.

        Returns a string format descriptions.

        """

        return "multiple-formats"
 #           return CdunifFormatHandler.getFormatDescription()

    def close(self):
        """
        Close the file.
        """
        if self.noncd == False:
            CdunifFormatHandler.close(self)
    
    def inquireVariableList(self):
        """
        Inquire the variable names.

        Returns a list of string variable names.
        """
        if (self.noncd):
            return []
        else:
            return CdunifFormatHandler.inquireVariableList(self)

    def inquireVariableDimensions(self, variableName):
        """
        Inquire the dimension names of a variable.

        Returns a list of string dimension names of the variable.
        """
        if (self.noncd):
            return []
        else:
            return CdunifFormatHandler.inquireVariableDimensions(self, variableName)

    def inquireAttributeList(self, variableName=None):
        """
        Inquire global or variable attribute names.

        Returns a list of attribute names.

        variableName
          String variable name. If None, return the global attribute list.
        """
        if (self.noncd and not self.attr_only):
            return []
        else:
            return CdunifFormatHandler.inquireAttributeList(self, variableName=variableName)

    def getAttribute(self, attributeName, variableName, *args):
        """
        Get the value of a global or variable attribute.

        Returns the attribute value, as an int, float, or 1-d numpy array.

        attributeName
          String name of the attribute.

        variableName:
          String name of the variable. If None, get a global attribute.

        args
          optional default value if the attribute is not found.
        """
        if (self.noncd and not self.attr_only):
            return None
        else:
            return CdunifFormatHandler.getAttribute(self, attributeName, variableName, *args)

    def hasVariable(self, variableName):
        """
        Returns True iff a file has the given variable.

        variableName:
          String name of the variable.
        """
        if (self.noncd):
            return False
        else:
            return CdunifFormatHandler.hasVariable(self, variableName)

    def hasAttribute(self, attributeName, variableName=None):
        """
        Returns True iff a file or variable has an attribute.

        attributeName
          String name of the attribute.

        variableName:
          String name of the variable. If None, check a global attribute.
        """
        if (self.noncd and not self.attr_only):
            return False
        else:
            return CdunifFormatHandler.hasAttribute(self, attributeName, variableName=variableName)

    def inquireVariableShape(self, variableName):
        """
        Get the shape of the variable multidimensional array.

        Returns a tuple of ints.

        variableName
          String name of the variable.
        """
        if (self.noncd):
            return []
        else:
            return CdunifFormatHandler.inquireVariableShape(self, variableName)

    def getVariable(self, variableName, index=None):
        """
        Get the value of the variable.

        Returns a numpy array.

        variableName
          String name of the variable.

        index
          Integer index to select along the first dimension. If None, return all values.
          
        """
        if (self.noncd):
            return []
        else:
            return CdunifFormatHandler.getVariable(self, variableName, index=index)

