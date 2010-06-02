import os
import logging
import urllib2
import cdtime
import string
from cdtime import reltime
from lxml.etree import Element, SubElement as SE, ElementTree, Comment
from esgcet.config import splitLine, splitRecord, getConfig, tagToCalendar, getThreddsServiceSpecs, getThreddsAuxiliaryServiceSpecs
from esgcet.model import *
from esgcet.exceptions import *
from sqlalchemy.orm import join
from esgcet.messaging import debug, info, warning, error, critical, exception

_nsmap = {
    None : "http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0",
    'xlink' : "http://www.w3.org/1999/xlink",
    'xsi' : "http://www.w3.org/2001/XMLSchema-instance"}
_XSI = '{%s}'%_nsmap['xsi']
_XLINK = '{%s}'%_nsmap['xlink']
SEQ=2
EVEN = 1
UNEVEN = 2
DEFAULT_THREDDS_CATALOG_VERSION = "2"
DEFAULT_THREDDS_SERVICE_APPLICATIONS = {
    'GridFTP':['DataMover-Lite'],
    'HTTPServer':['Web Browser','Web Script'],
    'OpenDAP':['Web Browser'],
    'SRM':[],
    }
DEFAULT_THREDDS_SERVICE_AUTH_REQUIRED = {
    'GridFTP':'true',
    'HTTPServer':'true',
    'OpenDAP':'false',
    'SRM':'false',
    }
DEFAULT_THREDDS_SERVICE_DESCRIPTIONS = {
    'GridFTP':'GridFTP',
    'HTTPServer':'HTTPServer',
    'OpenDAP':'OpenDAP',
    'SRM':'SRM',
    }
LAS2CDUnits = {
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
    }

ThreddsBases = ['/thredds/fileServer', '/thredds/dodsC', '/thredds/wcs', '/thredds/ncServer']
ThreddsFileServer = '/thredds/fileServer'

def parseLASTimeDelta(unitsString):
    fields = unitsString.split()
    if len(fields)!=2:
        raise ESGPublishError("Invalid LAS units string: %s, should have the form 'value units'"%unitsString)
    value = string.atof(fields[0])
    units = fields[1].lower()
    return value, LAS2CDUnits[units]

def checkTimes(firstValue, lastValue, units, calendarTag, delta, npoints):
    calendar = tagToCalendar[calendarTag]
    deltaValue, deltaUnits = parseLASTimeDelta(delta)
    result = checkTimes_1(firstValue, lastValue, units, calendar, deltaValue, deltaUnits, npoints)
    return result

def checkTimes_1(firstValue, lastValue, units, calendar, deltaValue, deltaUnits, npoints):
    first = reltime(firstValue, units)
    last = reltime(lastValue, units)
    firstAdjusted = first.tocomp(calendar).add(0, deltaUnits)
    lastAdjusted = last.tocomp(calendar).add(0, deltaUnits)
    lastEstimated = firstAdjusted.add((npoints-1)*deltaValue, deltaUnits, calendar)
    result = lastEstimated.cmp(lastAdjusted)
    return (result==0), firstAdjusted, lastAdjusted, lastEstimated

def splitTimes(fvlist, calendarTag, delta):
    # Split the file variables into evenly-spaced chunks.
    # Returns [chunk, chunk, ...] where each chunk is (startindex, stopindex+1, flag, nchunk, fa, la, le) and
    # flag = EVEN if the aggregate filevariable[startindex..stopindex] is evenly spaced, or
    #      = UNEVEN if no subset of filevariable[startindex..stopindex] is evenly spaced.
    # fa = firstAdjusted
    # la = lastAdjusted
    # le = lastEstimated
    #      
    # fvlist = [(filevar, firstValue, lastValue, units, ncoords), (filevar, firstValue, ...)]
    calendar = tagToCalendar[calendarTag]
    deltaValue, deltaUnits = parseLASTimeDelta(delta)
    result = []
    istart = 0
    while (istart<len(fvlist)):
        n, lookfor, ntot, fa, la, le = splitTimes_1(fvlist[istart:], calendar, deltaValue, deltaUnits)
        result.append((istart, istart+n, lookfor, ntot, fa, la, le))
        istart += n
    return result

def splitTimes_1(fvlist, calendar, deltaValue, deltaUnits):
    # Find the largest n in [0,len(fvlist)) such that either:
    # (1) fvlist[0:n] is evenly spaced and fvlist[0:n+1] is not, or
    # (2) fvlist[0:n] is unevenly spaced, and fvlist[n:n+1] is evenly spaced.

    # Check if the first file_variable is EVEN or UNEVEN
    filevar, firstValue, lastValue, units, ncoords = fvlist[0]
    result, fa, la, le = checkTimes_1(firstValue, lastValue, units, calendar, deltaValue, deltaUnits, ncoords)
    pfa, pla, ple = fa, la, le
    if result:
        lookfor = EVEN
        n = 1
        ntot = ncoords
        while (n<len(fvlist)):

            # Keep expanding the aggregate until the aggregate is unevenly spaced.
            ntot += fvlist[n][4]
            lastValue = fvlist[n][2]
            nextresult, fa, la, le = checkTimes_1(firstValue, lastValue, units, calendar, deltaValue, deltaUnits, ntot)
            if not nextresult:
                break
            else:
                n += 1
        return (n, lookfor, ntot, fa, la, le)
    else:
        lookfor = UNEVEN
        n = 1
        ntot = ncoords
        while (n<len(fvlist)):

            # Keep looking at the next file until it is evenly spaced
            ncoord = fvlist[n][4]
            ntot += ncoord
            firstValue = fvlist[n][1]
            lastValue = fvlist[n][2]
            nextresult, fa, la, le = checkTimes_1(firstValue, lastValue, units, calendar, deltaValue, deltaUnits, ncoord)
            if nextresult:
                fa, la, le = pfa, pla, ple
                break
            else:
                pfa, pla, ple = fa, la, le
                n += 1
        return (n, lookfor, ntot, fa, la, le)

def hasThreddsService(serviceName, serviceDict):
    # Returns True iff:
    # - the service is a simple Thredds service, or
    # - the service is compound, and at least one component is a Thredds service
    try:
        serviceSpec = serviceDict[serviceName]
    except KeyError:
        raise ESGPublishError("Invalid service name: %s, must be one of %s"%(serviceName, `serviceDict.keys()`))
    if serviceSpec[0]:                  # Simple service
        result = serviceSpec[1]
    else:
        result = False
        for subName in serviceSpec[1]:
            if serviceDict[subName][1]:
                result = True
                break
    return result

def _getRootPathAndLoc(fileobj, rootDict):
    fileFields = fileobj.getLocation().split(os.sep)
    if fileFields[0]=='':
        del fileFields[0]

    filesRootPath = None
    filesRootLoc = None
    for rootPath, rootLoc in rootDict.items():
        if fileFields[:len(rootLoc)] == rootLoc:
            filesRootPath = rootPath
            filesRootLoc = os.sep+apply(os.path.join, rootLoc)

    return filesRootPath, filesRootLoc

