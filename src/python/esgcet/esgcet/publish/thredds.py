import os
import logging
import ssl, httplib
from base64 import b64encode
import string
import hashlib
import urlparse
from lxml.etree import Element, SubElement as SE, ElementTree, Comment
from esgcet.config import splitLine, splitRecord, getConfig, getThreddsServiceSpecs, getThreddsAuxiliaryServiceSpecs
from esgcet.model import *
from esgcet.exceptions import *
from sqlalchemy.orm import join
from sqlalchemy import desc
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

GRIDFTP_SERVICE_TYPE = "GridFTP"
DEFAULT_THREDDS_CATALOG_VERSION = "2"
DEFAULT_THREDDS_SERVICE_APPLICATIONS = {
    GRIDFTP_SERVICE_TYPE:['DataMover-Lite'],
    'HTTPServer':['Web Browser','Web Script'],
    'OpenDAP':['Web Browser'],
    'SRM':[],
    'LAS':['Web Browser'],
    'BaseJumper':['Web Browser'],
    'Globus':['Web Browser']
    }
DEFAULT_THREDDS_SERVICE_AUTH_REQUIRED = {
    GRIDFTP_SERVICE_TYPE:'true',
    'HTTPServer':'true',
    'OpenDAP':'false',
    'SRM':'false',
    'LAS':'false',
    'BaseJumper':'false',
    'Globus':'false',
    }
DEFAULT_THREDDS_SERVICE_DESCRIPTIONS = {
    GRIDFTP_SERVICE_TYPE:'GridFTP',
    'HTTPServer':'HTTPServer',
    'OpenDAP':'OpenDAP',
    'SRM':'SRM',
    'LAS':'Live Access Server',
    'BaseJumper':'BASE Jumper HPSS access Server',
    'Globus':'Globus Transfer Service',
    }

ThreddsBases = ['/thredds/fileServer', '/thredds/dodsC', '/thredds/wcs', '/thredds/ncServer']
ThreddsFileServer = '/thredds/fileServer'

def genLasServiceHash(serviceAddr):
    p = urlparse.urlparse(serviceAddr[:-1])
    d = os.path.dirname(p.path)
    dbase = urlparse.urlunparse((p.scheme, p.netloc, d, None, None, None))
    s16 = '\xfe\xff'+(dbase.encode('utf-16-be'))
    result = hashlib.md5(s16).hexdigest().upper()
    return result    


def normTime(filevar, tounits, mdhandler):
    try:
        result = mdhandler.normalizeTime(filevar.aggdim_first, filevar.aggdim_units, tounits)
    except:
        print filevar
        raise
    return result


def normTimeRange(filevar, tounits, calendarTag, mdhandler):
    calendar = mdhandler.tagToCalendar(calendarTag)
    try:
        rval = mdhandler.normalizeTime(filevar.aggdim_first, filevar.aggdim_units, tounits, calendar=calendar)
        sval = mdhandler.normalizeTime(filevar.aggdim_last, filevar.aggdim_units, tounits, calendar=calendar)
    except:
        print filevar
        raise
    return rval, sval


def parseLASTimeDelta(unitsString):
    fields = unitsString.split()
    if len(fields)!=2:
        raise ESGPublishError("Invalid LAS units string: %s, should have the form 'value units'"%unitsString)
    value = string.atof(fields[0])
    units = fields[1].lower()
    return value, units


def splitTimes(fvlist, calendarTag, delta, mdhandler):
    # Split the file variables into evenly-spaced chunks.
    # Returns [chunk, chunk, ...] where each chunk is (startindex, stopindex+1, flag, nchunk, fa, la, le) and
    # flag = EVEN if the aggregate filevariable[startindex..stopindex] is evenly spaced, or
    #      = UNEVEN if no subset of filevariable[startindex..stopindex] is evenly spaced.
    # fa = firstAdjusted
    # la = lastAdjusted
    # le = lastEstimated
    #      
    # fvlist = [(filevar, firstValue, lastValue, units, ncoords), (filevar, firstValue, ...)]
    calendar = mdhandler.tagToCalendar(calendarTag)
    deltaValue, lasUnits = parseLASTimeDelta(delta)
    deltaUnits = mdhandler.LAS2CDUnits(lasUnits)
    result = []
    istart = 0
    while (istart<len(fvlist)):
        n, lookfor, ntot, fa, la, le = splitTimes_1(fvlist[istart:], calendar, deltaValue, deltaUnits, mdhandler)
        result.append((istart, istart+n, lookfor, ntot, fa, la, le))
        istart += n
    return result


