import os
import logging
import numpy
import re
import datetime
from cdtime import reltime, DefaultCalendar
from esgcet.messaging import debug, info, warning, error, critical, exception

# from Scientific.IO import NetCDF
from cdms2 import Cdunif
from esgcet.model import *
from esgcet.exceptions import *
from esgcet.config import splitLine, getConfig, tagToCalendar
from utility import getTypeAndLen, issueCallback, compareFiles, checksum

NAME=0
LENGTH=1
SEQ=2

CREATE_OP=1
DELETE_OP=2
RENAME_OP=3
UPDATE_OP=4
REPLACE_OP=5

MAX_FILENAME_DUPLICATES = 1000          # Maximum number of duplicate file basenames in a dataset
def generateFileBase(location, basedict, dsetname):
    """Generate a basename that is unique wrt to all files in the dataset."""
    basename = os.path.basename(location)
    if not basedict.has_key(basename):
        result = basename
    else:
        for i in xrange(MAX_FILENAME_DUPLICATES):
            cand = "%s_%d"%(basename, i)
            if not basedict.has_key(cand):
                result = cand
                break
        else:
            raise ESGPublishError("Too many files with basename: %s in dataset %s, maximum=%d"%(basename, dsetname, MAX_FILENAME_DUPLICATES))

    return result

