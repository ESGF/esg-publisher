"Handle CF metadata"

import cdtime

# Map between cdtime calendar and CF tags
calendarToTag = {
    cdtime.MixedCalendar : 'gregorian',
    cdtime.NoLeapCalendar : 'noleap',
    cdtime.GregorianCalendar : 'proleptic_gregorian',
    cdtime.JulianCalendar : 'julian',
    cdtime.Calendar360 : '360_day'
    }

tagToCalendar = {
    'gregorian' : cdtime.MixedCalendar,
    'standard' : cdtime.GregorianCalendar,
    'noleap' : cdtime.NoLeapCalendar,
    'julian' : cdtime.JulianCalendar,
    'proleptic_gregorian' : cdtime.GregorianCalendar,
    '360_day' : cdtime.Calendar360,
    '360' : cdtime.Calendar360,
    '365_day' : cdtime.NoLeapCalendar,
    }

class CFHandler(object):

    _standardNames = {}
    _initialized = False

    def __init__(self, Session=None):

        if not self._initialized:
            from esgcet.model import StandardName
            session = Session()
            standardNames = session.query(StandardName).all()
            for s in standardNames:
                self._standardNames[s.name] = s
            session.close()
            self._initialized = True

    def validateStandardName(self, name):
        return (self._standardNames.get(name, None) is not None)
    
    def axisIsTime(self, variable):
        # Note: relax the criteria somewhat to handle aggregate time variables
        if variable is None:
            return False
        varid = variable.short_name.lower()
        axisattr = variable.lookupAttr('axis')
        if (axisattr is not None) and axisattr=='T': return True
        return (varid[0:4] == 'time')

    def axisIsLongitude(self, variable):
        if variable is None or (len(variable.dimensions)!=1) or (variable.short_name!=variable.dimensions[0].name):
            return False
        varid = variable.short_name.lower()
        axisattr = variable.lookupAttr('axis')
        if (axisattr is not None) and axisattr=='X': return True
        units = variable.lookupAttr('units')
        if (units is not None) and units=='degrees_east': return True
        return (varid[0:3] == 'lon')

    def axisIsLatitude(self, variable):
        if variable is None or (len(variable.dimensions)!=1) or (variable.short_name!=variable.dimensions[0].name):
            return False
        varid = variable.short_name.lower()
        axisattr = variable.lookupAttr('axis')
        if (axisattr is not None) and axisattr=='Y': return True
        units = variable.lookupAttr('units')
        if (units is not None) and units=='degrees_north': return True
        return (varid[0:3] == 'lat')

    def axisIsLevel(self, variable):
        if variable is None or (len(variable.dimensions)!=1) or (variable.short_name!=variable.dimensions[0].name):
            return False
        varid = variable.short_name.lower()
        axisattr = variable.lookupAttr('axis')
        if (axisattr is not None) and axisattr=='Z': return True
        return ((varid[0:3] == 'lev') or (varid[0:5] == 'depth')) # or (id in level_aliases))

    def levelDirection(self, variable):
        varid = variable.short_name.lower()
        if varid[0:5]=='depth':
            return "down"
        else:
            return "up"

    def getCalendarTag(self, variable):
        if variable is None:
            return None
        calenattr = variable.lookupAttr('calendar')
        if calenattr is not None:
            calendar = calenattr.lower()
        else:
            calendar = None

        return calendar