def splitTimes_1(fvlist, calendar, deltaValue, deltaUnits, mdhandler):
    # Find the largest n in [0,len(fvlist)) such that either:
    # (1) fvlist[0:n] is evenly spaced and fvlist[0:n+1] is not, or
    # (2) fvlist[0:n] is unevenly spaced, and fvlist[n:n+1] is evenly spaced.

    # Check if the first file_variable is EVEN or UNEVEN
    filevar, firstValue, lastValue, units, ncoords = fvlist[0]
    result, fa, la, le = mdhandler.checkTimes(firstValue, lastValue, units, calendar, deltaValue, deltaUnits, ncoords)
    pfa, pla, ple = fa, la, le
    if result:
        lookfor = EVEN
        n = 1
        ntot = ncoords
        while (n<len(fvlist)):

            # Keep expanding the aggregate until the aggregate is unevenly spaced.
            ntot += fvlist[n][4]
            lastValue = fvlist[n][2]
            nextresult, fa, la, le = mdhandler.checkTimes(firstValue, lastValue, units, calendar, deltaValue, deltaUnits, ntot)
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
            nextresult, fa, la, le = mdhandler.checkTimes(firstValue, lastValue, units, calendar, deltaValue, deltaUnits, ncoord)
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


def _genLASAccess(parent, dsetname, serviceSpecs, hash, idtype, dataFormat):
    servtype, url, serviceName, compoundname = serviceSpecs
    urlPath = "?%s=%s_ns_%s"%(idtype, hash, dsetname)
    lasAccess = SE(parent, "access", urlPath=urlPath, serviceName=serviceName, dataFormat=dataFormat)
    return lasAccess


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


def _genFileV2(parent, path, size, ID, name, urlPath, serviceName, serviceDict, fileid, trackingID, modTime, fileVersion, checksum, checksumType,
               variable=None, fileVersionObj=None, gridftpMap=True, pid_wizard=None):
    dataset = SE(parent, "dataset", ID=ID, name=name)

    # Cache the URL for notification
    if fileVersionObj is not None:
        fileVersionObj.url = urlPath

    # Add tech notes documentation if present
    if fileVersionObj.tech_notes is not None:
        documentation = SE(dataset, "documentation", type="summary")
        documentation.set(_XLINK+"href", fileVersionObj.tech_notes)
        if fileVersionObj.tech_notes_title is not None:
            documentation.set(_XLINK+"title", fileVersionObj.tech_notes_title)

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
            # Map dataset roots for gridFTP if gridftp_map_dataset_roots config option is true
            elif serviceType==GRIDFTP_SERVICE_TYPE:
                if gridftpMap:
                    publishPath = urlPath
                else:
                    publishPath = path
                if publishPath[0]!=os.sep:
                    publishPath = os.sep+publishPath
            elif serviceType == "Globus":
                publishPath = urlPath
            else:
                publishPath = path
            if isThreddsFileService:
                dataset.set("urlPath", publishPath)
                dataset.set("serviceName", subName)
            else:
                access = SE(dataset, "access", serviceName=subName, urlPath=publishPath)

    # add file handle to dataset PID
    if pid_wizard:
        pid_wizard.add_file(file_name=name,
                            file_handle=trackingID,
                            checksum=checksum,
                            file_size=size,
                            publish_path=publishPath,
                            checksum_type=checksumType,
                            file_version=fileVersion)
    return dataset


def _genDatasetRoots(parent, rootSpecs):
    for path, location in rootSpecs:
        datasetRoot = SE(parent, "datasetRoot", path=path, location=location)


def _genAggregationsV2(parent, variable, variableID, handler, dataset, project, model, experiment, aggServiceName, aggdim_name, perVarMetadata, versionNumber):

    mdhandler = handler.getMetadataHandler()
    
    aggID = "%s.%d.aggregation"%(variableID, versionNumber)
    try:
        aggName = handler.generateNameFromContext('variable_aggregation_dataset_name', project_description=project.description, model_description=model.description, experiment_description=experiment.description, variable=variable.short_name, variable_long_name=variable.long_name, variable_standard_name=variable.standard_name)
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

    # Note: Create time_length here so that THREDDS is happy, set its value below
    timeLengthProp = SE(aggDataset, "property", name="time_length", value="0")
    netcdf = SE(aggDataset, "netcdf", nsmap=nsmap)
    aggElem = SE(netcdf, "aggregation", type="joinExisting", dimName=aggdim_name)
    if dataset.calendar:
        calendarProperty = SE(aggDataset, "property", name="calendar", value=dataset.calendar)

    # Sort filevars according to aggdim_first normalized to the dataset basetime
    filevars = []
    has_null_aggdim = False
    for filevar in variable.file_variables:
        if filevar.aggdim_first is None:
            has_null_aggdim = True
            break
        filevars.append((filevar, normTime(filevar, dataset.aggdim_units, mdhandler)))
    if has_null_aggdim:
        return
    filevars.sort(lambda x,y: cmp(x[1], y[1]))

    nvars = 0
    agglen = 0
    for filevar, aggdim_first in filevars:
        fvdomain = map(lambda x: (x.name, x.length, x.seq), filevar.dimensions)
        fvdomain.sort(lambda x,y: cmp(x[SEQ], y[SEQ]))
        if len(fvdomain)>0 and fvdomain[0][0]==aggdim_name:
            sublen = fvdomain[0][1]
            fileNetcdf = SE(aggElem, "netcdf", location=filevar.file.getLocation(), ncoords="%d"%sublen)
            agglen += sublen
            nvars += 1
    timeLengthProp.set("value", "%d"%agglen)

    # Create the aggregation if at least one filevar has the aggregate dimension
    if nvars>0:
        parent.append(aggDataset)