def extractFromDataset(datasetName, fileIterator, dbSession, cfHandler, aggregateDimensionName=None, offline=False, operation=CREATE_OP, progressCallback=None, stopEvent=None, keepVersion=False, newVersion=None, extraFields=None, masterGateway=None, comment=None, **context):
    """
    Extract metadata from a dataset represented by a list of files, add to a database. Populates the database tables:

    - dataset
    - file
    - file_variable (partially)
    - associated attribute tables

    Returns a Dataset object.

    datasetName
      String dataset identifier.

    fileIterator
      An iterator that returns an iteration of (file_path, file_size), where file_size is an integer.

    dbSession
      A database Session.

    cfHandler  
      A CF handler instance

    aggregateDimensionName
      The name of the dimension across which the dataset is aggregated, if any.

    offline
      Boolean, True if the files are offline, cannot be scanned.

    operation
      Publication operation, one of CREATE_OP, DELETE_OP, RENAME_OP, UPDATE_OP

    progressCallback
      Tuple (callback, initial, final) where ``callback`` is a function of the form ``callback(progress)``, ``initial`` is the initial value reported, ``final`` is the final value reported.

    stopEvent
      Object with boolean attribute ``stop_extract`` (for example, ``utility.StopEvent``). If set to True (in another thread) the extraction is stopped.

    keepVersion
      Boolean, True if the dataset version should not be incremented.

    newVersion
      Set the new version number explicitly. By default the version number is incremented by 1. See keepVersion.

    extraFields
      Extra fields dictionary, as from ``readDatasetMap``.

    masterGateway
      The gateway that owns the master copy of the datasets. If None, the dataset is not replicated.
      Otherwise the TDS catalog is written with a 'master_gateway' property, flagging the dataset(s)
      as replicated.

    comment
      String comment on the dataset version. If the dataset version is not increased, the comment is ignored.

    context
      A dictionary with keys ``project``, ``model``, ``experiment``, etc. The context consists of all fields needed to uniquely define the dataset.

    """

    session = dbSession()

    # Get configuration options related to the scan
    configOptions = {}
    config = getConfig()
    if config is not None:
        section = 'project:%s'%context.get('project')
        vlstring = config.get(section, 'variable_locate', default=None)
        if vlstring is not None:
            fields = splitLine(vlstring)
            varlocate = [s.split(',') for s in fields]
        else:
            varlocate = None

        line = config.get('DEFAULT', 'checksum', default=None)
        if line is not None:
            checksumClient, checksumType = splitLine(line)
        else:
            checksumClient = None
            checksumType = None
    else:
        varlocate = None
        checksumClient = None
        checksumType = None
        
    configOptions['variable_locate'] = varlocate
    configOptions['checksumClient'] = checksumClient
    configOptions['checksumType'] = checksumType

    # Check if the dataset is already in the database
    dset = session.query(Dataset).filter_by(name=datasetName).first()
    if dset is not None:
        if operation==CREATE_OP:
            operation = REPLACE_OP
    else:
        if operation in [UPDATE_OP, REPLACE_OP]:
            operation = CREATE_OP
        elif operation in [DELETE_OP, RENAME_OP]:
            raise ESGPublishError("No such dataset: %s"%datasetName)

    # Cannot add online files to offline dataset, and vice versa
    if dset is not None and dset.offline != offline:
        if dset.offline:
            raise ESGPublishError("Dataset %s is offline, set offline flag or replace the dataset."%dset.name)
        else:
            raise ESGPublishError("Dataset %s is online, but offline flag is set."%dset.name)

    # Cannot publish a replica with the same ID as a local dataset and vice versa
    if dset is not None and dset.master_gateway != masterGateway:
        if dset.master_gateway is None:
            raise ESGPublishError("Dataset %s exists and is not a replica - delete it before publishing a replica of the same name."%dset.name)
        else:
            raise ESGPublishError("Dataset %s exists and is a replica. Use --replica or delete the existing dataset."%dset.name)

    createTime = datetime.datetime.now() # DatasetVersion creation_time
    if operation==CREATE_OP:
        # Create a new dataset
        info("Creating dataset: %s"%datasetName)
        dset = Dataset(datasetName, context.get('project', None), context.get('model', None), context.get('experiment', None), context.get('run_name', None), offline=offline, masterGateway=masterGateway)
        session.add(dset)

        # Create an initial dataset version
        existingVersion = 0
        eventFlag = CREATE_DATASET_EVENT
        addNewVersion = createDataset(dset, fileIterator, session, cfHandler, configOptions, aggregateDimensionName=aggregateDimensionName, offline=offline, progressCallback=progressCallback, stopEvent=stopEvent, extraFields=extraFields, masterGateway=masterGateway, **context)
        
    elif operation in [UPDATE_OP, REPLACE_OP]:
        existingVersion = dset.getVersion()
        eventFlag = UPDATE_DATASET_EVENT
        addNewVersion = updateDataset(dset, fileIterator, session, cfHandler, configOptions, aggregateDimensionName=aggregateDimensionName, offline=offline, progressCallback=progressCallback, stopEvent=stopEvent, extraFields=extraFields, replace=(operation==REPLACE_OP), **context)
         
    elif operation==RENAME_OP:
        existingVersion = dset.getVersion()
        eventFlag = UPDATE_DATASET_EVENT
        addNewVersion = renameFiles(dset, fileIterator, session, cfHandler, configOptions, aggregateDimensionName=aggregateDimensionName, offline=offline, progressCallback=progressCallback, stopEvent=stopEvent, extraFields=extraFields, **context)
         
    elif operation==DELETE_OP:
        existingVersion = dset.getVersion()
        eventFlag = UPDATE_DATASET_EVENT
        addNewVersion = deleteFiles(dset, fileIterator, session, cfHandler, configOptions, aggregateDimensionName=aggregateDimensionName, offline=offline, progressCallback=progressCallback, stopEvent=stopEvent, extraFields=extraFields, **context)
    else:
        raise ESGPublishError("Invalid dataset operation: %s"%`operation`)

    # Create a new dataset version if necessary
    if keepVersion:
        newVersion = existingVersion
    elif newVersion is None:
        newVersion = existingVersion + 1
        
    if addNewVersion and newVersion>existingVersion:
        info("New dataset version = %d"%newVersion)
        dsetVersion = DatasetVersion(newVersion, creation_time=createTime, comment=comment)
        dset.versions.append(dsetVersion)
        event = Event(datasetName, newVersion, eventFlag)
        dset.events.append(event)
    elif masterGateway is not None:     # Force version set on replication
        info("Dataset version = %d"%newVersion)
        dset.setVersion(newVersion)

    info("Adding file info to database")
    session.commit()
    session.close()

    return dset

def createDataset(dset, fileIterator, session, cfHandler, configOptions, aggregateDimensionName=None, offline=False, progressCallback=None, stopEvent=None, extraFields=None, masterGateway=None, **context):

    filelist = [item for item in fileIterator]
    nfiles = len(filelist)

    basedict = {}                       # file.base => 1
    varlocate = configOptions['variable_locate']
    checksumClient = configOptions['checksumClient']
    checksumType = configOptions['checksumType']
    seq = 0
    for path, sizet in filelist:
        size, mtime = sizet

        csum = None
        csumtype = checksumType
        if extraFields is not None:
            csum = extraFields.get((dset.name, path, 'checksum'), None)
            csumtype = extraFields.get((dset.name, path, 'checksum_type'), None)
        if csum is None and not offline and checksumClient is not None:
            csum = checksum(path, checksumClient)
            csumtype = checksumType

        # Create a file and version
        base = generateFileBase(path, basedict, dset.name)
        file = File(base, 'netCDF')
        basedict[base] = 1
        fileVersion = FileVersion(1, path, size, mod_time=mtime, checksum=csum, checksum_type=csumtype)
        file.versions.append(fileVersion)
        seq += 1

        dset.files.append(file)

        # Extract the dataset contents
        if not offline:
            info("Scanning %s"%path)