def _genService(parent, specs, initDictionary=None, serviceApplications=None, serviceAuthRequired=None, serviceDescriptions=None):

    serviceDict = {}                    # name => element
    returnDict = initDictionary
    if returnDict is None:
        returnDict = {}                 # name => (isCompound, [subservice, subservice, ...])
                                        #   -or-
                                        # name => (isSimple, isThreddsService, serviceType, base, isThreddsFileService)  

    # Create the elements
    for serviceType, base, name, compoundName in specs:
        isThreddsService = (os.path.normpath(base) in ThreddsBases)
        isThreddsFileService = (os.path.normpath(base) == ThreddsFileServer)
        desc = DEFAULT_THREDDS_SERVICE_DESCRIPTIONS[serviceType]
        if serviceDescriptions is not None:
            desc = serviceDescriptions.get(name, desc)

        # If the service is part of a compound service:
        if compoundName is not None:

            # Create the compound service if necessary
            compoundService = serviceDict.get(compoundName, None)
            if compoundService is None:
                compoundService = SE(parent, "service", name=compoundName, serviceType="Compound", base="")
                serviceDict[compoundName] = compoundService
                returnDict[compoundName] = (False, [])
                            
            # Append the simple service to the compound
            service = SE(compoundService, "service", name=name, serviceType=serviceType, base=base, desc=desc)
            serviceDict[name] = service
            returnDict[compoundName][1].append(name)
            returnDict[name] = (True, isThreddsService, serviceType, base, isThreddsFileService)

        # Otherwise if a simple service just create the service
        else:
            if serviceDict.has_key(name):
                raise ESGPublishError("Duplicate service name in configuration: %s"%name)
            service = SE(parent, "service", name=name, serviceType=serviceType, base=base, desc=desc)
            returnDict[name] = (True, isThreddsService, serviceType, base, isThreddsFileService)

        # Add the requires_authorization and application properties
        auth_required = DEFAULT_THREDDS_SERVICE_AUTH_REQUIRED[serviceType]
        if serviceAuthRequired is not None:
            auth_required = serviceAuthRequired.get(name, auth_required)
        reqAuth = SE(service, "property", name="requires_authorization", value=auth_required)

        apps = DEFAULT_THREDDS_SERVICE_APPLICATIONS[serviceType]
        if serviceApplications is not None:
            apps = serviceApplications.get(name, apps)

        for app in apps:
            appElem = SE(service, "property", name="application", value=app)

    return returnDict

def _genGeospatialCoverage(parent, variable):
    geospatialCoverage = SE(parent, "geospatialCoverage")
    if variable.northsouth_range is not None:
        northsouth = SE(geospatialCoverage, "northsouth")
        start, end, units = variable.northsouth_range.split(':')
        startElem = SE(northsouth, "start")
        startElem.text = start
        size = SE(northsouth, "size")
        size.text = str(float(end) - float(start))
        unitsElem = SE(northsouth, "units")
        unitsElem.text = units
    if variable.eastwest_range is not None:
        eastwest = SE(geospatialCoverage, "eastwest")
        start, end, units = variable.eastwest_range.split(':')
        startElem = SE(eastwest, "start")
        startElem.text = start
        size = SE(eastwest, "size")
        size.text = str(float(end) - float(start))
        unitsElem = SE(eastwest, "units")
        unitsElem.text = units
    if variable.updown_range is not None:
        updown = SE(geospatialCoverage, "updown")
        start, end, units = variable.updown_range.split(':')
        startElem = SE(updown, "start")
        startElem.text = start
        size = SE(updown, "size")
        size.text = str(float(end) - float(start))
        unitsElem = SE(updown, "units")
        unitsElem.text = units
    
    return geospatialCoverage

def _genTime(value, units, calendarTag):
    t = reltime(value, units)
    c = t.tocomp(tagToCalendar[calendarTag])
    result = "%04d-%02d-%02dT%02d:%02d:%02d"%(c.year, c.month, c.day, c.hour, c.minute, int(c.second))
    return result

def _genTimeCoverage(parent, start, end, resolution):
    timeCoverage = SE(parent, "timeCoverage")
    startElem = SE(timeCoverage, "start")
    startElem.text = start
    endElem = SE(timeCoverage, "end")
    endElem.text = end
    if resolution is not None:
        resolutionElem = SE(timeCoverage, "resolution")
        resolutionElem.text = resolution
    return timeCoverage

def _genVariable(parent, variable):
    variableElem = SE(parent, "variable", name=variable.short_name)
    if variable.standard_name is not None:
        variableElem.set("vocabulary_name", variable.standard_name)
    elif variable.long_name is not None:
        variableElem.set("vocabulary_name", variable.long_name)
    else:
        variableElem.set("vocabulary_name", variable.short_name)
    if variable.units is not None:
        variableElem.set("units", variable.units)
    else:
        variableElem.set("units", "None")
    variableElem.text = variable.long_name
    return variableElem

def _genFile(parent, path, size, ID, name, urlPath, serviceName, serviceDict):
    dataset = SE(parent, "dataset", ID=ID, name=name)
    # metadata = SE(dataset, "metadata")
    dataSize = SE(dataset, "dataSize", units="bytes")
    dataSize.text = str(size)

    serviceDesc = serviceDict[serviceName]
    if serviceDesc[0]:                  # Simple service
        isSimple, isThreddsService, serviceType, base, isThreddsFileService = serviceDesc
        if isThreddsService:
            publishPath = urlPath
        else:
            publishPath = path
        
        # For restrictAccess to work, the access info has to be in the dataset element!
        if isThreddsFileService:
            dataset.set("urlPath", publishPath)
            dataset.set("serviceName", serviceName)
        else:
            access = SE(dataset, "access", serviceName=serviceName, urlPath=publishPath)
    else:                               # Compound service
        isSimple, serviceList = serviceDesc
        for subName in serviceList:
            isSimple, isThreddsService, serviceType, base, isThreddsFileService = serviceDict[subName]
            if isThreddsService:
                publishPath = urlPath
            else:
                publishPath = path
            if isThreddsFileService:
                dataset.set("urlPath", publishPath)
                dataset.set("serviceName", subName)
            else:
                access = SE(dataset, "access", serviceName=subName, urlPath=publishPath)
            
    return dataset

def _genFileV2(parent, path, size, ID, name, urlPath, serviceName, serviceDict, fileid, trackingID, modTime, fileVersion, checksum, checksumType, variable=None):
    dataset = SE(parent, "dataset", ID=ID, name=name)

    fileIDProp = SE(dataset, "property", name="file_id", value=fileid)
    fileVersionProp = SE(dataset, "property", name="file_version", value=str(fileVersion))
    sizeProp = SE(dataset, "property", name="size", value=str(size))
    if trackingID is not None:
        trackingProp = SE(dataset, "property", name="tracking_id", value=trackingID)

    if modTime is not None:
        modtimeProp = SE(dataset, "property", name="mod_time", value=modTime)

    if checksum is not None:
        checksumProp = SE(dataset, "property", name="checksum", value=checksum)
        checksumTypeProp = SE(dataset, "property", name="checksum_type", value=checksumType)

    if variable is not None:
        perFileVariables = SE(dataset, "variables", vocabulary="CF-1.0")
        perFileVariable = _genVariable(perFileVariables, variable)
    dataSize = SE(dataset, "dataSize", units="bytes")
    dataSize.text = str(size)

    serviceDesc = serviceDict[serviceName]
    if serviceDesc[0]:                  # Simple service
        isSimple, isThreddsService, serviceType, base, isThreddsFileService = serviceDesc
        if isThreddsService:
            publishPath = urlPath
        else:
            publishPath = path

        # For restrictAccess to work, the access info has to be in the dataset element!
        if isThreddsFileService:
            dataset.set("urlPath", publishPath)
            dataset.set("serviceName", serviceName)
        else:
            access = SE(dataset, "access", serviceName=serviceName, urlPath=publishPath)
    else:                               # Compound service
        isSimple, serviceList = serviceDesc
        for subName in serviceList:
            isSimple, isThreddsService, serviceType, base, isThreddsFileService = serviceDict[subName]
            if isThreddsService:
                publishPath = urlPath
            else:
                publishPath = path
            if isThreddsFileService:
                dataset.set("urlPath", publishPath)
                dataset.set("serviceName", subName)
            else:
                access = SE(dataset, "access", serviceName=subName, urlPath=publishPath)
            
    return dataset

def _genDatasetRoots(parent, rootSpecs):
    for path, location in rootSpecs:
        datasetRoot = SE(parent, "datasetRoot", path=path, location=location)