def _genSubAggregation(parent, aggID, aggName, aggServiceName, aggdim_name, fvlist, flag, las_time_delta, calendar, start, lasServiceSpecs, lasServiceHash):
    aggDataset = Element("dataset", name=aggName, ID=aggID, urlPath=aggID, serviceName=aggServiceName)
    aggIDProp = SE(aggDataset, "property", name="aggregation_id", value=aggID)
    if flag==EVEN:
        timeDeltaProperty = SE(aggDataset, "property", name="time_delta", value=las_time_delta)
        calendarProperty = SE(aggDataset, "property", name="calendar", value=calendar)
        startProperty = SE(aggDataset, "property", name="start", value=repr(start))
    nsmap = {
        None : "http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2"
        }

    # Note: Create time_length here so that THREDDS is happy, set its value below
    timeLengthProperty = SE(aggDataset, "property", name="time_length", value="0")

    if lasServiceSpecs is not None:
        _genLASAccess(aggDataset, aggID, lasServiceSpecs, lasServiceHash, "catid", "NetCDF")

    netcdf = SE(aggDataset, "netcdf", nsmap=nsmap)
    aggElem = SE(netcdf, "aggregation", type="joinExisting", dimName=aggdim_name)
    agglen = 0
    for filevar, aggfirst, agglast, units, ncoords in fvlist:
        fileNetcdf = SE(aggElem, "netcdf", location=filevar.file.getLocation(), ncoords="%d"%ncoords)
        agglen += ncoords
    timeLengthProperty.set("value", "%d"%agglen)
    parent.append(aggDataset)    


def _genLASAggregations(parent, variable, variableID, handler, dataset, project, model, experiment, aggServiceName, aggdim_name, lasTimeDelta, perVarMetadata, versionNumber, lasServiceSpecs, lasServiceHash):

    mdhandler = handler.getMetadataHandler()

    # Generate the top-level aggregation
    aggID = "%s.%d.aggregation"%(variableID, versionNumber)
    try:
        aggName = handler.generateNameFromContext('variable_aggregation_dataset_name', project_description=project.description, model_description=model.description, experiment_description = experiment.description, variable=variable.short_name, variable_long_name=variable.long_name, variable_standard_name=variable.standard_name)
    except:
        aggName = aggID
    aggDataset = Element("dataset", name=aggName, ID=aggID)
    aggIDProp = SE(aggDataset, "property", name="aggregation_id", value=aggID)
    perAggVariables = SE(aggDataset, "variables", vocabulary="CF-1.0")
    perAggVariable = _genVariable(perAggVariables, variable)
    aggDataset.append(perVarMetadata)
    if lasServiceSpecs is not None:
        _genLASAccess(aggDataset, aggID, lasServiceSpecs, lasServiceHash, "catid", "NetCDF")

    # Sort filevars according to aggdim_first normalized to the dataset basetime
    filevars = []
    has_null_aggdim = False
    for filevar in variable.file_variables:
        if filevar.aggdim_first is None:
            has_null_aggdim = True
            break
        r2, s2 = normTimeRange(filevar, dataset.aggdim_units, dataset.calendar, mdhandler)
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
    lasTimeDeltaValue, lasTimeDeltaUnits = parseLASTimeDelta(lasTimeDelta)
    cdunits = mdhandler.LAS2CDUnits(lasTimeDeltaUnits)
    cdcalendar = mdhandler.tagToCalendar(dataset.calendar)
    iseven, first, last, est = mdhandler.checkTimes(filevars[0][1], filevars[-1][2], dataset.aggdim_units, cdcalendar, lasTimeDeltaValue, cdunits, ntot)

    # If so, just generate one subaggregation
    if iseven:
        subAggID = "%s.%d"%(aggID, 1)
        subAggName = "%s - Subset %d"%(aggName, 1)
        _genSubAggregation(aggDataset, subAggID, subAggName, aggServiceName, aggdim_name, fvlist, EVEN, lasTimeDelta, dataset.calendar, first, lasServiceSpecs, lasServiceHash)

    # Split the aggregation so that each piece is either evenly spaced or not.
    else:
        chunks = splitTimes(fvlist, dataset.calendar, lasTimeDelta, mdhandler)

        # For each subaggregation generate a dataset.
        nid = 1
        for start, stop, flag, nchunk, fa, la, le in chunks:
            subAggID = "%s.%d"%(aggID, nid)
            subAggName = "%s - Subset %d"%(aggName, nid)
            _genSubAggregation(aggDataset, subAggID, subAggName, aggServiceName, aggdim_name, fvlist[start:stop], flag, lasTimeDelta, dataset.calendar, fa, lasServiceSpecs, lasServiceHash)
            nid += 1