#             f = NetCDF.NetCDFFile(path)
            f = Cdunif.CdunifFile(path)
            extractFromFile(dset, f, file, session, cfHandler, aggdimName=aggregateDimensionName, varlocate=varlocate, **context)
            f.close()
        else:
            info("File %s is offline"%path)

        # Callback progress
        try:
            issueCallback(progressCallback, seq, nfiles, 0, 1, stopEvent=stopEvent)
        except:
            session.rollback()
            session.close()
            raise

    return True

def updateDataset(dset, fileIterator, session, cfHandler, configOptions, aggregateDimensionName=None, offline=False, progressCallback=None, stopEvent=None, extraFields=None, replace=False, **context):

    # Delete existing variables. They will be regenerated from the existing file variables and files.
    if replace:
        info("Replacing files in dataset: %s, version %d"%(dset.name, dset.getVersion()))
    else:
        info("Updating files in dataset: %s, version %d"%(dset.name, dset.getVersion()))
        
    for var in dset.variables:
        session.delete(var)

    # Create a file dictionary for the dataset
    #   filedict[path] = file
    basedict = {}
    locdict = {}
    deletedict = {}                     # Files that have been deleted.
    todelete = {}                       # Track which files will be deleted from a replace operation.
    for file in dset.files:
        location = file.getLocation()
        basedict[file.base] = 1         # Note: basedict has to include deleted files also.
        if file.deletion_time is not None:
            deletedict[location] = file
        else:
            locdict[location] = file
            todelete[location] = True

    filelist = [item for item in fileIterator]
    nfiles = len(filelist)

    varlocate = configOptions['variable_locate']
    checksumClient = configOptions['checksumClient']
    checksumType = configOptions['checksumType']
    seq = 0
    addNewDatasetVersion = False        # Add a new dataset version if any file has been modified
                                        # or deleted. Note: don't increment the dataset version
                                        # just because a new file was added, since the publisher
                                        # may be creating the dataset incrementally.
    for path, sizet in filelist:
        size, mtime=sizet
        csum = None
        csumtype = checksumType
        if extraFields is not None:
            csum = extraFields.get((dset.name, path, 'checksum'), None)
            csumtype = extraFields.get((dset.name, path, 'checksum_type'), None)
        if csum is None and not offline and checksumClient is not None:
            csum = checksum(path, checksumClient)
            csumtype = checksumType

        # oldpath is the value of 'from_file' if present
        if extraFields is not None:
            oldpath = extraFields.get((dset.name, path, 'from_file'), None)
        else:
            oldpath = None

        # If oldpath != path and exists in the dataset, delete it
        if oldpath is not None and oldpath!=path and locdict.has_key(oldpath):
            file = locdict[oldpath]
            file.delete(session)
            del locdict[oldpath]
            deletedict[oldpath] = file
            todelete[oldpath] = False   # Already been deleted
            addNewDatasetVersion = True

        # If the file was deleted, undelete it.
        if deletedict.has_key(path):
            info("Adding file %s"%path)
            file = deletedict[path]
            file.undelete()
            del deletedict[path]
            locdict[path] = file
            base = generateFileBase(path, basedict, dset.name)
            file.base = base
            basedict[base] = 1
            todelete[path] = False
            fileVersionNo = file.getVersion()+1
            addNewDatasetVersion = True

        # If the file is in the dataset ...
        elif locdict.has_key(path):
            file = locdict[path]
            todelete[path] = False

            # ... If the file matches the existing file version, no-op
            if compareFiles(file, path, size, offline, checksum=csum):
                info("File %s exists, skipping"%path)
                continue

            # ... Else bump the version number and add a new version
            else:
                fileVersionNo = file.getVersion() + 1
                file.deleteChildren(session) # The file is in the dataset but differs from
                                             # the file entry, so will be rescanned
                info("File %s version %d added"%(path, fileVersionNo))
                addNewDatasetVersion = True

        # Else add a new file, version 1
        else:
            if oldpath is None:
                info("Adding new file %s"%path)
            else:
                info("Replacing %s with %s"%(oldpath, path))
            base = generateFileBase(path, basedict, dset.name)
            file, fileVersionNo = FileFactory(base, path, session, deletedFileDictionary=deletedict)
            basedict[base] = 1
            dset.files.append(file)
            locdict[path] = file

        # Create a new file version
        fileVersion = FileVersion(fileVersionNo, path, size, mod_time=mtime, checksum=csum, checksum_type=csumtype)
        file.versions.append(fileVersion)

        seq += 1

        # Extract the dataset contents
        if not offline:
            info("Scanning %s"%path)
            f = Cdunif.CdunifFile(path)
            extractFromFile(dset, f, file, session, cfHandler, aggdimName=aggregateDimensionName, varlocate=varlocate, **context)
            f.close()
        else:
            info("File %s is offline"%path)

        # Callback progress
        try:
            issueCallback(progressCallback, seq, nfiles, 0, 1, stopEvent=stopEvent)
        except:
            session.rollback()
            session.close()
            raise

    # For a replace operation, remove old files not in the new dataset
    if replace:
        for path, value in todelete.items():
            if value:
                info("Deleting entry for file %s"%path)
                file = locdict[path]
                file.delete(session)
                addNewDatasetVersion = True

    return addNewDatasetVersion