def _genAggregations(parent, variable, variableID, handler, dataset, project, model, experiment, aggServiceName, aggdim_name):
    aggID = "%s.aggregation"%variableID
    try:
        aggName = handler.generateNameFromContext('variable_aggregation_dataset_name', project_description=project.description, model_description=model.description, experiment_description = experiment.description, variable=variable.short_name, variable_long_name=variable.long_name, variable_standard_name=variable.standard_name)
    except:
        aggName = aggID
    aggDataset = Element("dataset", name=aggName, ID=aggID, urlPath=aggID, serviceName=aggServiceName)
    nsmap = {
        None : "http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2"
        }
    netcdf = SE(aggDataset, "netcdf", nsmap=nsmap)
    aggElem = SE(netcdf, "aggregation", type="joinExisting", dimName=aggdim_name)

    # Sort filevars according to aggdim_first normalized to the dataset basetime
    filevars = []
    has_null_aggdim = False
    for filevar in variable.file_variables:
        if filevar.aggdim_first is None:
            has_null_aggdim = True
            break
        filevars.append((filevar, normTime(filevar, dataset.aggdim_units)))
    if has_null_aggdim:
        return
    filevars.sort(lambda x,y: cmp(x[1], y[1]))

    nvars = 0
    for filevar, aggdim_first in filevars:
        fvdomain = map(lambda x: (x.name, x.length, x.seq), filevar.dimensions)
        fvdomain.sort(lambda x,y: cmp(x[SEQ], y[SEQ]))
        if len(fvdomain)>0 and fvdomain[0][0]==aggdim_name:
            fileNetcdf = SE(aggElem, "netcdf", location=filevar.file.getLocation(), ncoords="%d"%fvdomain[0][1])
            nvars += 1

    # Create the aggregation if at least one filevar has the aggregate dimension
    if nvars>0:
        parent.append(aggDataset)

def _genAggregationsV2(parent, variable, variableID, handler, dataset, project, model, experiment, aggServiceName, aggdim_name, perVarMetadata):
    aggID = "%s.aggregation"%variableID
    try:
        aggName = handler.generateNameFromContext('variable_aggregation_dataset_name', project_description=project.description, model_description=model.description, experiment_description = experiment.description, variable=variable.short_name, variable_long_name=variable.long_name, variable_standard_name=variable.standard_name)
    except:
        aggName = aggID
    aggDataset = Element("dataset", name=aggName, ID=aggID, urlPath=aggID, serviceName=aggServiceName)
    aggIDProp = SE(aggDataset, "property", name="aggregation_id", value=aggID)
    perAggVariables = SE(aggDataset, "variables", vocabulary="CF-1.0")
    perAggVariable = _genVariable(perAggVariables, variable)
    aggDataset.append(perVarMetadata)
    nsmap = {
        None : "http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2"
        }
    netcdf = SE(aggDataset, "netcdf", nsmap=nsmap)
    aggElem = SE(netcdf, "aggregation", type="joinExisting", dimName=aggdim_name)

    # Sort filevars according to aggdim_first normalized to the dataset basetime
    filevars = []
    has_null_aggdim = False
    for filevar in variable.file_variables:
        if filevar.aggdim_first is None:
            has_null_aggdim = True
            break
        filevars.append((filevar, normTime(filevar, dataset.aggdim_units)))
    if has_null_aggdim:
        return
    filevars.sort(lambda x,y: cmp(x[1], y[1]))

    nvars = 0
    for filevar, aggdim_first in filevars:
        fvdomain = map(lambda x: (x.name, x.length, x.seq), filevar.dimensions)
        fvdomain.sort(lambda x,y: cmp(x[SEQ], y[SEQ]))
        if len(fvdomain)>0 and fvdomain[0][0]==aggdim_name:
            fileNetcdf = SE(aggElem, "netcdf", location=filevar.file.getLocation(), ncoords="%d"%fvdomain[0][1])
            nvars += 1

    # Create the aggregation if at least one filevar has the aggregate dimension
    if nvars>0:
        parent.append(aggDataset)

def _genSubAggregation(parent, aggID, aggName, aggServiceName, aggdim_name, fvlist, flag, las_time_delta, calendar, start):
    aggDataset = Element("dataset", name=aggName, ID=aggID, urlPath=aggID, serviceName=aggServiceName)
    if flag==EVEN:
        timeDeltaProperty = SE(aggDataset, "property", name="time_delta", value=las_time_delta)
        calendarProperty = SE(aggDataset, "property", name="calendar", value=calendar)
        startProperty = SE(aggDataset, "property", name="start", value=repr(start))
    nsmap = {
        None : "http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2"
        }
    netcdf = SE(aggDataset, "netcdf", nsmap=nsmap)
    aggElem = SE(netcdf, "aggregation", type="joinExisting", dimName=aggdim_name)
    for filevar, aggfirst, agglast, units, ncoords in fvlist:
        fileNetcdf = SE(aggElem, "netcdf", location=filevar.file.getLocation(), ncoords="%d"%ncoords)
    parent.append(aggDataset)    

def _genLASAggregations(parent, variable, variableID, handler, dataset, project, model, experiment, aggServiceName, aggdim_name, lasTimeDelta):

    # Generate the top-level aggregation
    aggID = "%s.aggregation"%variableID
    try:
        aggName = handler.generateNameFromContext('variable_aggregation_dataset_name', project_description=project.description, model_description=model.description, experiment_description = experiment.description, variable=variable.short_name, variable_long_name=variable.long_name, variable_standard_name=variable.standard_name)
    except:
        aggName = aggID
    aggDataset = Element("dataset", name=aggName, ID=aggID)

    # Sort filevars according to aggdim_first normalized to the dataset basetime
    filevars = []
    has_null_aggdim = False
    for filevar in variable.file_variables:
        if filevar.aggdim_first is None:
            has_null_aggdim = True
            break
        r2, s2 = normTime_2(filevar, dataset.aggdim_units, dataset.calendar)
        filevars.append((filevar, r2, s2))
    if has_null_aggdim:
        return                          # No aggregation added
    filevars.sort(lambda x,y: cmp(x[1], y[1]))

    # Add aggregation dimension coordinate length to filevars list
    ntot = 0
    nfvars = 0
    fvlist = []
    for filevar, aggfirst, agglast in filevars:
        fvdomain = map(lambda x: (x.name, x.length, x.seq), filevar.dimensions)
        fvdomain.sort(lambda x,y: cmp(x[SEQ], y[SEQ]))
        if len(fvdomain)>0 and fvdomain[0][0]==dataset.aggdim_name:
            ncoords = fvdomain[0][1]
            ntot += ncoords
            fvlist.append((filevar, aggfirst, agglast, dataset.aggdim_units, ncoords))
            nfvars += 1

    # If no file variables have the aggregate dimension, don't create an aggregate
    if nfvars>0:
        parent.append(aggDataset)
    else:
        return

    # Check if the aggregation as a whole is evenly spaced, based on las_time_delta.
    iseven, first, last, est = checkTimes(filevars[0][1], filevars[-1][2], dataset.aggdim_units, dataset.calendar, lasTimeDelta, ntot)

    # If so, just generate one subaggregation
    if iseven:
        subAggID = "%s.%d"%(aggID, 1)
        subAggName = "%s - Subset %d"%(aggName, 1)
        _genSubAggregation(aggDataset, subAggID, subAggName, aggServiceName, aggdim_name, fvlist, EVEN, lasTimeDelta, dataset.calendar, first)

    # Split the aggregation so that each piece is either evenly spaced or not.
    else:
        chunks = splitTimes(fvlist, dataset.calendar, lasTimeDelta)

        # For each subaggregation generate a dataset.
        nid = 1
        for start, stop, flag, nchunk, fa, la, le in chunks:
            subAggID = "%s.%d"%(aggID, nid)
            subAggName = "%s - Subset %d"%(aggName, nid)
            _genSubAggregation(aggDataset, subAggID, subAggName, aggServiceName, aggdim_name, fvlist[start:stop], flag, lasTimeDelta, dataset.calendar, fa)
            nid += 1
            
def normTime(filevar, tounits):
    try:
        r = reltime(filevar.aggdim_first, filevar.aggdim_units)
    except:
        print filevar
        raise
    r2 = r.torel(tounits)
    return r2.value

def normTime_2(filevar, tounits, calendarTag):
    calendar = tagToCalendar[calendarTag]
    try:
        r = reltime(filevar.aggdim_first, filevar.aggdim_units)
        s = reltime(filevar.aggdim_last, filevar.aggdim_units)
    except:
        print filevar
        raise
    r2 = r.torel(tounits, calendar)
    s2 = s.torel(tounits, calendar)
    return r2.value, s2.value