def _genPerVariableDatasetsV2(parent, dataset, datasetName, resolution, filesRootLoc, filesRootPath, datasetRootDict, excludeVariables, offline,
                              serviceName, serviceDict, aggServiceName, handler, project, model, experiment, las_configure, las_time_delta,
                              versionNumber, variablesElem, variableElemDict, lasServiceSpecs, lasServiceHash, gridftpMap=True, pid_wizard=None):

    mdhandler = handler.getMetadataHandler()

    aggdim_name = dataset.aggdim_name
    shortNames = {}
    datasetVersionObj = dataset.getVersionObj()
    for variable in dataset.variables:
        # It is possible for a dataset to have different variables with the same name,
        # for example if the number of levels is different in one file than another.
        # Ensure that IDs are unique
        if variable.short_name in excludeVariables:
            continue

        # Check the variable/file combination for project conformance

        # The property variable.file_variables will return FileVariables for 
        # all versions of this variable.  We need to filter those FileVariables 
        # by the files we know are part of the version we want.
        ds_fileVersions = set(datasetVersionObj.getFileVersions())
        filelist = []
        for filevar in variable.file_variables:
            if not handler.threddsIsValidVariableFilePair(variable, filevar.file):
                continue
            for var_fileVersion in filevar.file.versions:
                if var_fileVersion in ds_fileVersions:
                    filelist.append((filevar.file.getLocation(), filevar.file.getSize(), filevar.file))

        if len(filelist)==0:
            if variable.short_name in variableElemDict:
                variablesElem.remove(variableElemDict[variable.short_name])
                del variableElemDict[variable.short_name]
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
        if variable.updown_values is not None:
            try:
                if variable.updown_values.strip()!='':
                    zvaluesProp = SE(perVarMetadata, "property", name="z_values", value=variable.updown_values)
            except:
                warning("updown_values = %s for %s"%(variable.updown_values, variableID))
        geoCoverage = _genGeospatialCoverage(perVarMetadata, variable)
        if variable.aggdim_first is not None:
            timeFirst = mdhandler.genTime(variable.aggdim_first, dataset.aggdim_units, dataset.calendar)
            timeLast = mdhandler.genTime(variable.aggdim_last, dataset.aggdim_units, dataset.calendar)
            timeCoverage = _genTimeCoverage(perVarMetadata, timeFirst, timeLast, resolution)

        # Files
        filesID = variableID
        try:
            filesName = handler.generateNameFromContext('variable_files_dataset_name', project_description=project.description, model_description=model.description, experiment_description=experiment.description, variable=variable.short_name, variable_long_name=variable.long_name, variable_standard_name=variable.standard_name)
        except Exception, e:
            filesName = filesID
        hasThreddsServ = hasThreddsService(serviceName, serviceDict)
        for path, size, fileobj in filelist:

            basename = os.path.basename(path)
            fileid = "%s.%s"%(datasetName, fileobj.base)
            fileVersionObj = fileobj.getLatestVersion()
            fileVersion = fileVersionObj.version
            fileVersionID = "%s.%s"%(datasetVersionObj.name, fileobj.base)

            # There only needs to be an associated Thredds rootpath if at least
            # one associated service is a Thredds service
            if hasThreddsServ:
                # Sanity check: are all the dataset files under the same rootpath?
                rootpath, rootloc = _getRootPathAndLoc(filevar.file, datasetRootDict)
                if rootpath is None:
                    raise ESGPublishError("File %s is not contained in any THREDDS root path. Please add an entry to thredds_dataset_roots in the configuration file."%path)
                if rootpath!=filesRootPath:
                    warning('rootpath=%s does not match dataset root path=%s'%(rootpath, filesRootPath))

                rootIndex = path.find(rootloc)
                if rootIndex==0:
                    urlpath = path.replace(rootloc, rootpath, 1)
                else:
                    # warning('File %s is not in a dataset root. Add an entry to thredds_dataset_roots with a directory containing this file'%path)
                    urlpath = path
            else:
                urlpath = path

            urlpath = os.path.normpath(urlpath)
            path = os.path.normpath(path)
            trackingID = fileobj.versions[-1].tracking_id
            modTime = fileobj.getModificationFtime()
            checksum = fileobj.getChecksum()
            checksumType = fileobj.getChecksumType()
            fileDataset = _genFileV2(parent, path, size, fileVersionID, basename, urlpath, serviceName, serviceDict, fileid, trackingID, modTime,
                                     fileVersion, checksum, checksumType, variable=variable, fileVersionObj=fileVersionObj, gridftpMap=gridftpMap,
                                     pid_wizard=pid_wizard)

        # Aggregation
        # Don't generate an aggregation if the variable has time overlaps or a non-monotonic aggregate dimension,
        # or the dataset does not have an aggregate dimension
        if variable.has_errors or dataset.aggdim_units is None:
            continue
        if las_configure:
            _genLASAggregations(parent, variable, variableID, handler, dataset, project, model, experiment, aggServiceName, aggdim_name, las_time_delta, perVarMetadata, versionNumber, lasServiceSpecs, lasServiceHash)
        else:
            _genAggregationsV2(parent, variable, variableID, handler, dataset, project, model, experiment, aggServiceName, aggdim_name, perVarMetadata, versionNumber)


