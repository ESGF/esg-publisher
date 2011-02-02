#!/usr/bin/env python

from esgcet.exceptions import ESGMethodNotImplemented
from esgcet.model import MAX_STANDARD_NAME_LENGTH

class MetadataHandler(object):
    """
    Base class for metadata convention and time value logic. The API is guided by the CF convention.

    Subclasses should implement all methods listed below.
    """

    _standardNames = {}
    _initialized = False

    def __init__(self, Session=None):

        if not MetadataHandler._initialized:
            from esgcet.model import StandardName
            if Session is not None:
                session = Session()
                standardNames = session.query(StandardName).all()
                for s in standardNames:
                    MetadataHandler._standardNames[s.name] = s
                session.close()
            MetadataHandler._initialized = True

    @staticmethod
    def validateStandardName(name):
        """
        Validate a name.

        Returns True iff the name is valid.

        name
          String variable name.
        """
        return (MetadataHandler._standardNames.get(name[:MAX_STANDARD_NAME_LENGTH], None) is not None)
    
    @staticmethod
    def axisIsTime(variable):
        """
        Test if a variable is a time coordinate.

        Return True iff the variable is a time coordinate.

        variable
          instance of ``esgcet.model.Variable``

        """
        raise ESGMethodNotImplemented

    @staticmethod
    def axisIsLongitude(variable):
        """
        Test if a variable is a longitude coordinate.

        Return True iff the variable is a longitude coordinate.

        variable
          instance of ``esgcet.model.Variable``

        """
        raise ESGMethodNotImplemented

    @staticmethod
    def axisIsLatitude(variable):
        """
        Test if a variable is a latitude coordinate.

        Return True iff the variable is a latitude coordinate.

        variable
          instance of ``esgcet.model.Variable``

        """
        raise ESGMethodNotImplemented

    @staticmethod
    def axisIsLevel(variable):
        """
        Test if a variable is a vertical level coordinate.

        Return True iff the variable is a vertical level coordinate.

        variable
          instance of ``esgcet.model.Variable``

        """
        raise ESGMethodNotImplemented

    @staticmethod
    def levelDirection(variable):
        """
        Get the vertical level direction.

        Returns the String 'up' or 'down'.

        variable
          instance of ``esgcet.model.Variable``
        
        """
        raise ESGMethodNotImplemented

    @staticmethod
    def getCalendarTag(variable):
        """
        Get the time calendar attribute of a time coordinate.

        Returns a String calendar.

        variable
          instance of ``esgcet.model.Variable``
        
        """
        raise ESGMethodNotImplemented

    @staticmethod
    def tagToCalendar(calendarTag):
        """
        Translate from a CF calendar tag to the equivalent cdtime calendar type.

        Returns a cdtime calendar.

        calendarTag
          String CF calendar tag, one of:
          'gregorian', 'standard', 'noleap', 'julian', 'proleptic_gregorian', '360_day', '360', '365_day'
          
        """
        raise ESGMethodNotImplemented

    @staticmethod
    def checkTimes(firstValue, lastValue, units, calendar, deltaValue, deltaUnits, npoints):
        """
        Check that a time range in the form (firstValue, lastValue) is equivalent to
        a time range of the form (firstValue, deltaValue, npoints). The representations
        are considered equivalent if:

          lastValue = firstValue + (npoints-1)*deltaValue

        Return (equivalent, firstTime, lastTime, lastEstimated) where:
          - equivalent is a Boolean, True iff the two representations are equivalent
          - firstTime is a cdtime ``comptime`` value representing the first timepoint
          - lastTime is a cdtime ``comptime`` value representing the last timepoint
          - lastEstimated is a cdtime ``comptime`` value representing the last timepoint, based on
            the (firstValue, deltaValue, npoints) representation.

        The first timepoint in the range is a relative time (firstValue, units, calendar);
        similarly the last timepoint is (lastValue, units, calendar):

        firstValue
          Float value of first timepoint.

        lastValue
          Float value last timepoint.

        units
          String time units.

        calendar
          cdtime calendar type

        deltaValue
          Float value of time delta representation.

        deltaUnits
          cdtime interval, for example, cdtime.Month

        npoints
          Integer number of points in time delta representation.

        """
        raise ESGMethodNotImplemented

    @staticmethod
    def genTime(value, units, calendarTag):
        """
        Generate a string representation of a relative time value.

        Returns a string representation of the relative time (value, units)

        value
          Float time value

        units
          String time units

        calendarTag
          String cdtime calendar tag.
        """
        raise ESGMethodNotImplemented

    @staticmethod
    def normalizeTime(fromDimensionValue, fromUnits, toUnits, calendar=None):
        """
        Normalize a relative time value (fromDimensionValue, fromUnits) to different units.

        Returns the float value of the normalized time. In other words, the normalized
        time is (return_value, toUnits).

        fromDimensionValue
          Float value of input relative time.

        fromUnits
          String units of input relative time.

        toUnits
          String time units of result time.

        calendar
          cdtime calendar type.
        """
        raise ESGMethodNotImplemented

    @staticmethod
    def LAS2CDUnits(lasUnits):
        """
        Translate from LAS style units to cdtime units. For example, "month" is translated to cdtime.Month.

        Returns the equivalent cdtime units representation.

        lasUnits:
          String LAS units.
        """
        raise ESGMethodNotImplemented