def renameFiles(dset, fileIterator, session, cfHandler, configOptions, aggregateDimensionName=None, offline=False, progressCallback=None, stopEvent=None, keepVersion=False, newVersion=None, extraFields=None, **context):

    info("Renaming files in dataset: %s, version %d"%(dset.name, dset.getVersion()))
    for var in dset.variables:
        session.delete(var)

    # Create a file dictionary for the dataset
    basedict = {}
    locdict = {}
    for file in dset.files:
        basedict[file.base] = 1
        if not file.isDeleted():
            locdict[file.getLocation()] = file

    filelist = [item for item in fileIterator]
    nfiles = len(filelist)

    varlocate = configOptions['variable_locate']
    seq = 0
    for path, size in filelist:

        # If the file exists, rename it
        oldpath = None
        if extraFields is not None:
            oldpath = extraFields.get((dset.name, path, 'from_file'), None)
        if oldpath is None:
            info("No from_file field for file %s, skipping"%path)
            continue

        if locdict.has_key(oldpath):
            file = locdict[oldpath]
            fileVersion = file.versions[-1]
            if not os.path.exists(path):
                info("File not found: %s, skipping"%path)
                continue
            info("Renaming %s to %s"%(oldpath, path))
            del basedict[file.base]
            base = generateFileBase(path, basedict, dset.name)
            file.base = base
            basedict[base] = 1
            fileVersion.location = path
            del locdict[oldpath]
            locdict[path] = file
        else:
            info("File entry %s not found, skipping"%oldpath)
            continue

        seq += 1

        # Callback progress
        try:
            issueCallback(progressCallback, seq, nfiles, 0, 1, stopEvent=stopEvent)
        except:
            session.rollback()
            session.close()
            raise

    return False

def deleteFiles(dset, fileIterator, session, cfHandler, configOptions, aggregateDimensionName=None, offline=False, progressCallback=None, stopEvent=None, extraFields=None, **context):

    # Delete existing variables. They will be regenerated from the existing file variables and files.
    info("Deleting file entries for dataset: %s, version %d"%(dset.name, dset.getVersion()))
    for var in dset.variables:
        session.delete(var)

    # Create a file dictionary for the dataset
    locdict = {}
    for file in dset.getFiles():
        locdict[file.getLocation()] = file

    filelist = [item for item in fileIterator]
    nfiles = len(filelist)

    varlocate = configOptions['variable_locate']
    seq = 0
    addNewDatasetVersion = False
    for path, size in filelist:

        # If the file exists in the dataset, delete the file children (with cascade), and the file
        if locdict.has_key(path):
            file = locdict[path]
            info("Deleting entry for file %s"%path)
            file.delete(session)
            addNewDatasetVersion = True
        else:
            info("File entry not found: %s, skipping"%path)

        seq += 1

        # Callback progress
        try:
            issueCallback(progressCallback, seq, nfiles, 0, 1, stopEvent=stopEvent)
        except:
            session.rollback()
            session.close()
            raise

    return addNewDatasetVersion