def _genPerTimeDatasetsV2(parent, dataset, datasetName, filesRootLoc, filesRootPath, datasetRootDict, excludeVariables, offline, serviceName,
                          serviceDict, handler, project, model, experiment, versionNumber, gridftpMap=True, pid_wizard=None):
    datasetVersionObj = dataset.getVersionObj(versionNumber)
    filelist = [(fileobj.getLocation(), fileobj.getSize(), fileobj) for fileobj in datasetVersionObj.files]
    filesID = datasetName
    try:
        filesName = handler.generateNameFromContext('per_time_files_dataset_name', project_description=project.description, model_description=model.description, experiment_description=experiment.description)
    except Exception, e:
        filesName = filesID
##     filesDataset = SE(parent, "dataset", name=filesName, ID=filesID)
    hasThreddsServ = hasThreddsService(serviceName, serviceDict)
    for path, size, fileobj in filelist:
        # basename = os.path.basename(path)
        basename = fileobj.parent.base
        fileid = "%s.%s"%(filesID, basename)
        threddsFileId = "%s.%s"%(datasetVersionObj.name, basename)
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
        fileDataset = _genFileV2(parent, path, size, threddsFileId, basename, urlpath, serviceName, serviceDict, fileid, trackingID, modTime,
                                 fileVersion, checksum, checksumType, fileVersionObj=fileobj, gridftpMap=gridftpMap, pid_wizard=pid_wizard)


