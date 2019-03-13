"Handle CF metadata and time value logic"

try:
    import cdat_info
    cdat_info.ping = False
except:
    pass
import cdtime

from metadata import MetadataHandler
from cdtime import reltime, DefaultCalendar

# Map between cdtime calendar and CF tags
_tagToCalendar = {
    'gregorian' : cdtime.MixedCalendar,
    'standard' : cdtime.GregorianCalendar,
    'noleap' : cdtime.NoLeapCalendar,
    'julian' : cdtime.JulianCalendar,
    'proleptic_gregorian' : cdtime.GregorianCalendar,
    '360_day' : cdtime.Calendar360,
    '360' : cdtime.Calendar360,
    '365_day' : cdtime.NoLeapCalendar,
    }

_LAS2CDUnits = {
    "year" : cdtime.Year,
    "month" : cdtime.Month,
    "day" : cdtime.Day,
    "hour" : cdtime.Hour,
    "minute" : cdtime.Minute,
    "second" : cdtime.Second,
    "years" : cdtime.Year,
    "months" : cdtime.Month,
    "days" : cdtime.Day,
    "hours" : cdtime.Hour,
    "minutes" : cdtime.Minute,
    "seconds" : cdtime.Second,
    "season" : cdtime.Season, # needed for CORDEX
    }

class CFHandler(MetadataHandler):

    @staticmethod
    def axisIsTime(variable):
        # Note: relax the criteria somewhat to handle aggregate time variables
        if variable is None:
            return False
        varid = variable.short_name.lower()
        axisattr = variable.lookupAttr('axis')
        if (axisattr is not None) and axisattr=='T': return True
        return (varid[0:4] == 'time')

    @staticmethod
    def axisIsLongitude(variable):
        if variable is None or (len(variable.dimensions)!=1) or (variable.short_name!=variable.dimensions[0].name):
            return False
        varid = variable.short_name.lower()
        axisattr = variable.lookupAttr('axis')
        if (axisattr is not None) and axisattr=='X': return True
        units = variable.lookupAttr('units')
        if (units is not None) and units=='degrees_east': return True
        return (varid[0:3] == 'lon')

    @staticmethod
    def axisIsLatitude(variable):
        if variable is None or (len(variable.dimensions)!=1) or (variable.short_name!=variable.dimensions[0].name):
            return False
        varid = variable.short_name.lower()
        axisattr = variable.lookupAttr('axis')
        if (axisattr is not None) and axisattr=='Y': return True
        units = variable.lookupAttr('units')
        if (units is not None) and units=='degrees_north': return True
        return (varid[0:3] == 'lat')

    @staticmethod
    def axisIsLevel(variable):
        if variable is None or (len(variable.dimensions)!=1) or (variable.short_name!=variable.dimensions[0].name):
            return False
        varid = variable.short_name.lower()
        axisattr = variable.lookupAttr('axis')
        if (axisattr is not None) and axisattr=='Z': return True
        return ((varid[0:3] == 'lev') or (varid[0:5] == 'depth')) # or (id in level_aliases))

    @staticmethod
    def levelDirection(variable):
        varid = variable.short_name.lower()
        if varid[0:5]=='depth':
            return "down"
        else:
            return "up"

    @staticmethod
    def getCalendarTag(variable):
        if variable is None:
            return None
        calenattr = variable.lookupAttr('calendar')
        if calenattr is not None:
            calendar = calenattr.lower()
        else:
            calendar = None

        return calendar

    @staticmethod
    def tagToCalendar(calendarTag):
        """
        Translate from a CF calendar tag to the equivalent cdtime calendar type.

        Returns a cdtime calendar.

        calendarTag
          String CF calendar tag, one of:
          'gregorian', 'standard', 'noleap', 'julian', 'proleptic_gregorian', '360_day', '360', '365_day'
          
        """
        return _tagToCalendar.get(calendarTag, DefaultCalendar)

    @staticmethod
    def checkTimes(firstValue, lastValue, units, calendar, deltaValue, deltaUnits, npoints):
        """
        Check that a time range in the form (firstValue, lastValue) is equivalent to
        a time range of the form (firstValue, deltaValue, npoints). The representations
        are considered equivalent if:

          lastValue = firstValue + (npoints-1)*deltaValue

        Return (equivalent, firstTime, lastTime, lastEstimated) where:
          - equivalent is a Boolean, True iff the two representations are equivalent
          - firstTime is a :meth:`cdtime.comptime`value representing the first timepoint
          - lastTime is a :meth:`cdtime.comptime`value representing the last timepoint
          - lastEstimated is a :meth:`cdtime.comptime`value representing the last timepoint, based on
            the (firstValue, deltaValue, npoints) representation. If the representations
            are not equivalent, it will differ from lastValue.

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
        first = reltime(firstValue, units)
        last = reltime(lastValue, units)
        firstAdjusted = first.tocomp(calendar).add(0, deltaUnits)
        lastAdjusted = last.tocomp(calendar).add(0, deltaUnits)
        lastEstimated = firstAdjusted.add((npoints-1)*deltaValue, deltaUnits, calendar)
        result = lastEstimated.cmp(lastAdjusted)
        return (result==0), firstAdjusted, lastAdjusted, lastEstimated

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
        t = reltime(value, units)
        c = t.tocomp(_tagToCalendar[calendarTag])
        result = "%04d-%02d-%02dT%02d:%02d:%02d"%(c.year, c.month, c.day, c.hour, c.minute, int(c.second))
        return result

    @staticmethod
    def normalizeTime(fromDimensionValue, fromUnits, toUnits, calendar=DefaultCalendar):
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
        result = reltime(fromDimensionValue, fromUnits)
        relresult = result.torel(toUnits, calendar)
        relvalue = relresult.value
        
        return float(relvalue)

    @staticmethod
    def LAS2CDUnits(lasUnits):
        """
        Translate from LAS style units to cdtime units. For example, "month" is translated to cdtime.Month.

        Returns the equivalent cdtime units representation.

        lasUnits:
          String LAS units.
        """
        return _LAS2CDUnits[lasUnits]