def _genPerVariableDatasets(parent, dataset, datasetName, resolution, filesRootLoc, filesRootPath, datasetRootDict, excludeVariables, offline, serviceName, serviceDict, aggServiceName, handler, project, model, experiment, las_configure, las_time_delta):
    aggdim_name = dataset.aggdim_name
    shortNames = {}
    for variable in dataset.variables:
        # It is possible for a dataset to have different variables with the same name,
        # for example if the number of levels is different in one file than another.
        # Ensure that IDs are unique
        if variable.short_name in excludeVariables:
            continue
        if shortNames.has_key(variable.short_name):
            uniqueName = "%s_%d"%(variable.short_name, shortNames[variable.short_name])
            shortNames[variable.short_name] += 1
        else:
            uniqueName = variable.short_name
            shortNames[variable.short_name] = 1
        variableID = "%s.%s"%(datasetName, uniqueName)
        try:
            variableName = handler.generateNameFromContext('variable_dataset_name', project_description=project.description, model_description=model.description, experiment_description=experiment.description, variable=variable.short_name, variable_long_name=variable.long_name, variable_standard_name=variable.standard_name)
        except:
            variableName = variableID
        perVarDataset = SE(parent, "dataset", name=variableName, ID=variableID)
        perVarMetadata = SE(perVarDataset, "metadata", inherited="true")
        perVarVariables = SE(perVarMetadata, "variables", vocabulary="CF-1.0")
        perVarVariable = _genVariable(perVarVariables, variable)
        perVarMetadata2 = SE(perVarDataset, "metadata")
        geoCoverage = _genGeospatialCoverage(perVarMetadata2, variable)
        if variable.aggdim_first is not None:
            timeFirst = _genTime(variable.aggdim_first, dataset.aggdim_units, dataset.calendar)
            timeLast = _genTime(variable.aggdim_last, dataset.aggdim_units, dataset.calendar)
            timeCoverage = _genTimeCoverage(perVarMetadata2, timeFirst, timeLast, resolution)

        # Files
        filelist = [(filevar.file.getLocation(), filevar.file.getSize()) for filevar in variable.file_variables]
        filesID = "%s.files"%variableID
        try:
            filesName = handler.generateNameFromContext('variable_files_dataset_name', project_description=project.description, model_description=model.description, experiment_description=experiment.description, variable=variable.short_name, variable_long_name=variable.long_name, variable_standard_name=variable.standard_name)
        except Exception, e:
            filesName = filesID
        filesDataset = SE(perVarDataset, "dataset", name=filesName, ID=filesID)
        hasThreddsServ = hasThreddsService(serviceName, serviceDict)
        for path, size in filelist:

            basename = os.path.basename(path)
            fileid = "%s.%s"%(filesID, basename)

            # There only needs to be an associated Thredds rootpath if at least
            # one associated service is a Thredds service
            if hasThreddsServ:
                # Sanity check: are all the dataset files under the same rootpath?
                rootpath, rootloc = _getRootPathAndLoc(filevar.file, datasetRootDict)
                if rootpath is None:
                    raise ESGPublishError("File %s is not contained in any THREDDS root path. Please add an entry to thredds_dataset_roots in the configuration file."%path)
                if rootpath!=filesRootPath:
                    warning('rootpath=%s does not match dataset root path=%s'%(rootpath, filesRootPath))

                rootIndex = path.find(filesRootLoc)
                if rootIndex==0:
                    urlpath = path.replace(filesRootLoc, filesRootPath, 1)
                else:
                    warning('File %s is not in a dataset root. Add an entry to thredds_dataset_roots with a directory containing this file'%path)
                    urlpath = path
            else:
                urlpath = path

            urlpath = os.path.normpath(urlpath)
            path = os.path.normpath(path)
            fileDataset = _genFile(filesDataset, path, size, fileid, basename, urlpath, serviceName, serviceDict)

        # Aggregation
        # Don't generate an aggregation if the variable has time overlaps or a non-monotonic aggregate dimension,
        # or the dataset does not have an aggregate dimension
        if variable.has_errors or dataset.aggdim_units is None:
            continue
        if las_configure:
            _genLASAggregations(perVarDataset, variable, variableID, handler, dataset, project, model, experiment, aggServiceName, aggdim_name, las_time_delta)
        else:
            _genAggregations(perVarDataset, variable, variableID, handler, dataset, project, model, experiment, aggServiceName, aggdim_name)

def _genPerTimeDatasets(parent, dataset, datasetName, filesRootLoc, filesRootPath, datasetRootDict, excludeVariables, offline, serviceName, serviceDict, handler, project, model, experiment):
    filelist = [(file.getLocation(), file.getSize()) for file in dataset.getFiles()]
    filesID = "%s.files"%datasetName
    try:
        filesName = handler.generateNameFromContext('per_time_files_dataset_name', project_description=project.description, model_description=model.description, experiment_description=experiment.description)
    except Exception, e:
        filesName = filesID
    filesDataset = SE(parent, "dataset", name=filesName, ID=filesID)
    hasThreddsServ = hasThreddsService(serviceName, serviceDict)
    for path, size in filelist:
        basename = os.path.basename(path)
        fileid = "%s.%s"%(filesID, basename)
        if hasThreddsServ:
            rootIndex = path.find(filesRootLoc)
            if rootIndex==0:
                urlpath = path.replace(filesRootLoc, filesRootPath, 1)
            else:
                warning('File %s is not in a dataset root. Add an entry to thredds_dataset_roots with a directory containing this file'%path)
                urlpath = path
        else:
            urlpath = path
        urlpath = os.path.normpath(urlpath)
        path = os.path.normpath(path)
        fileDataset = _genFile(filesDataset, path, size, fileid, basename, urlpath, serviceName, serviceDict)

def _genPerVariableDatasetsV2(parent, dataset, datasetName, resolution, filesRootLoc, filesRootPath, datasetRootDict, excludeVariables, offline, serviceName, serviceDict, aggServiceName, handler, project, model, experiment, las_configure, las_time_delta):
    aggdim_name = dataset.aggdim_name
    shortNames = {}
    for variable in dataset.variables:
        # It is possible for a dataset to have different variables with the same name,
        # for example if the number of levels is different in one file than another.
        # Ensure that IDs are unique
        if variable.short_name in excludeVariables:
            continue
        if shortNames.has_key(variable.short_name):
            uniqueName = "%s_%d"%(variable.short_name, shortNames[variable.short_name])
            shortNames[variable.short_name] += 1
        else:
            uniqueName = variable.short_name
            shortNames[variable.short_name] = 1
        variableID = "%s.%s"%(datasetName, uniqueName)
        try:
            variableName = handler.generateNameFromContext('variable_dataset_name', project_description=project.description, model_description=model.description, experiment_description=experiment.description, variable=variable.short_name, variable_long_name=variable.long_name, variable_standard_name=variable.standard_name)
        except:
            variableName = variableID

        perVarMetadata = Element("metadata", inherited="true")
        geoCoverage = _genGeospatialCoverage(perVarMetadata, variable)
        if variable.aggdim_first is not None:
            timeFirst = _genTime(variable.aggdim_first, dataset.aggdim_units, dataset.calendar)
            timeLast = _genTime(variable.aggdim_last, dataset.aggdim_units, dataset.calendar)
            timeCoverage = _genTimeCoverage(perVarMetadata, timeFirst, timeLast, resolution)

        # Files
        filelist = [(filevar.file.getLocation(), filevar.file.getSize(), filevar.file) for filevar in variable.file_variables]
        filesID = variableID
        try:
            filesName = handler.generateNameFromContext('variable_files_dataset_name', project_description=project.description, model_description=model.description, experiment_description=experiment.description, variable=variable.short_name, variable_long_name=variable.long_name, variable_standard_name=variable.standard_name)
        except Exception, e:
            filesName = filesID
        hasThreddsServ = hasThreddsService(serviceName, serviceDict)
        for path, size, fileobj in filelist:

            basename = os.path.basename(path)
            fileid = "%s.%s"%(datasetName, fileobj.base)
            fileVersion = fileobj.getVersion()
            fileVersionID = "%s.%s.v%d"%(datasetName, fileobj.base, fileVersion)

            # There only needs to be an associated Thredds rootpath if at least
            # one associated service is a Thredds service
            if hasThreddsServ:
                # Sanity check: are all the dataset files under the same rootpath?
                rootpath, rootloc = _getRootPathAndLoc(filevar.file, datasetRootDict)
                if rootpath is None:
                    raise ESGPublishError("File %s is not contained in any THREDDS root path. Please add an entry to thredds_dataset_roots in the configuration file."%path)
                if rootpath!=filesRootPath:
                    warning('rootpath=%s does not match dataset root path=%s'%(rootpath, filesRootPath))

                rootIndex = path.find(filesRootLoc)
                if rootIndex==0:
                    urlpath = path.replace(filesRootLoc, filesRootPath, 1)
                else:
                    warning('File %s is not in a dataset root. Add an entry to thredds_dataset_roots with a directory containing this file'%path)
                    urlpath = path
            else:
                urlpath = path

            urlpath = os.path.normpath(urlpath)
            path = os.path.normpath(path)
            trackingID = fileobj.versions[-1].tracking_id
            modTime = fileobj.getModificationFtime()
            checksum = fileobj.getChecksum()
            checksumType = fileobj.getChecksumType()
            fileDataset = _genFileV2(parent, path, size, fileVersionID, basename, urlpath, serviceName, serviceDict, fileid, trackingID, modTime, fileVersion, checksum, checksumType, variable=variable)

        # Aggregation
        # Don't generate an aggregation if the variable has time overlaps or a non-monotonic aggregate dimension,
        # or the dataset does not have an aggregate dimension
        if variable.has_errors or dataset.aggdim_units is None:
            continue
        if las_configure:
            _genLASAggregations(perVarDataset, variable, variableID, handler, dataset, project, model, experiment, aggServiceName, aggdim_name, las_time_delta)
        else:
            _genAggregationsV2(parent, variable, variableID, handler, dataset, project, model, experiment, aggServiceName, aggdim_name, perVarMetadata)