def extractFromFile(dataset, openfile, fileobj, session, cfHandler, aggdimName=None, varlocate=None, **context):
    """
    Extract metadata from a file, add to a database.

    dataset
      The dataset instance.

    openfile
      An open netCDF file object.

    fileobj
      A (logical) file instance.

    session
      A database session instance.

    cfHandler
      A CF handler instance

    aggdimName
      The name of the dimension which is split across files, if any.

    varlocate
      List with elements [varname, pattern]. The variable will be extracted from the file only if the filename
      matches the pattern at the start. Example: [['ps', 'ps_'], ['xyz', 'xyz_']]

    context
      A dictionary with keys project, model, experiment, and run.

    """

    fileVersion = fileobj.versions[-1]

    # Get the aggregate dimension range
    aggvar = None
    if aggdimName is not None and openfile.variables.has_key(aggdimName):
        aggvar = openfile.variables[aggdimName]
        aggvarFirst = aggvar[0]
        aggvarLast = aggvar[-1]
        aggvarLen = len(aggvar)
        aggvarunits = map_to_charset(aggvar.units)
        if aggdimName.lower()=="time" or (hasattr(aggvar, "axis") and aggvar.axis=="T"):
            if abs(aggvarFirst)>1.e12 or abs(aggvarLast)>1.e12:
                dataset.warning("File: %s has time range: [%f, %f], looks bogus."%(fileVersion.location, aggvarFirst, aggvarLast), WARNING_LEVEL, AGGREGATE_MODULE)

    if aggdimName is not None and aggvar is None:
        info("Aggregate dimension not found: %s"%aggdimName)

    varlocatedict = {}
    if varlocate is not None:
        for varname, pattern in varlocate:
            varlocatedict[varname] = pattern

    # For each variable in the file:
    for varname, var in openfile.variables.items():
        debug("%s%s"%(varname, `var.shape`))

        # Check varlocate
        if varlocatedict.has_key(varname) and not re.match(varlocatedict[varname], os.path.basename(fileVersion.location)):
            debug("Skipping variable %s in %s"%(varname, fileVersion.location))
            continue

        # Create a file variable
        filevar = FileVariable(varname, getattr(var, 'long_name', None))
        fileobj.file_variables.append(filevar)

        # Create attributes:
        for attname in dir(var):
            if attname not in ['_FillValue', 'assignValue', 'getValue', 'getitem', 'getslice', 'setitem', 'setslice', 'typecode']:
                attvalue = getattr(var, attname)
                atttype, attlen = getTypeAndLen(attvalue)
                attribute = FileVariableAttribute(attname, map_to_charset(attvalue), atttype, attlen)
                filevar.attributes.append(attribute)
                debug('  %s.%s = %s'%(varname, attname, `attvalue`))

        # Create dimensions
        seq = 0
        for dimname, dimlen in zip(var.dimensions, var.shape):
            dimension = FileVariableDimension(dimname, dimlen, seq)
            filevar.dimensions.append(dimension)
            if dimname==aggdimName:
                filevar.aggdim_first = aggvarFirst
                filevar.aggdim_last = aggvarLast
                filevar.aggdim_units = aggvarunits
            seq += 1

        # Set coordinate axis range and type if applicable
        if len(var.shape)==1:
            if cfHandler.axisIsLatitude(filevar):
                filevar.coord_range = '%f:%f'%(var[0], var[-1])
                filevar.coord_type = 'Y'
            elif cfHandler.axisIsLongitude(filevar):
                filevar.coord_range = '%f:%f'%(var[0], var[-1])
                filevar.coord_type = 'X'
            elif cfHandler.axisIsLevel(filevar):
                filevar.coord_range = '%f:%f'%(var[0], var[-1])
                filevar.coord_type = 'Z'

    # Create global attribute
    for attname in dir(openfile):
        if attname not in ['close', 'createDimension', 'createVariable', 'flush', 'readDimension', 'sync']:
            attvalue = getattr(openfile, attname)
            atttype, attlen = getTypeAndLen(attvalue)
            attribute = FileAttribute(attname, map_to_charset(attvalue), atttype, attlen)
            fileobj.attributes.append(attribute)
            if attname=='tracking_id':
                fileVersion.tracking_id = attvalue
            debug('.%s = %s'%(attname, getattr(openfile, attname)))
        

def lookupVar(name, index):
    """Helper function for aggregateVariables:
    Lookup a variable in the dataset index."""
    varlist = index.get(name, None)
    if varlist is None:
        result = None
    else:
        result = varlist[0][0]
    return result

def lookupCoord(name, index, length):
    """Helper function for aggregateVariables:
    Lookup a coordinate variable in the dataset index."""
    varlist = index.get(name, None)
    if varlist is None:
        result = None
    else:
        for var, domain in varlist:
            if len(domain)>0:
                dlen = domain[0][1]
            else:
                dlen = 0
            
            if dlen==length:
                result = var
                break
        else:
            result = None
    return result

def lookupAttr(var, attname):
    """Helper function for aggregateVariables:
    Lookup an attribute of the variable."""
    result = None
    if var is not None:
        for attr in var.attributes:
            if attr.name==attname:
                result = attr.value
                break
    return result

