#!/usr/bin/env python

from esgcet.exceptions import ESGMethodNotImplemented

class FormatHandler(object):
    """
    Base class for self-describing file I/O. The API is modeled after the netCDF classic data model:

    - A file contains a collection of variables (multidimensional arrays) and attributes.
    - Each variable has an associated ordered list of dimension names.
    - The attributes are global, or variable-specific.
    - Attributes are scalar or one-dimensional arrays.

    Subclasses should implement the following methods:

    - open: Open a file.
    - getFormatDescription: Get a string description of the format.
    - close: Close a file.
    - getAttribute: Get a global or variable attribute.
    - getVariable: Get variable data (only used for coordinate variables).
    - hasAttribute: Inquire if a global or variable attribute exists.
    - hasVariable: Inquire if a variable exists.
    - inquireAttributeList: Get a list of attributes.
    - inquireVariableDimensions: Get a list of variable dimensions.
    - inquireVariableList: Get a list of variables.
    - inquireVariableShape: Get the shape of a variable, as a tuple.

    """

    def __init__(self, *args):
        raise ESGMethodNotImplemented

    @staticmethod
    def open(path, mode='r'):
        """
        Open a file.

        Returns a file object.

        path
          String path name.

        mode
          String mode. Since only mode='r' (read-only) is currently used, it is optional.
        """
        raise ESGMethodNotImplemented

    @staticmethod
    def getFormatDescription():
        """Get a desription of the format.

        Returns a string format descriptions.

        """
        raise ESGMethodNotImplemented

    def close(self):
        """
        Close the file.
        """
        raise ESGMethodNotImplemented
    
    def inquireVariableList(self):
        """
        Inquire the variable names.

        Returns a list of string variable names.
        """
        raise ESGMethodNotImplemented

    def inquireVariableDimensions(self, variableName):
        """
        Inquire the dimension names of a variable.

        Returns a list of string dimension names of the variable.
        """
        raise ESGMethodNotImplemented

    def inquireAttributeList(self, variableName=None):
        """
        Inquire global or variable attribute names.

        Returns a list of attribute names.

        variableName
          String variable name. If None, return the global attribute list.
        """
        raise ESGMethodNotImplemented

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
        raise ESGMethodNotImplemented

    def hasVariable(self, variableName):
        """
        Returns True iff a file has the given variable.

        variableName:
          String name of the variable.
        """
        raise ESGMethodNotImplemented

    def hasAttribute(self, attributeName, variableName=None):
        """
        Returns True iff a file or variable has an attribute.

        attributeName
          String name of the attribute.

        variableName:
          String name of the variable. If None, check a global attribute.
        """
        raise ESGMethodNotImplemented

    def inquireVariableShape(self, variableName):
        """
        Get the shape of the variable multidimensional array.

        Returns a tuple of ints.

        variableName
          String name of the variable.
        """
        raise ESGMethodNotImplemented

    def getVariable(self, variableName, index=None):
        """
        Get the value of the variable.

        Returns a numpy array.

        variableName
          String name of the variable.

        index
          Integer index to select along the first dimension. If None, return all values.
          
        """
        raise ESGMethodNotImplemented