def _genPerTimeDatasetsV2(parent, dataset, datasetName, filesRootLoc, filesRootPath, datasetRootDict, excludeVariables, offline, serviceName, serviceDict, handler, project, model, experiment):
    filelist = [(fileobj.getLocation(), fileobj.getSize(), fileobj) for fileobj in dataset.getFiles()]
    filesID = datasetName
    try:
        filesName = handler.generateNameFromContext('per_time_files_dataset_name', project_description=project.description, model_description=model.description, experiment_description=experiment.description)
    except Exception, e:
        filesName = filesID
##     filesDataset = SE(parent, "dataset", name=filesName, ID=filesID)
    hasThreddsServ = hasThreddsService(serviceName, serviceDict)
    for path, size, fileobj in filelist:
        basename = os.path.basename(path)
        fileid = "%s.%s"%(filesID, basename)
        if hasThreddsServ:
            rootIndex = path.find(filesRootLoc)
            if rootIndex==0:
                urlpath = path.replace(filesRootLoc, filesRootPath, 1)
            else:
                warning('File %s is not in a dataset root. Add an entry to thredds_dataset_roots with a directory containing this file'%path)
                urlpath = path
        else:
            urlpath = path
        urlpath = os.path.normpath(urlpath)
        path = os.path.normpath(path)
        trackingID = fileobj.getTrackingID()
        modTime = fileobj.getModificationFtime()
        fileVersion = fileobj.getVersion()
        checksum = fileobj.getChecksum()
        checksumType = fileobj.getChecksumType()
        fileDataset = _genFileV2(parent, path, size, fileid, basename, urlpath, serviceName, serviceDict, fileid, trackingID, modTime, fileVersion, checksum, checksumType)

def generateThredds(datasetName, dbSession, outputFile, handler, datasetInstance=None, genRoot=False, service=None, perVariable=None):
    """
    Generate THREDDS Data Server configuration file.

    datasetName
      String dataset identifier.

    dbSession
      A database Session.

    outputFile
      Open file instance.

    handler
      Project handler

    datasetInstance
      Existing dataset instance. If not provided, the instance is regenerated from the database using the datasetName.

    genRoot
      Boolean, if True then generate a datasetRoot element. The default is False since duplicate datasetRoot elements
      cause a THREDDS error on reinitialization.

    service
      String service name. If omitted, the first online/offline service in the configuration is used.

    perVariable
      Boolean, overrides ``variable_per_file'' config option.

    """

    session = dbSession()
    info("Writing THREDDS catalog %s"%outputFile.name)

    # Lookup the dataset
    if datasetInstance is None:
        dset = session.query(Dataset).filter_by(name=datasetName).first()
    else:
        dset = datasetInstance
        # session.save_or_update(dset)
        session.add(dset)
    if dset is None:
        raise ESGPublishError("Dataset not found: %s"%datasetName)

    # Clear THREDDS errors from dataset_status
    dset.clear_warnings(session, THREDDS_MODULE)

    # Update the handler from the database. This ensures that the handler context is in sync
    # with the dataset.
    context = handler.getContextFromDataset(dset)

    # Lookup the related objects
    project = session.query(Project).filter_by(name=dset.project).first()
    model = session.query(Model).filter_by(name=dset.model, project=dset.project).first()
    experiment = session.query(Experiment).filter_by(name=dset.experiment, project=dset.project).first()

    # Get configuration options
    config = getConfig()
    if config is None:
        raise ESGPublishError("No configuration file found.")
    section = 'project:%s'%dset.project

    catalog_version = config.get('DEFAULT', 'thredds_catalog_version', default=DEFAULT_THREDDS_CATALOG_VERSION)

    if catalog_version=="1":
        _generateThreddsV1(datasetName, outputFile, handler, session, dset, context, project, model, experiment, config, section, genRoot=genRoot, service=service, perVariable=perVariable)
    elif catalog_version=="2":
        _generateThreddsV2(datasetName, outputFile, handler, session, dset, context, project, model, experiment, config, section, genRoot=genRoot, service=service, perVariable=perVariable)
    else:
        raise ESGPublishError("Invalid catalog version: %s"%catalog_version)

    session.commit()
    session.close()

def _generateThreddsV1(datasetName, outputFile, handler, session, dset, context, project, model, experiment, config, section, genRoot=False, service=None, perVariable=None):

    global _nsmap, _XSI

    offline = dset.offline
    threddsAggregationSpecs = getThreddsServiceSpecs(config, section, 'thredds_aggregation_services')
    threddsFileSpecs = getThreddsServiceSpecs(config, section, 'thredds_file_services')
    threddsOfflineSpecs = getThreddsServiceSpecs(config, section, 'thredds_offline_services')
    threddsRestrictAccess = config.get(section, 'thredds_restrict_access')
    threddsDatasetRootsOption = config.get('DEFAULT', 'thredds_dataset_roots')
    threddsDatasetRootsSpecs = splitRecord(threddsDatasetRootsOption)
    excludeVariables = splitLine(config.get(section, 'thredds_exclude_variables', ''), sep=',')
    if not offline:
        if perVariable is None:
            perVariable = config.getboolean(section, 'variable_per_file', False)
    else:
        perVariable = False
    lasConfigure = config.getboolean(section, 'las_configure', False)
    if lasConfigure:
        lasTimeDelta = handler.generateNameFromContext('las_time_delta')
    else:
        lasTimeDelta = None
    resolution = handler.getResolution()
    description = handler.getField('description')
    rights = handler.getField('rights')
    creator = handler.getField('creator')
    publisher = handler.getField('publisher')

    catalog = Element("catalog", name="TDS configuration file", nsmap=_nsmap)
    catalog.set(_XSI+"schemaLocation", "%s http://www.unidata.ucar.edu/schemas/thredds/InvCatalog.1.0.2.xsd"%_nsmap[None])
    doc = ElementTree(catalog)

    serviceDict = _genService(catalog, threddsAggregationSpecs)
    serviceDict = _genService(catalog, threddsFileSpecs, initDictionary=serviceDict)
    if len(threddsOfflineSpecs)>0:
        serviceDict = _genService(catalog, threddsOfflineSpecs, initDictionary=serviceDict)
    else:
        info("No offline services specified (option=thredds_offline_services).")
    
    if project is None or experiment is None or model is None:
        datasetDesc = datasetName
    else:

        # First try generating the description from the existing context
        try:
            datasetDesc = handler.generateNameFromContext('dataset_name_format', project_description=project.description, model_description=model.description, experiment_description = experiment.description)
        except:

            # Maybe the database values are screwy, just get the dataset_name fields
            try:
                context = handler.parseDatasetName(datasetName, context)
                datasetDesc = handler.generateNameFromContext('dataset_name_format', **context)
            except:

                # OK, give up
                datasetDesc = datasetName
                
    datasetElem = SE(catalog, "dataset", name=datasetDesc, ID=datasetName, restrictAccess=threddsRestrictAccess)

    for name in handler.getFieldNames():
        if handler.isThreddsProperty(name):
            try:
                property = SE(datasetElem, "property", name=name, value=handler.getField(name))
            except TypeError:
                raise ESGPublishError("Invalid value for field %s: %s"%(name, handler.getField(name)))

    if description!='':
        documentation = SE(datasetElem, "documentation", type="summary")
        documentation.text = description

    if rights not in [None, '']:
        doc_rights = SE(datasetElem, "documentation", type="rights")
        doc_rights.text = rights

    if creator!='' and handler.validMaps.has_key('creator'):
        creator_email, creator_url = handler.validMaps['creator'].get(creator)
        if creator_email is None:
            creator_email = ''
        if creator_url is None:
            creator_url = ''
        creatorElem  = SE(datasetElem, "creator")
        creatorName = SE(creatorElem, "name")
        creatorName.text = creator
        creatorContact = SE(creatorElem, "contact", email=creator_email, url=creator_url)
        
    if publisher!='' and handler.validMaps.has_key('publisher'):
        publisher_contact, publisher_url = handler.validMaps['publisher'].get(publisher)
        if publisher_contact is None:
            publisher_contact = ''
        if publisher_url is None:
            publisher_url = ''
        publisherElem  = SE(datasetElem, "publisher")
        publisherName = SE(publisherElem, "name")
        publisherName.text = publisher
        publisherContact = SE(publisherElem, "contact", email=publisher_contact, url=publisher_url)
        
    if not offline:
        if perVariable:
            metadata1 = SE(datasetElem, "metadata")
        else:
            metadata1 = SE(datasetElem, "metadata", inherited="true")
        variables = SE(metadata1, "variables", vocabulary="CF-1.0")
        shortNames = {}
        for variable in dset.variables:
            if variable.short_name not in excludeVariables:
                # It is possible for a dataset to have different variables with the same name,
                # for example if the number of levels is different in one file than another.
                # Only list a variable name once in the <variables> element.
                if shortNames.has_key(variable.short_name):
                    continue
                shortNames[variable.short_name] = 1
                variableElem = _genVariable(variables, variable)

    metadata2 = SE(datasetElem, "metadata", inherited="true")