def createAggregateVar(var, varattr, aggregateDimensionName):
    """Helper function for aggregateVariables:
    Create an aggregate dimension or bounds variable associated with a variable."""
    aggVar = None
    for filevar in var.file_variables:
        if hasattr(filevar.file, varattr):
            aggfilevar = getattr(filevar.file, varattr)
            if aggVar is None:
                aggVar = Variable(aggfilevar.short_name, aggfilevar.long_name)
                aggVar.domain = ((aggregateDimensionName, 0, 0),)+tuple(aggfilevar.domain[1:]) # Zero out aggregate dimension length
                # Create attributes
                for fvattribute in aggfilevar.attributes:
                    attribute = VariableAttribute(fvattribute.name, map_to_charset(fvattribute.value), fvattribute.datatype, fvattribute.length)
                    aggVar.attributes.append(attribute)

            aggVar.file_variables.append(aggfilevar)
    return aggVar

def aggregateVariables(datasetName, dbSession, aggregateDimensionName=None, cfHandler=None, progressCallback=None, stopEvent=None, datasetInstance=None):
    """
    Aggregate file variables into variables, and add to the database. Populates the database tables:

    - variable
    - file_variable
    - associated attribute tables

    Returns a Dataset object.

    datasetName
      String dataset identifier.

    dbSession
      A database Session.

    aggregateDimensionName
      The name of the dimension across which the dataset is aggregated, if any.

    cfHandler
      A CFHandler to validate standard names, etc.

    progressCallback
      Tuple (callback, initial, final) where ``callback`` is a function of the form ``callback(progress)``, ``initial`` is the initial value reported, ``final`` is the final value reported.

    stopEvent
      Object with boolean attribute ``stop_extract`` (for example, ``utility.StopEvent``). If set to True (in another thread) the extraction is stopped.

    datasetInstance
      Existing dataset instance. If not provided, the instance is regenerated from the database.

    """

    session = dbSession()
    info("Aggregating variables")

    # Lookup the dataset
    if datasetInstance is None:
        dset = session.query(Dataset).filter_by(name=datasetName).first()
        for variable in dset.variables:
            session.delete(variable)
        for attrname, attr in dset.attributes.items():
            if not attr.is_category:
                del dset.attributes[attrname]
        session.commit()
        dset.variables = []
    else:
        dset = datasetInstance
        # session.save_or_update(dset)
        session.add(dset)
    if dset is None:
        raise ESGPublishError("Dataset not found: %s"%datasetName)

    dsetindex = {}                      # dsetindex[varname] = [(variable, domain), (variable, domain), ...]
                                        #   where domain = ((dim0, len0, 0), (dim1, len1, 1), ...)
                                        #   Note:
                                        #     (1) If a dim0 is the aggregate dimension, len0 is 0
                                        #     (2) A dsetindex entry will only have multiple tuples if
                                        #         there are more than one variable with the same name
                                        #         and different domains.
    varindex = {}                       # varindex[(varname, domain, attrname)] = attribute
    globalAttrIndex = {}                # globalAttrIndex[attname] = attval, for global attributes
    dsetvars = []

    # Create variables
    seq = 0
    nfiles = len(dset.getFiles())
    for file in dset.getFiles():
        for filevar in file.file_variables:

            # Get the filevar and variable domain
            fvdomain = map(lambda x: (x.name, x.length, x.seq), filevar.dimensions)
            fvdomain.sort(lambda x,y: cmp(x[SEQ], y[SEQ]))
            filevar.domain = fvdomain
            if len(fvdomain)>0 and fvdomain[0][0]==aggregateDimensionName:
                vardomain = ((aggregateDimensionName, 0, 0),)+tuple(fvdomain[1:]) # Zero out aggregate dimension length
            else:
                vardomain = tuple(fvdomain)

            # Create the variable if necessary
            varlist = dsetindex.get(filevar.short_name, None)
            if varlist is None or vardomain not in [item[1] for item in varlist]:
                var = Variable(filevar.short_name, filevar.long_name)
                var.domain = vardomain

                # Record coordinate variable range if applicable
                if filevar.coord_type is not None:
                    var.coord_type = filevar.coord_type
                    var.coord_range = filevar.coord_range
                    
                dsetvars.append(var)
                if varlist is None:
                    dsetindex[var.short_name] = [(var, vardomain)]
                else:
                    varlist.append((var, vardomain))
            else:
                for tvar, domain in varlist:
                    if domain==vardomain:
                        var = tvar
                        break

            # Attach the file variable to the variable
            var.file_variables.append(filevar)

            # Create attributes
            for fvattribute in filevar.attributes:
                vattribute = varindex.get((var.short_name, vardomain, fvattribute.name), None)
                if vattribute is None:
                    attribute = VariableAttribute(fvattribute.name, map_to_charset(fvattribute.value), fvattribute.datatype, fvattribute.length)
                    var.attributes.append(attribute)
                    varindex[(var.short_name, vardomain, attribute.name)] = attribute
                    if attribute.name == 'units':
                        var.units = attribute.value

        # Create global attributes
        for fileattr in file.attributes:
            fattribute = globalAttrIndex.get(fileattr.name, None)
            if fattribute is None and fileattr.name not in ['readDimension']:
                attribute = DatasetAttribute(fileattr.name, map_to_charset(fileattr.value), fileattr.datatype, fileattr.length)
                dset.attributes[attribute.name] = attribute
                globalAttrIndex[attribute.name] = attribute
        seq += 1
        try:
            issueCallback(progressCallback, seq, nfiles, 0, 0.25, stopEvent=stopEvent)
        except:
            session.rollback()
            session.close()
            raise

    # Find the aggregation dimension bounds variable, if any
    aggDim = lookupVar(aggregateDimensionName, dsetindex)
    boundsName = lookupAttr(aggDim, 'bounds')
    aggUnits = lookupAttr(aggDim, 'units')
    aggDimBounds = lookupVar(boundsName, dsetindex)

    # Set calendar for time aggregation
    isTime = cfHandler.axisIsTime(aggDim)
    if isTime:
        calendar = cfHandler.getCalendarTag(aggDim)
        if calendar is None:
            calendar = "gregorian"
    else:
        calendar = None
    dset.calendar = calendar
    dset.aggdim_name = aggregateDimensionName
    dset.aggdim_units = aggUnits
    try:
        cdcalendar = tagToCalendar[calendar]
    except:
        cdcalendar = DefaultCalendar

    # Add the non-aggregate dimension variables to the dataset
    for var in dsetvars:
        if var not in [aggDim, aggDimBounds]:
            dset.variables.append(var)

    # Set coordinate ranges
    for var in dset.variables:
        for name, length, seq in var.domain:
            if name==aggregateDimensionName:
                continue
            dvar = lookupCoord(name, dsetindex, length)
            if dvar is not None:
                units = lookupAttr(dvar, 'units')
                if hasattr(dvar, 'coord_type'):
                    if dvar.coord_type=='X':
                        var.eastwest_range = dvar.coord_range+':'+units
                    elif dvar.coord_type=='Y':
                        var.northsouth_range = dvar.coord_range+':'+units
                    elif dvar.coord_type=='Z':
                        var.updown_range = dvar.coord_range+':'+units

    # Attach aggregate dimension filevars to files
    if aggDim is not None:
        for filevar in aggDim.file_variables:
            filevar.file.aggDim = filevar
    if aggDimBounds is not None:
        for filevar in aggDimBounds.file_variables:
            filevar.file.aggDimBounds = filevar

    # Combine aggregate dimensions:
    # Scan all variables with the aggregate dimension in the domain. For each such variable,
    # create an aggregate dimension variable, and bounds if needed.
    timevars = []
    for var in dset.variables:
        if len(var.domain)>0 and aggregateDimensionName==var.domain[0][NAME]:
            aggVar = createAggregateVar(var, 'aggDim', aggregateDimensionName)
            aggBoundsVar = createAggregateVar(var, 'aggDimBounds', aggregateDimensionName)
            if aggVar is not None:
                aggVar.units = aggUnits
                timevars.append(aggVar)
            if aggBoundsVar is not None:
                timevars.append(aggBoundsVar)

    # Create variable dimensions, aggregating the agg dimension
    debug("Creating dimensions")
    i = 0
    nvars = len(dset.variables+timevars)
    for var in dset.variables+timevars:
        vardomain = var.domain

        # Increment aggregate dimension length
        if len(vardomain)>0 and aggregateDimensionName==vardomain[0][NAME]:
            for filevar in var.file_variables:
                fvdomain = filevar.domain
                vardomain = ((aggregateDimensionName, vardomain[0][LENGTH]+fvdomain[0][LENGTH], vardomain[0][SEQ]),)+tuple(vardomain[1:])
        var.domain = vardomain

        # Create the variable domain
        for name, length, seq in vardomain:
            dimension = VariableDimension(name, length, seq)
            var.dimensions.append(dimension)
        i += 1
        try:
            issueCallback(progressCallback, i, nvars, 0.25, 0.5, stopEvent=stopEvent)
        except:
            session.rollback()
            session.close()
            raise

    # Set variable aggregate dimension ranges
    debug("Setting aggregate dimension ranges")
    seq = 0
    nvars = len(dset.variables+timevars)
    for var in dset.variables+timevars:
        vardomain = var.domain
        if len(vardomain)>0 and vardomain[0][NAME]==aggregateDimensionName:

            # Adjust times so they have consistent base units
            try:
                filevarRanges = map(lambda x: (x.file.getLocation(),
                                               reltime(x.aggdim_first, x.aggdim_units).torel(aggUnits, cdcalendar).value,
                                               reltime(x.aggdim_last, x.aggdim_units).torel(aggUnits, cdcalendar).value),
                                    var.file_variables)
            except:
                for fv in var.file_variables:
                    try:
                        firstt = reltime(fv.aggdim_first, fv.aggdim_units).torel(aggUnits, cdcalendar).value
                        lastt = reltime(fv.aggdim_last, fv.aggdim_units).torel(aggUnits, cdcalendar).value
                    except:
                        error("path=%s, Invalid aggregation dimension value or units: first_value=%f, last_value=%f, units=%s"%(fv.file.getLocation(), fv.aggdim_first, fv.aggdim_last, fv.aggdim_units))
                        raise

            mono = cmp(filevarRanges[0][1], filevarRanges[0][2])
            if mono<=0:
                filevarRanges.sort(lambda x, y: cmp(x[1], y[1]))
            else:
                filevarRanges.sort(lambda x, y: -cmp(x[1], y[1]))

            # Check that ranges don't overlap. Aggregate dimension and bounds may be duplicated.
            lastValues = numpy.array(map(lambda x: x[2], filevarRanges))
            firstValues = numpy.array(map(lambda x: x[1], filevarRanges))
            if (var not in [aggDim, aggDimBounds]):
                if mono<=0:
                    compare = (lastValues[0:-1] >= firstValues[1:])
                else:
                    compare = (lastValues[0:-1] <= firstValues[1:])
                if compare.any():
                    overlaps = compare.nonzero()[0]
                    dset.warning("Variable %s is duplicated:"%(var.short_name), WARNING_LEVEL, AGGREGATE_MODULE)
                    var.has_errors = True
                    nprint = min(len(overlaps), 3)
                    for i in range(nprint):
                        dset.warning("  %s: (%d, %d)"%filevarRanges[overlaps[i]], WARNING_LEVEL, AGGREGATE_MODULE)
                        dset.warning("  %s: (%d, %d)"%filevarRanges[overlaps[i]+1], WARNING_LEVEL, AGGREGATE_MODULE)
                    if len(overlaps)>nprint:
                        dset.warning("    ... (%d duplications total)"%len(overlaps), WARNING_LEVEL, AGGREGATE_MODULE)

                # Check monotonicity of last values.
                else:
                    if mono<=0:
                        compare = (lastValues[0:-1] < lastValues[1:]).all()
                    else:
                        compare = (lastValues[0:-1] > lastValues[1:]).all()
                    if not compare:
                        dset.warning("File aggregate dimension ranges are not monotonic for variable %s: %s"%(var.short_name, `filevarRanges`), WARNING_LEVEL, AGGREGATE_MODULE)
                        var.has_errors = True

            var.aggdim_first = firstValues[0]
            var.aggdim_last = lastValues[-1]
        seq += 1
        try:
            issueCallback(progressCallback, seq, nvars, 0.5, 0.75, stopEvent=stopEvent)
        except:
            session.rollback()
            session.close()
            raise

    # Combine identical aggregate dimensions and add to the dataset
    timevardict = {}
    for var in timevars:
        timevardict[(var.short_name, var.domain, var.aggdim_first, var.aggdim_last)] = var

    for var in timevardict.values():
        dset.variables.append(var)
        
    # Validate standard names
    seq = 0
    nvars = len(dset.variables)
    for var in dset.variables:
        attr = lookupAttr(var, 'standard_name')
        if (attr is not None):
            if (cfHandler is not None) and (not cfHandler.validateStandardName(attr)):
                info("Invalid standard name: %s for variable %s"%(attr, var.short_name))
            else:
                var.standard_name = attr
        seq += 1
        try:
            issueCallback(progressCallback, seq, nvars, 0.75, 1.0, stopEvent=stopEvent)
        except:
            session.rollback()
            session.close()
            raise

    debug("Adding variable info to database")
    session.commit()
    session.close()