def generateThredds(datasetName, dbSession, outputFile, handler, datasetInstance=None, genRoot=False, service=None, perVariable=None,
                    versionNumber=-1, pid_connector=None):
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
      Boolean, overrides ``variable_per_file`` config option.

    versionNumber
      Version number. Defaults to latest.

    pid_connector
        esgfpid.Connector object to register PIDs

    """

    session = dbSession()
    if hasattr(outputFile, "name"):
        info("Writing THREDDS catalog %s"%outputFile.name)
    else:
        info("Creating THREDDS catalog for dataset %s"%datasetName)

    # Lookup the dataset
    if datasetInstance is None:
        #!FIXME: this call doesn't use versionNumber
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
        raise ESGPublishError("Catalog version=1 deprecated, please use version 2 instead")
##         _generateThreddsV1(datasetName, outputFile, handler, session, dset, context, project, model, experiment, config, section, genRoot=genRoot, service=service, perVariable=perVariable)
    elif catalog_version=="2":
        _generateThreddsV2(datasetName, outputFile, handler, session, dset, context, project, model, experiment, config, section, genRoot=genRoot,
                           service=service, perVariable=perVariable, versionNumber=versionNumber, pid_connector=pid_connector)
    else:
        raise ESGPublishError("Invalid catalog version: %s"%catalog_version)

    session.commit()
    session.close()


def _generateThreddsV2(datasetName, outputFile, handler, session, dset, context, project, model, experiment, config, section, genRoot=False,
                       service=None, perVariable=None, versionNumber=-1, pid_connector=None):

    global _nsmap, _XSI
    CATALOG_VERSION = "2"

    offline = dset.offline
    threddsAggregationSpecs = getThreddsServiceSpecs(config, section, 'thredds_aggregation_services')
    threddsFileSpecs = getThreddsServiceSpecs(config, section, 'thredds_file_services')
    threddsOfflineSpecs = getThreddsServiceSpecs(config, section, 'thredds_offline_services')
    threddsRestrictAccess = config.get(section, 'thredds_restrict_access', default=None)
    if threddsRestrictAccess is None:
        warning("thredds_restrict_access is not set: THREDDS datasets will be openly readable.")
    threddsDatasetRootsOption = config.get('DEFAULT', 'thredds_dataset_roots')
    threddsDatasetRootsSpecs = splitRecord(threddsDatasetRootsOption)
    threddsServiceApplicationSpecs = getThreddsAuxiliaryServiceSpecs(config, section, 'thredds_service_applications', multiValue=True)
    threddsServiceAuthRequiredSpecs = getThreddsAuxiliaryServiceSpecs(config, section, 'thredds_service_auth_required')
    threddsServiceDescriptionSpecs = getThreddsAuxiliaryServiceSpecs(config, section, 'thredds_service_descriptions')
    excludeVariables = splitLine(config.get(section, 'thredds_exclude_variables', default=''), sep=',')
    gridftpMapDatasetRoots = config.getboolean(section, 'gridftp_map_dataset_roots', default=True)
    datasetIdTemplate = config.get(section, 'dataset_id', raw=True, default=None)
    directoryFormat = config.get(section, 'directory_format', raw=True, default=None)

    if not "%(root)s" in directoryFormat:
        directoryFormat = None

    if not offline:
        if perVariable is None:
            perVariable = config.getboolean(section, 'variable_per_file', False)
    else:
        perVariable = False
    lasConfigure = config.getboolean(section, 'las_configure', False)
    if lasConfigure:
        lasTimeDelta = handler.generateNameFromContext('las_time_delta')

        # Get the LAS service specs
        lasServiceSpecs = None
        lasServiceHash = None
        for entry in threddsAggregationSpecs:
            if entry[0]=='LAS':
                lasServiceSpecs = entry
                lasServiceHash = genLasServiceHash(entry[1])
                break
    else:
        lasTimeDelta = None
        lasServiceSpecs = None
        lasServiceHash = None
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

    # Check that the version actually exists
    dsetVersionObj = dset.getVersionObj(version=versionNumber)
    if dsetVersionObj is None:
        raise "No dataset found: %s, version %d"%(dset.name, versionNumber)
    dsetVersion = versionNumber
    if project is None or experiment is None or model is None:
        datasetDesc = datasetName
    else:

        # First try generating the description from the existing context
        try:
            if perVariable:

                # Allow variable_short_name and variable_standard_name
                variable_short_name = "<Unknown>"
                variable_standard_name = "<Unknown>"
                for variable in dset.variables:
                    if variable.short_name not in excludeVariables:
                        variable_short_name = variable.short_name
                        variable_standard_name = variable.standard_name
                        break
                datasetDesc = handler.generateNameFromContext('dataset_name_format', project_description=project.description, model_description=model.description, experiment_description = experiment.description, version=str(dsetVersion), variable_short_name=variable_short_name, variable_standard_name=variable_standard_name)
            else:
                datasetDesc = handler.generateNameFromContext('dataset_name_format', project_description=project.description, model_description=model.description, experiment_description = experiment.description, version=str(dsetVersion))
        except:

            # Maybe the database values are screwy, just get the dataset_name fields
            try:
                context = handler.parseDatasetName(datasetName, context)
                datasetDesc = handler.generateNameFromContext('dataset_name_format', **context)
            except:

                # OK, give up
                datasetDesc = datasetName
                
    dsetVersionID = "%s.v%d"%(datasetName, dsetVersion)
    datasetElem = SE(catalog, "dataset", name=datasetDesc, ID=dsetVersionID)

    # If thredds_restrict_access is set, add restrictAccess attribute, otherwise data is open
    if threddsRestrictAccess is not None:
        datasetElem.set("restrictAccess", threddsRestrictAccess)

    # Add tech notes documentation if present
    if dsetVersionObj.tech_notes is not None:
        documentation = SE(datasetElem, "documentation", type="summary")
        documentation.set(_XLINK+"href", dsetVersionObj.tech_notes)
        if dsetVersionObj.tech_notes_title is not None:
            documentation.set(_XLINK+"title", dsetVersionObj.tech_notes_title)

    # Add citation link if present
    if dsetVersionObj.citation_url is not None:
        SE(datasetElem, "property", name="citation_url", value=dsetVersionObj.citation_url)
        documentation = SE(datasetElem, "documentation", type="citation")
        documentation.set(_XLINK + "href", dsetVersionObj.citation_url)
        documentation.set(_XLINK + "title", "Citation")

    # Add link to PID if present
    if dsetVersionObj.pid is not None:
        SE(datasetElem, "property", name="pid", value=dsetVersionObj.pid)
        documentation = SE(datasetElem, "documentation", type="pid")
        documentation.set(_XLINK + "href", 'http://hdl.handle.net/%s' %dsetVersionObj.pid)
        documentation.set(_XLINK + "title", "PID")

    datasetIdProp = SE(datasetElem, "property", name="dataset_id", value=datasetName)
    datasetVersionProp = SE(datasetElem, "property", name="dataset_version", value=str(dsetVersion))
    if datasetIdTemplate is not None:
        datasetIdTemplate = SE( datasetElem, "property", name="dataset_id_template_", value=datasetIdTemplate)
    if directoryFormat is not None:
        directoryFormat = SE( datasetElem, "property", name="directory_format_template_", value=directoryFormat)

    is_replica = False
    if dset.master_gateway is not None:
        is_replica = True
        SE(datasetElem, "property", name="is_replica", value="true")

    for name in handler.getFieldNames():
        if handler.isThreddsProperty(name) and name != "dataset_version":

            vals_lst = []
            # delimited-values here
            if config.get(section, name + "_delimiter", default="no") == "space":
                vals_lst = handler.getField(name).split(' ')
            elif config.get(section, name + "_delimiter", default="no") == "comma":          
                vals_lst = handler.getField(name).split(',')
            if len(vals_lst) > 0:
                for value in vals_lst:
                    # TODO need a try/except?
                    property = SE(datasetElem, "property", name=name, value=value)    
            else:
                try:
                    if handler.getField(name):
                        property = SE(datasetElem, "property", name=name, value=handler.getField(name))
                except TypeError:
                    raise ESGPublishError("Invalid value for field %s: %s"%(name, handler.getField(name)))

    if description=='':
        description = dsetVersionObj.comment
        
    if description not in ['', None]:
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
        variableElemDict = {}
        for variable in dset.variables:
            if variable.short_name not in excludeVariables:
                # It is possible for a dataset to have different variables with the same name,
                # for example if the number of levels is different in one file than another.
                # Only list a variable name once in the <variables> element.
                if shortNames.has_key(variable.short_name):
                    continue
                shortNames[variable.short_name] = 1
                variableElem = _genVariable(variables, variable)
                variableElemDict[variable.short_name] = variableElem

    metadata2 = SE(datasetElem, "metadata", inherited="true")
##     geospatialCoverage = SE(metadata2, "geospatialCoverage")
##     coverageName = SE(geospatialCoverage, "name", vocabulary="Thredds")
##     coverageName.text = "global"
    dataType = SE(metadata2, "dataType")
    dataType.text = "Grid"
    dataFormat = SE(metadata2, "dataFormat")
    dataFormat.text = "NetCDF"

    # Add LAS access element if configuring LAS
    if lasConfigure and (lasServiceSpecs is not None):
        _genLASAccess(datasetElem, dsetVersionID, lasServiceSpecs, lasServiceHash, "catid", "NetCDF")

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
    catalogObj = session.query(Catalog).filter_by(dataset_name=datasetName, version=versionNumber).first()
    catalogObj.rootpath = filesRootPath

    # start PID generation
    pid_wizard = None
    if pid_connector:
        pid_wizard = pid_connector.create_publication_assistant(drs_id=datasetName,
                                                                version_number=versionNumber,
                                                                is_replica=is_replica)

    if perVariable:
        # Per-variable datasets
        _genPerVariableDatasetsV2(datasetElem, dset, datasetName, resolution, filesRootLoc, filesRootPath, datasetRootDict, excludeVariables,
                                  offline, serviceName, serviceDict, aggServiceName, handler, project, model, experiment, lasConfigure, lasTimeDelta,
                                  versionNumber, variables, variableElemDict, lasServiceSpecs, lasServiceHash, gridftpMap=gridftpMapDatasetRoots,
                                  pid_wizard=pid_wizard)
    else:
        # Per-time datasets
        _genPerTimeDatasetsV2(datasetElem, dset, datasetName, filesRootLoc, filesRootPath, datasetRootDict, excludeVariables, offline, serviceName,
                              serviceDict, handler, project, model, experiment, versionNumber, gridftpMap=gridftpMapDatasetRoots,
                              pid_wizard=pid_wizard)

    # Call the THREDDS catalog hook if set
    catalogHook = handler.getThreddsCatalogHook()
    if catalogHook is not None:
        info('Calling catalog hook')
        catalogHook(doc, dset, dsetVersionObj, catalogObj, config, section, perVariable)

    doc.write(outputFile, xml_declaration=True, encoding='UTF-8', pretty_print=True)
    event = Event(dset.name, versionNumber, WRITE_THREDDS_CATALOG_EVENT)
    dset.events.append(event)

    # send PID information to handle server once THREDDS catalog is written
    if pid_wizard:
        pid_wizard.dataset_publication_finished()


def readThreddsWithAuthentication(url, config):
    """
    Read a protected page from the THREDDS Data Server.

    Returns the THREDDS page as a string.

    url
      String URL to read.

    config
      Configuration file object.
    
    """

#    threddsAuthenticationRealm = config.get('DEFAULT', 'thredds_authentication_realm')
    threddsUsername = config.get('DEFAULT', 'thredds_username')
    threddsPassword = config.get('DEFAULT', 'thredds_password')

    # Create an OpenerDirector with support for Basic HTTP Authentication...
    try:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    except AttributeError:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS)


    user_pass = b64encode(threddsUsername +":"+threddsPassword)

    pd = urlparse.urlparse(url)

    conn = httplib.HTTPSConnection(pd.hostname, port=pd.port, context=ctx)

    req_headers = {'Host': pd.hostname,
               'Authorization' : 'Basic %s' % user_pass
               }
    
    conn.request('GET', url, headers=req_headers)

    res = conn.getresponse()

    page = res.read()

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
        msg = `e`
        if msg.find("maximum recursion depth")!=-1:
            msg = "Invalid thredds password. Check the value of thredds_password in esg.ini"
        raise ESGPublishError("Error reinitializing the THREDDS Data Server: %s"%msg)

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


def ensureDirectoryExists(dirPath, mode=0775):
    """
    Ensure a specified directory exists, including any parent directories.
    Does not return anything, but raises an exception if it cannot be created.
    """
    if not os.path.isdir(dirPath):
        ensureDirectoryExists(os.path.dirname(dirPath), mode=mode)
        try:
            os.mkdir(dirPath)
            os.chmod(dirPath, mode)
        except OSError:
            if not os.path.exists(dirPath):
                raise ESGPublishError("Error creating directory %s. Please make sure you have the correct permissions." % dirPath)


def getThreddsNumberedDir(threddsRoot, threddsMaxCatalogs):
    """
    Get the subdirectory path when using the numbered directory scheme.
    Returns the path relative to threddsRoot
    """

    # - Find the 'last' subdirectory in numerical order
    subdirs = os.listdir(threddsRoot)
    digitSubdirs = [int(item) for item in subdirs if item.isdigit()]
    if digitSubdirs:
        lastdir = max(digitSubdirs)
        subdir = str(lastdir)

        # - Get the number of catalogs. If >= the max, create a new directory        
        ncatalogs = len(os.listdir(os.path.join(threddsRoot, subdir)))

        if ncatalogs < threddsMaxCatalogs:
            return subdir
        else:
            return str(lastdir + 1)
    else:
        return '1'


def reusedCatalogPath(catalog, threddsRoot, threddsCatalogBasename):
    """
    If catalog path can be reused -- that is: if the dataset has already been 
    published, and the directory exists, and the basename is correct -- return 
    the full path, otherwise returns None
    """
    subdir, basename = os.path.split(catalog.location)
    lastSubdir = os.path.join(threddsRoot, subdir)
    if os.path.exists(lastSubdir) and basename==threddsCatalogBasename:
        return os.path.join(lastSubdir, basename)
    else:
        return None


def generateThreddsOutputPath(datasetName, version, dbSession, handler, createDirectory=True):
    """Generate a THREDDS dataset catalog output path and ensure it is stored in the db. If necessary, create a new directory.

    Uses the init file options:
    - thredds_root
    - thredds_catalog_basename
    - thredds_use_numbered_directories
    - thredds_max_catalogs_per_directory

    Returns the pathname, of the form thredds_root/subdir/thredds_catalog_basename, where subdir is an integer.

    datasetName
      String dataset identifier.

    version  
      version number
      
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
    threddsCatalogBasename = handler.generateNameFromContext('thredds_catalog_basename', dataset_id=datasetName, version=str(version))
    threddsUseNumberedDirs = config.getboolean('DEFAULT', 'thredds_use_numbered_directories', default=True)
    if threddsUseNumberedDirs:
        threddsMaxCatalogs = int(config.get('DEFAULT', 'thredds_max_catalogs_per_directory'))

    session = dbSession()

    catalog = session.query(Catalog).filter_by(dataset_name=datasetName, version=version).first()

    if catalog:
        reusedPath = reusedCatalogPath(catalog, threddsRoot, threddsCatalogBasename)
        if reusedPath:
            session.close()
            return reusedPath
        else:
            session.delete(catalog)
            session.commit()

    if threddsUseNumberedDirs:
        relPath = getThreddsNumberedDir(threddsRoot, threddsMaxCatalogs)
    else:
        relPath = datasetName.replace('.', '/')

    fullPath = os.path.join(threddsRoot, relPath)

    # Create the subdirectory if necessary
    if createDirectory:
        ensureDirectoryExists(fullPath)

    # Build the catalog name
    result = os.path.join(fullPath, threddsCatalogBasename)
    location = os.path.join(relPath, threddsCatalogBasename) # relative to root

    # Add the database catalog entry
    catalog = Catalog(datasetName, version, location)
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

    # Get the dataset catalogs. Note: include all dataset versions.
    session = dbSession()
    for subcatalog in session.query(Catalog).select_from(join(Catalog, Dataset, Catalog.dataset_name==Dataset.name)).order_by(Catalog.dataset_name, desc(Catalog.version)).all():
#     for subcatalog in session.query(Catalog).select_from(join(Catalog, Dataset, Catalog.dataset_name==Dataset.name)).all():
        # Check that an existing catalog rootpath was not removed from the dataset roots list.
        # If so, THREDDS will choke.
        # Note: It's OK if the rootpath is None: that means the associated service is non-THREDDS
        # and doesn't have a rootpath prefix.
        if subcatalog.rootpath is not None and subcatalog.rootpath not in threddsDatasetRootPaths:
            warning("Catalog entry for dataset %s has rootpath = %s. Please add this to thredds_dataset_roots in the configuration file and regenerate the THREDDS catalog."%(subcatalog.dataset_name, subcatalog.rootpath))
            # NOTE! Don't delete the catalog - it may have been generated using a different configuration!
            # session.delete(subcatalog)
        else:

            # print catalog.dataset_name, catalog.location
            catalogId = "%s.v%d"%(subcatalog.dataset_name, subcatalog.version)
            catalogRef = SE(catalog, "catalogRef", name=catalogId)
            catalogRef.set(_XLINK+"title", catalogId)
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