##     geospatialCoverage = SE(metadata2, "geospatialCoverage")
##     coverageName = SE(geospatialCoverage, "name", vocabulary="Thredds")
##     coverageName.text = "global"
    dataType = SE(metadata2, "dataType")
    dataType.text = "Grid"
    dataFormat = SE(metadata2, "dataFormat")
    dataFormat.text = "NetCDF"

    if service is not None:
        serviceName = service
    elif not offline:                   # Choose the first service configured if not specified
        serviceName = threddsFileSpecs[0][2]
    else:
        serviceName = threddsOfflineSpecs[0][2]
    aggServiceName = threddsAggregationSpecs[0][2]

    datasetRootDict = {}                # {'abc_path':['a','b','c'], 'def_path':['d','e','f']}
    for rootPath, rootLoc in threddsDatasetRootsSpecs:
        fields = rootLoc.split(os.sep)
        if fields[0]=='':
            del fields[0]
        if fields[-1]=='':
            del fields[-1]
        datasetRootDict[rootPath] = fields

    # Get the rootPath for the dataset. rootPath is the 'shorthand' for the dataset's root directory
    filesRootPath, filesRootLoc = _getRootPathAndLoc(dset.getFiles()[0], datasetRootDict)
    hasThreddsServ = hasThreddsService(serviceName, serviceDict)
    if hasThreddsServ and filesRootPath is None:
        raise ESGPublishError("File %s is not contained in any THREDDS root path. Please add an entry to thredds_dataset_roots in the configuration file."%dset.getFiles()[0].getLocation())

    # Save the rootLoc with the dataset catalog. When the full THREDDS catalog is written,
    # the rootpath is checked against the thredds_dataset_roots entries.
    catalogObj = session.query(Catalog).filter_by(dataset_name=datasetName).first()
    catalogObj.rootpath = filesRootPath

    if perVariable:
        # Per-variable datasets
        _genPerVariableDatasets(datasetElem, dset, datasetName, resolution, filesRootLoc, filesRootPath, datasetRootDict, excludeVariables, offline, serviceName, serviceDict, aggServiceName, handler, project, model, experiment, lasConfigure, lasTimeDelta)
    else:
        # Per-time datasets
        _genPerTimeDatasets(datasetElem, dset, datasetName, filesRootLoc, filesRootPath, datasetRootDict, excludeVariables, offline, serviceName, serviceDict, handler, project, model, experiment)

    doc.write(outputFile, xml_declaration=True, encoding='UTF-8', pretty_print=True)
    event = Event(dset.name, dset.getVersion(), WRITE_THREDDS_CATALOG_EVENT)
    dset.events.append(event)

def _generateThreddsV2(datasetName, outputFile, handler, session, dset, context, project, model, experiment, config, section, genRoot=False, service=None, perVariable=None):

    global _nsmap, _XSI
    CATALOG_VERSION = "2"

    offline = dset.offline
    threddsAggregationSpecs = getThreddsServiceSpecs(config, section, 'thredds_aggregation_services')
    threddsFileSpecs = getThreddsServiceSpecs(config, section, 'thredds_file_services')
    threddsOfflineSpecs = getThreddsServiceSpecs(config, section, 'thredds_offline_services')
    threddsRestrictAccess = config.get(section, 'thredds_restrict_access')
    threddsDatasetRootsOption = config.get('DEFAULT', 'thredds_dataset_roots')
    threddsDatasetRootsSpecs = splitRecord(threddsDatasetRootsOption)
    threddsServiceApplicationSpecs = getThreddsAuxiliaryServiceSpecs(config, section, 'thredds_service_applications', multiValue=True)
    threddsServiceAuthRequiredSpecs = getThreddsAuxiliaryServiceSpecs(config, section, 'thredds_service_auth_required')
    threddsServiceDescriptionSpecs = getThreddsAuxiliaryServiceSpecs(config, section, 'thredds_service_descriptions')
    excludeVariables = splitLine(config.get(section, 'thredds_exclude_variables', ''), sep=',')
    if not offline:
        if perVariable is None:
            perVariable = config.getboolean(section, 'variable_per_file', False)
    else:
        perVariable = False
    lasConfigure = config.getboolean(section, 'las_configure', False)
    if lasConfigure:
        lasTimeDelta = handler.generateNameFromContext('las_time_delta')
    else:
        lasTimeDelta = None
    resolution = handler.getResolution()
    description = handler.getField('description')
    rights = handler.getField('rights')
    creator = handler.getField('creator')
    publisher = handler.getField('publisher')

    catalog = Element("catalog", name="TDS configuration file", nsmap=_nsmap)
    catalog.set(_XSI+"schemaLocation", "%s http://www.unidata.ucar.edu/schemas/thredds/InvCatalog.1.0.2.xsd"%_nsmap[None])
    doc = ElementTree(catalog)

    serviceDict = _genService(catalog, threddsAggregationSpecs, serviceApplications=threddsServiceApplicationSpecs, serviceAuthRequired=threddsServiceAuthRequiredSpecs, serviceDescriptions=threddsServiceDescriptionSpecs)
    serviceDict = _genService(catalog, threddsFileSpecs, initDictionary=serviceDict, serviceApplications=threddsServiceApplicationSpecs, serviceAuthRequired=threddsServiceAuthRequiredSpecs, serviceDescriptions=threddsServiceDescriptionSpecs)
    if len(threddsOfflineSpecs)>0:
        serviceDict = _genService(catalog, threddsOfflineSpecs, initDictionary=serviceDict, serviceApplications=threddsServiceApplicationSpecs, serviceAuthRequired=threddsServiceAuthRequiredSpecs, serviceDescriptions=threddsServiceDescriptionSpecs)
    else:
        info("No offline services specified (option=thredds_offline_services).")
    
    catalogVersionProp = SE(catalog, "property", name="catalog_version", value=CATALOG_VERSION)

    if project is None or experiment is None or model is None:
        datasetDesc = datasetName
    else:

        # First try generating the description from the existing context
        try:
            datasetDesc = handler.generateNameFromContext('dataset_name_format', project_description=project.description, model_description=model.description, experiment_description = experiment.description)
        except:

            # Maybe the database values are screwy, just get the dataset_name fields
            try:
                context = handler.parseDatasetName(datasetName, context)
                datasetDesc = handler.generateNameFromContext('dataset_name_format', **context)
            except:

                # OK, give up
                datasetDesc = datasetName
                
    dsetVersion = dset.getVersion()
    dsetVersionID = "%s.v%d"%(datasetName, dsetVersion)
    datasetElem = SE(catalog, "dataset", name=datasetDesc, ID=dsetVersionID, restrictAccess=threddsRestrictAccess)

    datasetIdProp = SE(datasetElem, "property", name="dataset_id", value=datasetName)
    datasetVersionProp = SE(datasetElem, "property", name="dataset_version", value=str(dsetVersion))

    if dset.master_gateway is not None:
        SE(datasetElem, "property", name="master_gateway", value=dset.master_gateway)

    for name in handler.getFieldNames():
        if handler.isThreddsProperty(name):
            try:
                property = SE(datasetElem, "property", name=name, value=handler.getField(name))
            except TypeError:
                raise ESGPublishError("Invalid value for field %s: %s"%(name, handler.getField(name)))

    if description!='':
        documentation = SE(datasetElem, "documentation", type="summary")
        documentation.text = description

    if rights not in [None, '']:
        doc_rights = SE(datasetElem, "documentation", type="rights")
        doc_rights.text = rights

    if creator!='' and handler.validMaps.has_key('creator'):
        creator_email, creator_url = handler.validMaps['creator'].get(creator)
        if creator_email is None:
            creator_email = ''
        if creator_url is None:
            creator_url = ''
        creatorElem  = SE(datasetElem, "creator")
        creatorName = SE(creatorElem, "name")
        creatorName.text = creator
        creatorContact = SE(creatorElem, "contact", email=creator_email, url=creator_url)
        
    if publisher!='' and handler.validMaps.has_key('publisher'):
        publisher_contact, publisher_url = handler.validMaps['publisher'].get(publisher)
        if publisher_contact is None:
            publisher_contact = ''
        if publisher_url is None:
            publisher_url = ''
        publisherElem  = SE(datasetElem, "publisher")
        publisherName = SE(publisherElem, "name")
        publisherName.text = publisher
        publisherContact = SE(publisherElem, "contact", email=publisher_contact, url=publisher_url)
        
    if not offline:
        if perVariable:
            metadata1 = SE(datasetElem, "metadata")
        else:
            metadata1 = SE(datasetElem, "metadata", inherited="true")
        variables = SE(metadata1, "variables", vocabulary="CF-1.0")
        shortNames = {}
        for variable in dset.variables:
            if variable.short_name not in excludeVariables:
                # It is possible for a dataset to have different variables with the same name,
                # for example if the number of levels is different in one file than another.
                # Only list a variable name once in the <variables> element.
                if shortNames.has_key(variable.short_name):
                    continue
                shortNames[variable.short_name] = 1
                variableElem = _genVariable(variables, variable)

    metadata2 = SE(datasetElem, "metadata", inherited="true")
##     geospatialCoverage = SE(metadata2, "geospatialCoverage")
##     coverageName = SE(geospatialCoverage, "name", vocabulary="Thredds")
##     coverageName.text = "global"
    dataType = SE(metadata2, "dataType")
    dataType.text = "Grid"
    dataFormat = SE(metadata2, "dataFormat")
    dataFormat.text = "NetCDF"

    if service is not None:
        serviceName = service
    elif not offline:                   # Choose the first service configured if not specified
        serviceName = threddsFileSpecs[0][2]
    else:
        serviceName = threddsOfflineSpecs[0][2]
    aggServiceName = threddsAggregationSpecs[0][2]

    datasetRootDict = {}                # {'abc_path':['a','b','c'], 'def_path':['d','e','f']}
    for rootPath, rootLoc in threddsDatasetRootsSpecs:
        fields = rootLoc.split(os.sep)
        if fields[0]=='':
            del fields[0]
        if fields[-1]=='':
            del fields[-1]
        datasetRootDict[rootPath] = fields

    # Get the rootPath for the dataset. rootPath is the 'shorthand' for the dataset's root directory
    filelist = dset.getFiles()
    if len(filelist)==0:
        raise ESGPublishError("Dataset %s does not contain any files, cannot publish"%dset.name)
    filesRootPath, filesRootLoc = _getRootPathAndLoc(dset.getFiles()[0], datasetRootDict)
    hasThreddsServ = hasThreddsService(serviceName, serviceDict)
    if hasThreddsServ and filesRootPath is None:
        raise ESGPublishError("File %s is not contained in any THREDDS root path. Please add an entry to thredds_dataset_roots in the configuration file."%dset.getFiles()[0].getLocation())

    # Save the rootLoc with the dataset catalog. When the full THREDDS catalog is written,
    # the rootpath is checked against the thredds_dataset_roots entries.
    catalogObj = session.query(Catalog).filter_by(dataset_name=datasetName).first()
    catalogObj.rootpath = filesRootPath

    if perVariable:
        # Per-variable datasets
        _genPerVariableDatasetsV2(datasetElem, dset, datasetName, resolution, filesRootLoc, filesRootPath, datasetRootDict, excludeVariables, offline, serviceName, serviceDict, aggServiceName, handler, project, model, experiment, lasConfigure, lasTimeDelta)
    else:
        # Per-time datasets
        _genPerTimeDatasetsV2(datasetElem, dset, datasetName, filesRootLoc, filesRootPath, datasetRootDict, excludeVariables, offline, serviceName, serviceDict, handler, project, model, experiment)

    doc.write(outputFile, xml_declaration=True, encoding='UTF-8', pretty_print=True)
    event = Event(dset.name, dset.getVersion(), WRITE_THREDDS_CATALOG_EVENT)
    dset.events.append(event)

def readThreddsWithAuthentication(url, config):
    """
    Read a protected page from the THREDDS Data Server.

    Returns the THREDDS page as a string.

    url
      String URL to read.

    config
      Configuration file object.
    
    """

    threddsAuthenticationRealm = config.get('DEFAULT', 'thredds_authentication_realm')
    threddsUsername = config.get('DEFAULT', 'thredds_username')
    threddsPassword = config.get('DEFAULT', 'thredds_password')

    # Create an OpenerDirector with support for Basic HTTP Authentication...
    auth_handler = urllib2.HTTPBasicAuthHandler()
    auth_handler.add_password(realm=threddsAuthenticationRealm,
                              uri=url,
                              user=threddsUsername,
                              passwd=threddsPassword)
    opener = urllib2.build_opener(auth_handler)
    
    # ...and install it globally so it can be used with urlopen.
    urllib2.install_opener(opener)
    handle = urllib2.urlopen(url)

    page = handle.read()
    handle.close()
    return page
    
def reinitializeThredds():
    """
    Reinitialize the THREDDS Data Server. This forces the catalogs to be reread.

    Returns the string contents of the error log associated with this reinitialization.
    
    """
    config = getConfig()
    if config is None:
        raise ESGPublishError("No configuration file found.")

    threddsReinitUrl = config.get('DEFAULT', 'thredds_reinit_url')
    threddsReinitSuccessPattern = config.get('DEFAULT', 'thredds_reinit_success_pattern')
    threddsReinitErrorUrl = config.get('DEFAULT', 'thredds_reinit_error_url')
    threddsErrorPattern = config.get('DEFAULT', 'thredds_error_pattern')
    threddsFatalErrorPattern = config.get('DEFAULT', 'thredds_fatal_error_pattern')
    info("Reinitializing THREDDS server")

    try:
        reinitResult = readThreddsWithAuthentication(threddsReinitUrl, config)
    except Exception, e:
        raise ESGPublishError("Error reinitializing the THREDDS Data Server: %s"%e)

    if reinitResult.find(threddsReinitSuccessPattern)==-1:
        raise ESGPublishError("Error reinitializing the THREDDS Data Server. Result=%s"%`reinitResult`)

    errorResult = readThreddsWithAuthentication(threddsReinitErrorUrl, config)
    index = errorResult.rfind(threddsErrorPattern)
    result = errorResult[index:]
    fatalIndex = result.find(threddsFatalErrorPattern)
    if fatalIndex!=-1:
        index2 = result[fatalIndex:].find('\n')
        errorMessage = result[fatalIndex:fatalIndex+index2]
        raise ESGPublishError("Error reinitializing the THREDDS Data Server: Fatal error: %s\n%s"%(errorMessage, str(result)))

    return errorResult[index:]

def generateThreddsOutputPath(datasetName, dbSession, handler, createDirectory=True):
    """Generate a THREDDS dataset catalog output path. If necessary, create a new directory.

    Uses the init file options:
    - thredds_root
    - thredds_catalog_basename
    - thredds_max_catalogs_per_directory

    Returns the pathname, of the form thredds_root/subdir/thredds_catalog_basename, where subdir is an integer.

    datasetName
      String dataset identifier.

    dbSession
      A database Session.

    handler
      Project handler instance.

    createDirectory
      Boolean, if True create directories as necessary.

    """

    # Get the root and basename.
    config = getConfig()
    if config is None:
        raise ESGPublishError("No configuration file found.")
    threddsRoot = config.get('DEFAULT', 'thredds_root')
    threddsCatalogBasename = handler.generateNameFromContext('thredds_catalog_basename', dataset_id=datasetName)
    threddsMaxCatalogs = int(config.get('DEFAULT', 'thredds_max_catalogs_per_directory'))

    # If the dataset has already been published, and the directory exists, and the basename is correct, reuse the catalog path.
    session = dbSession()
    catalog = session.query(Catalog).filter_by(dataset_name=datasetName).first()
    if catalog is not None:
        subdir, basename = os.path.split(catalog.location)
        lastSubdir = os.path.join(threddsRoot, subdir)
        if os.path.exists(lastSubdir) and basename==threddsCatalogBasename:
            result = os.path.join(lastSubdir, basename)
            return result
        else:
            session.delete(catalog)
            session.commit()

    # Get the subdirectory name:
    # - Find the 'last' subdirectory in numerical order
    subdirs = os.listdir(threddsRoot)
    digitSubdirs = [int(item) for item in subdirs if item.isdigit()]
    if len(digitSubdirs)>0:
        nsubdirs = max(digitSubdirs)
        subdir = str(nsubdirs)
        lastSubdir = os.path.join(threddsRoot, subdir)

        # - Get the number of catalogs. If >= the max, create a new directory
        ncatalogs = len(os.listdir(lastSubdir))
        if ncatalogs>=threddsMaxCatalogs:
            subdir = str(nsubdirs+1)
            lastSubdir = os.path.join(threddsRoot, subdir)
    else:
        subdir = '1'
        lastSubdir = os.path.join(threddsRoot, subdir)

    # Create the subdirectory if necessary
    if createDirectory and not os.path.exists(lastSubdir):
        os.mkdir(lastSubdir, 0775)

    # Build the catalog name
    result = os.path.join(lastSubdir, threddsCatalogBasename)
    location = os.path.join(subdir, threddsCatalogBasename) # relative to root

    # Add the database catalog entry
    catalog = Catalog(datasetName, location)
    session.add(catalog)

    session.commit()
    session.close()
    return result

def updateThreddsMasterCatalog(dbSession):
    """Rewrite the THREDDS ESG master catalog.

    Uses the init file options:
    - thredds_dataset_roots
    - thredds_master_catalog_name
    - thredds_root

    """

    global _nsmap, _XSI

    # Get the catalog path
    config = getConfig()
    if config is None:
        raise ESGPublishError("No configuration file found.")
    threddsRoot = config.get('DEFAULT', 'thredds_root')
    threddsMasterCatalogName = config.get('DEFAULT', 'thredds_master_catalog_name')
    threddsDatasetRootsOption = config.get('DEFAULT', 'thredds_dataset_roots')
    threddsDatasetRootsSpecs = splitRecord(threddsDatasetRootsOption)
    threddsDatasetRootPaths = [item[0] for item in threddsDatasetRootsSpecs]
    master = os.path.join(threddsRoot, "catalog.xml")
    info("Writing THREDDS ESG master catalog %s"%master)

    # Generate the master catalog
    catalog = Element("catalog", name=threddsMasterCatalogName, nsmap=_nsmap)
    catalog.set(_XSI+"schemaLocation", "%s http://www.unidata.ucar.edu/schemas/thredds/InvCatalog.1.0.2.xsd"%_nsmap[None])
    _genDatasetRoots(catalog, threddsDatasetRootsSpecs)
    doc = ElementTree(catalog)

    # Create document root elements

    # Get the dataset catalogs
    session = dbSession()
    for subcatalog in session.query(Catalog).select_from(join(Catalog, Dataset, Catalog.dataset_name==Dataset.name)).all():
        # Check that an existing catalog rootpath was not removed from the dataset roots list.
        # If so, THREDDS will choke.
        # Note: It's OK if the rootpath is None: that means the associated service is non-THREDDS
        # and doesn't have a rootpath prefix.
        if subcatalog.rootpath is not None and subcatalog.rootpath not in threddsDatasetRootPaths:
            warning("Catalog entry for dataset %s has rootpath = %s. Please add this to thredds_dataset_roots in the configuration file and regenerate the THREDDS catalog."%(subcatalog.dataset_name, subcatalog.rootpath))
            session.delete(subcatalog)
        else:

            # print catalog.dataset_name, catalog.location
            catalogRef = SE(catalog, "catalogRef", name=subcatalog.dataset_name)
            catalogRef.set(_XLINK+"title", subcatalog.dataset_name)
            catalogRef.set(_XLINK+"href", subcatalog.location)

    doc.write(master, xml_declaration=True, encoding='UTF-8', pretty_print=True)

    session.commit()
    session.close()

def updateThreddsRootCatalog():
    """Rewrite the THREDDS root catalog. The root catalog is (typically) one level
    above the ESG master catalog, and contains a catalogRef to the ESG master.

    Uses the init file options:
    - thredds_aggregation_services
    - thredds_file_services
    - thredds_master_catalog_name
    - thredds_offline_services
    - thredds_root
    - thredds_root_catalog_name

    """

    global _nsmap, _XSI

    config = getConfig()
    if config is None:
        raise ESGPublishError("No configuration file found.")

    section = 'DEFAULT'
    threddsESGRoot = config.get('DEFAULT', 'thredds_root')
    threddsRoot = os.path.dirname(threddsESGRoot)
    rootCatalog = os.path.join(threddsRoot, 'catalog.xml')
    info("Writing THREDDS root catalog %s"%rootCatalog)
    threddsMasterCatalogName = config.get(section, 'thredds_master_catalog_name')
    threddsRootCatalogName = config.get(section, 'thredds_root_catalog_name')
    threddsAggregationSpecs = getThreddsServiceSpecs(config, section, 'thredds_aggregation_services')
    threddsFileSpecs = getThreddsServiceSpecs(config, section, 'thredds_file_services')
    threddsOfflineSpecs = getThreddsServiceSpecs(config, section, 'thredds_offline_services')

    catalog = Element("catalog", name=threddsMasterCatalogName, nsmap=_nsmap)
    doc = ElementTree(catalog)
    aggregationServiceDict = _genService(catalog, threddsAggregationSpecs)
    fileServiceDict = _genService(catalog, threddsFileSpecs)
    if len(threddsOfflineSpecs)>0:
        offlineServiceDict = _genService(catalog, threddsOfflineSpecs)
    else:
        info("No offline services specified (option=thredds_offline_services).")

    catalogRef = SE(catalog, "catalogRef", name=threddsRootCatalogName)
    catalogRef.set(_XLINK+"title", threddsRootCatalogName)
    catalogRef.set(_XLINK+"href", "esgcet/catalog.xml")
    try:
        doc.write(rootCatalog, xml_declaration=True, encoding='UTF-8', pretty_print=True)
    except IOError:
        warning("Could not write to THREDDS root catalog %s - permission error?"%rootCatalog)
        
