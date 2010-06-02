"""Utility routines for publishing."""

import os
import stat
import numpy
import types
import string
import glob
import re
import logging
import subprocess
from cdms2 import Cdunif
from esgcet.config import getHandler, getHandlerByName, CFHandler, splitLine
from esgcet.exceptions import *
from esgcet.messaging import debug, info, warning, error, critical, exception

def getTypeAndLen(att):
    """Get the type descriptor of an attribute.
    """
    if isinstance(att, numpy.ndarray):
        result = (att.dtype.char, len(att))
    elif isinstance(att, types.StringType):
        result = ('S', 1)
    elif isinstance(att, types.FloatType):
        result = ('d', 1)
    else:
        result = ('O', 1)
    return result
    
def processIterator(command, commandArgs, filefilt=None, offline=False):
    """Create an iterator from an external process.

    Returns an iterator that returns (path, size) at each iteration.
    
    command
      Command string to execute the process - for example,
      "/some/python/bin/hsils.py".  The process must write to stdout,
      a blank-separated "path size" on each line.

    commandArgs
      String arguments to the process.

    filefilt
      A regular expression as defined in the Python re module. Each file returned has basename matching the filter.

    offline
      Boolean, if True don't try to stat files.

    """

    try:
        f = subprocess.Popen(command+" "+commandArgs, shell=True, stdout=subprocess.PIPE).stdout
    except:
        error("Error running command '%s %s', check configuration option 'offline_lister_executable'."%(command, commandArgs))
        raise
    for path, size in filelistIterator_1(f, filefilt, offline=offline):
        yield (path, size)
    f.close()
    return

def processNodeMatchIterator(command, commandArgs, handler, filefilt=None, datasetName=None, offline=False):
    """Create an iterator from an external process, matching a list of node filters to each path.
    The node filters are generated from the ``directory_format`` option associated with the project
    represented by the handler.

    Returns an iterator that returns (dataset_name, path, size) at each iteration.
    
    command
      Command string to execute the process - for example,
      "/some/python/bin/hsils.py".  The process must write to stdout,
      a blank-separated "path size" on each line.

    commandArgs
      String arguments to the process.

    handler
      Project handler.

    filefilt
      A regular expression as defined in the Python re module. Each file returned has basename matching the filter.

    datasetName
      String dataset name. If specified, always return this as the first item of the tuple, and ignore ``nodefilts``.

    offline
      Boolean, if True don't try to stat files.

    """

    nodefilts = handler.getDirectoryFormatFilters()
    idfields, formats = handler.getDatasetIdFields()

    idCache = {}
    for path, size in processIterator(command, commandArgs, filefilt=filefilt, offline=offline):

        # Check if any node filter matches the path
        if datasetName is None:

            direc = os.path.dirname(path)

            # Check if we have already matched this directory
            if idCache.has_key(direc):
                datasetId = idCache[direc]
                yield (datasetId, path, size)
                continue

            foundOne = False
            for filt in nodefilts:
                result = re.match(filt, direc)
                if result is not None:
                    foundOne = True
                    break

            if foundOne:
                groupdict = result.groupdict()
                if not groupdict.has_key('project'):
                    groupdict['project'] = handler.name
                datasetId = handler.generateDatasetId('dataset_id', idfields, groupdict, multiformat=formats)
                idCache[direc] = datasetId
                yield (datasetId, path, size)
                continue
            else:
                raise ESGPublishError("No match for path=%s, must specify a dataset name"%path)

        # If the dataset name was specified, just use it.
        else:
            yield (datasetName, path, size)

def filelistIterator(filelist, filefilt=None):
    """Create an iterator from a filelist.

    Returns an iterator that returns (path, size) at each iteration. If sizes are omitted from the file, the sizes are inserted, provided the files are online.
    
    filelist
      Path to a file containing a list of files. Each line of filelist contains an absolute filename and optional file size, blank-separated.

    filefilt
      A regular expression as defined in the Python re module. Each file returned has basename matching the filter.

    offline
      Boolean, if True don't try to stat files.

    """
    f = open(filelist)
    for path, size in filelistIterator_1(f, filefilt):
        yield (path, size)
    f.close()
    return

def filelistIterator_1(f, filefilt, offline=False):
    line = f.readline()
    while line:
        line = line.strip()
        if line[0]=='#':
            line = f.readline()
            continue
        fields = line.split()
        if len(fields)==1:
            path = fields[0]
            if not offline:
                stats = os.stat(path)
                size = stats[stat.ST_SIZE]
                mtime = stats[stat.ST_MTIME]
            else:
                size = 0
                mtime = None
            if filefilt is None or re.match(filefilt, os.path.basename(path)) is not None:
                yield (path, (size, mtime))
        elif len(fields)==2:
            try:
                path = fields[0]
                size = string.atol(fields[1])
                if not offline:
                    mtime = os.stat(path)[stat.ST_MTIME]
                else:
                    mtime = None
            except:
                raise ESGPublishError("Invalid filelist entry in %s: %s"%(f.name, line))
            if filefilt is None or re.match(filefilt, os.path.basename(path)) is not None:
                yield (path, (size, mtime))
        else:
            raise ESGPublishError("Filelist %s has invalid format."%filelist)
        line = f.readline()

def fnmatchIterator(pathexp):
    """Create an iterator from a Unix-style path expression.

    Returns an iterator that returns (path, size) at each iteration.

    pathexp
      A Unix-style path expression, which may include wildcard characters.
    """
    pathlist = glob.glob(pathexp)
    for path in pathlist:
        stats = os.stat(path)
        size = stats[stat.ST_SIZE]
        mtime = stats[stat.ST_MTIME]
        yield (path, (size, mtime))
    return

def fnIterator(pathlist):
    """Create an iterator from a list of paths.

    Returns an iterator that returns (path, size) at each iteration.

    pathlist
      A list or tuple of file paths.
    """
    for path in pathlist:
        stats = os.stat(path)
        size = stats[stat.ST_SIZE]
        mtime = stats[stat.ST_MTIME]
        yield (path, (size, mtime))
    return

def directoryIterator(top, filefilt=None, followSymLinks=True, followSubdirectories=True):
    """Create an iterator over all files under a directory.
    
    Returns an iterator that returns (path, size) at each iteration, for each file in the *top* directory or a subdirectory of *top*.

    top
      Top level directory name.

    filefilt
      A regular expression as defined in the Python re module. Each file returned has basename matching the filter.

    followSymLinks
      Boolean flag. Symbolic links are followed unless followSymLinks is False.

    followSubdirectories
      Boolean flag. If true then recurse through subdirectories.
    """

    try:
        names = os.listdir(top)
    except os.error:
        return

    for basename in names:
        name = os.path.join(top, basename)
        try:
            if followSymLinks:
                st = os.stat(name)
            else:
                st = os.lstat(name)
        except os.error:
            continue

        # Search regular files in top directory
        if stat.S_ISREG(st.st_mode):
            if re.match(filefilt, basename) is not None:
                yield (name, (st.st_size, st.st_mtime))
            
        # Search subdirectories
        elif followSubdirectories and stat.S_ISDIR(st.st_mode):
            for path, size in directoryIterator(name, filefilt):
                yield (path, size)

    return

def multiDirectoryIterator(top, filefilt=None, followSymLinks=True):
    """Same as **directoryIterator** for a list of directories.

    Returns an iterator that returns (path, size) at each iteration, for each file under each directory in *top*.

    top
      A list or tuple of top level directory names.

    filefilt
      A regular expression as defined in the Python re module. Each file returned has basename matching the filter.

    followSymLinks
      Boolean flag. Symbolic links are followed unless followSymLinks is False.
    """

    for direc in top:
        for path, size in directoryIterator(direc, filefilt, followSymLinks):
                yield (path, size)

def nodeIterator(top, nodefilt, filefilt, followSymLinks=True):
    """Generate an iterator over non-empty directories that match a pattern.

    Returns an iterator that returns a tuple (*path*, *sample_file*, *groupdict*) at each iteration, where:

    - *path* is the node (directory) path
    - *sample_file* is a file in the node that matches the file filter
    - *groupdict* is the group dictionary generated by the match. For example, if *nodefilt* contains a named group '(?P<model>) that matches 'some_value', then *groupdict* maps 'model' => 'some_value'

    top
      A list or tuple of top level directory names.

    nodefilt
      A regular expression as defined in the Python re module. Each node returned matches the expression.
      May also be a list of regular expressions, in which case each node returned matches at least one expression
      in the list.

    filefilt
      A regular expression as defined in the Python re module. Each sample file returned has basename matching the filter.

    followSymLinks
      Boolean flag. Symbolic links are followed unless followSymLinks is False.

    """

    try:
        names = os.listdir(top)
    except os.error:
        return

    if type(nodefilt) is not type([]):
        nodefilt = [nodefilt]

    foundOne = False
    for basename in names:
        name = os.path.join(top, basename)
        try:
            if followSymLinks:
                st = os.stat(name)
            else:
                st = os.lstat(name)
        except os.error:
            continue

        # Search regular files in top directory
        if stat.S_ISREG(st.st_mode):
            if not foundOne:

                # Find the first node filter that matches
                for filt in nodefilt:
                    result = re.match(filt, top)
                    if result is not None:
                        break
                    
                # If the node pattern matches and the file not a directory and the file filter matches:
                if (result is not None) and (re.match(filefilt, basename) is not None):
                    groupdict = result.groupdict()
                    foundOne = True
                    yield (top, basename, groupdict)
            
        # Search subdirectories
        elif stat.S_ISDIR(st.st_mode):
            for nodepath, filepath, gdict in nodeIterator(name, nodefilt, filefilt, followSymLinks=followSymLinks):
                yield (nodepath, filepath, gdict)

    return

# Progress gui helpers

class StopEvent(object):

    def __init__(self, stop_extract=False):
        self.stop_extract = stop_extract

def progressCallback(progress):
    """Sample progress callback. ``progress`` is a number in the range [0,100] """
    print 'Progress: %f'%progress

def linmap(init, final, frac):
    return (final-init)*frac + init

def issueCallback(callbackTuple, i, n, subi, subj, stopEvent=None):
    """
    Issue a progress callback.

    callbackTuple
      Tuple of the form (callback, initial, final) where ``callback`` is a function of the form ``callback(progress)`` and ``progress`` is in the range ``[initial, final]``.

    i
      Iteration counter,

    n
      Total number of iterations.

    subi
      Initial range value for this callback. Must be between ``initial`` and ``final``.

    subj
      Final range value for this callback. Must be between ``initial`` and ``final``.

    stopEvent
      Raise ESGStopPublication exception if stopEvent.stop_extract is True. May be used by a progress GUI running in a different thread.

    Example::

      callbackTuple = (progressCallback, 0, 100)
      issueCallback(progressCallback, 5, 10, 0.5, 0.75)

    states that the progressCallback will take values in the range [0,100], this set of callbacks will issue values in the range [50,75], and this particular call will generate a progress value of 62.5.
    """
    if callbackTuple is not None:
        callback, initial, final = callbackTuple
        init2 = linmap(initial, final, float(subi))
        final2 = linmap(initial, final, float(subj))
        callback(linmap(init2, final2, float(i)/n))

    if stopEvent is not None and stopEvent.stop_extract:
        raise ESGStopPublication("Publication stopped")
    
def readDatasetMap(mappath, parse_extra_fields=False):
    """Read a dataset map.

    A dataset map is a text file, each line having the form:

    dataset_id | absolute_file_path | size [ | ``from_file``=<path> [ | extra_field=extra_value ...]]

    Returns (if parse_extra_fields=False) a dataset map - a dictionary: dataset_id => [(path, size), (path, size), ...]
    If parse_extra_fields=True, returns a tuple (dataset_map, extra_dictionary). See parse_extra_fields.
      

    mappath
      Name of the dataset map.

    parse_extra_fields
      Boolean; if True then parse any extra fields of the form *extra_field=extra_value*, and return
      a dictionary with items of the form:

      extrafields[(dataset_id, absolute_file_path, *field_name*)] => field_value

      where *field_name* is one of:

      - ``from_file``
      - ``mod_time``

    """
    datasetMap = {}
    extraFieldMap = {}
    mapfile = open(mappath)
    for line in mapfile.readlines():
        if line[0]=='#' or line.strip()=='':
            continue

        if parse_extra_fields:
            fields = splitLine(line)
            datasetId, path, size = fields[0:3]
            if len(fields)>3:
                for field in fields[3:]:
                    efield, evalue = field.split('=')
                    extraFieldMap[(datasetId, path, efield.strip())] = evalue.strip()
            if datasetMap.has_key(datasetId):
                datasetMap[datasetId].append((path, size))
            else:
                datasetMap[datasetId] = [(path, size)]
        else:
            datasetId, path, size = splitLine(line)[0:3]
            if datasetMap.has_key(datasetId):
                datasetMap[datasetId].append((path, size))
            else:
                datasetMap[datasetId] = [(path, size)]

    mapfile.close()

    for value in datasetMap.values():
        value.sort()
        
    if parse_extra_fields:
        return (datasetMap, extraFieldMap)
    else:
        return datasetMap

def datasetMapIterator(datasetMap, datasetId, extraFields=None, offline=False):
    """Create an iterator from a dataset map entry.

    Returns an iterator that returns (path, size) at each iteration. If sizes are omitted from the file, the sizes are inserted, provided the files are online.
    
    datasetMap
      Dictionary dataset map as returned by **readDatasetMap**.

    datasetId
      Dataset string identifier.
      
    extraFields
      Extra dataset map fields, as from **readDatasetMap**.

    offline
      Boolean, if true don't try to stat the file.

    """

    for path, csize in datasetMap[datasetId]:
        csize = csize.strip()
        if csize=="":
            size = os.stat(path)[stat.ST_SIZE]
        else:
            size = string.atol(csize)
        mtime = None
        if extraFields is not None:
            mtime = extraFields.get((datasetId, path, 'mod_time'))
        if mtime is None:
            if not offline:
                mtime = os.stat(path)[stat.ST_MTIME]
            else:
                mtime = None
        else:
            mtime = float(mtime)
        yield (path, (size, mtime))

def iterateOverDatasets(projectName, dmap, directoryMap, datasetNames, Session, aggregateDimension, operation, filefilt, initcontext, offlineArg, properties, testProgress1=None, testProgress2=None, handlerDictionary=None, keepVersion=False, newVersion=None, extraFields=None, masterGateway=None, comment=None):
    """
    Scan and aggregate (if possible) a list of datasets. The datasets and associated files are specified
    in one of two ways: either as a *dataset map* (see ``dmap``) or a *directory map* (see ``directoryMap``).
    All dataset information is persisted in the database. This is a 'helper' routine for esgpublish[_gui].

    Returns a list of persistent Dataset instances.

    projectName
      String name of the project associated with the datasets. If None, it is determined by the first handler found that
      can open a sample file from the dataset.
      
    dmap
      A dictionary dataset map, as returned from ``readDatasetMap``. If None, ``directoryMap`` must be specified.

    directoryMap
      A dictionary directory map, as returned from ``ProjectHandler.generateDirectoryMap``.
      
    datasetNames
      A list of dataset names identifying the datasets to be scanned.

    Session
      An SQLAlchemy Session.
      
    aggregateDimension
      Name of the dimension on which to aggregate the datasets.

    operation
      The publication operation, one of esgcet.publish.CREATE_OP, DELETE_OP, RENAME_OP, UPDATE_OP

    filefilt
      String regular expression as defined by the Python re module. If a ``directoryMap`` is specified, only files whose
      basename matches the filter are scanned. If ``dmap`` is specified, the filter is ignored.

    initcontext
      Dictionary of initial context values for *all* datasets. These values will override metadata contained in datafiles.
      Contrast with ``properties``.

    offlineArg
      Boolean flag or dictionary
      
      If a boolean flag: if True the files are treated as offline (not local) and are not scanned or aggregated. The associated
      metadata will be a minimal set including file name and size.

      If a dictionary, maps dataset_name => offline flag

    properties
      Dictionary of property/value pairs. The properties must be configured in the initialization file section
      corresponding to the project, and do not override existing metadata values. Contrast with ``initcontext``.

    testProgress1=None
      Tuple (callback, initial, final) where ``callback`` is a function of the form *callback(progress)*,
      ``initial`` is the initial value reported, ``final`` is the final value reported. This callback applies only to
      the scan phase.

    testProgress2=None
      Tuple (callback, initial, final) where ``callback`` is a function of the form *callback(progress)*,
      ``initial`` is the initial value reported, ``final`` is the final value reported. This callback applies only to
      the aggregation phase.

    handlerDictionary=None
      A dictionary mapping datasetName => handler. If None, handlers are determined by project name.

    keepVersion
      Boolean, True if the dataset version should not be incremented.

    newVersion
      Set the new version number explicitly. By default the version number is incremented by 1. See keepVersion.

    extraFields
      Extra dataset map fields, as from **readDatasetMap**.

    masterGateway
      The gateway that owns the master copy of the datasets. If None, the dataset is not replicated.
      Otherwise the TDS catalog is written with a 'master_gateway' property, flagging the dataset(s)
      as replicated.

    comment=None:
      String comment to associate with new datasets created.

    """
    from esgcet.publish import extractFromDataset, aggregateVariables

    prevProject = None
    datasets = []
    ct = len(datasetNames)
    for iloop in range(ct): 
        datasetName = datasetNames[iloop]
        context = initcontext.copy()

        # Get offline flag
        if type(offlineArg) is dict:
            offline = offlineArg[datasetName]
        else:
            offline = offlineArg

        # Get a file iterator and sample file
        if dmap is not None:
            if len(dmap[datasetName])==0:
                warning("No files specified for dataset %s"%datasetName)
                continue
            firstFile = dmap[datasetName][0][0]
            fileiter = datasetMapIterator(dmap, datasetName, extraFields=extraFields, offline=offlineArg)
        else:
            direcTuples = directoryMap[datasetName]
            firstDirec, sampleFile = direcTuples[0]
            firstFile = os.path.join(firstDirec, sampleFile)
            fileiter  = multiDirectoryIterator([direc for direc, sampfile in direcTuples], filefilt)

        # If the project is not specified, try to read it from the first file
        if handlerDictionary is not None and handlerDictionary.has_key(datasetName):
            handler = handlerDictionary[datasetName]
        elif projectName is not None:
            handler = getHandlerByName(projectName, firstFile, Session, validate=True, offline=offline)
        else:
            handler = getHandler(firstFile, Session, validate=True)
            if handler is None:
                raise ESGPublishError("No project found in file %s, specify with --project."%firstFile)
            projectName = handler.name
        if prevProject is not None and projectName!=prevProject:
            raise ESGPublishError("Multiple projects found: %s, %s. Can only publish from one project"%(prevProject, projectName))
        prevProject = projectName

        # Generate the initial context from the dataset name
        context = handler.parseDatasetName(datasetName, context)

        # Load the rest of the context from the first file, if possible
        context = handler.getContext(**context)

        # Add properties from the command line
        fieldNames = handler.getFieldNames()
        for name, value in properties.items():
            if name not in fieldNames:
                warning('Property not configured: %s, was ignored'%name)
            else:
                context[name] = value

        # Update the handler context and fill in default values
        handler.updateContext(context, True)

        # Ensure that fields are valid:
        try:
            handler.validateContext(context)
        except ESGInvalidMandatoryField:
            if offline:
                error("Dataset id has a missing or invalid mandatory field")
            raise

        # Create a CFHandler for validation of standard names, checking time axes, etc.
        cfHandler = CFHandler(Session)

        dataset=None
        if testProgress1 is not None:
           testProgress1[1] = (100./ct)*iloop
           if not offline:
              testProgress1[2] = (100./ct)*iloop + (50./ct)
           else:
              testProgress1[2] = (100./ct)*iloop + (100./ct)
        dataset = extractFromDataset(datasetName, fileiter, Session, cfHandler, aggregateDimensionName=aggregateDimension, offline=offline, operation=operation, progressCallback=testProgress1, keepVersion=keepVersion, newVersion=newVersion, extraFields=extraFields, masterGateway=masterGateway, comment=comment, **context)

        if not offline:
            if testProgress2 is not None:
               testProgress2[1] = (100./ct)*iloop + 50./ct
               testProgress2[2] = (100./ct)*(iloop + 1)
            aggregateVariables(datasetName, Session, aggregateDimensionName=aggregateDimension, cfHandler=cfHandler, progressCallback=testProgress2, datasetInstance=dataset)

        # Save the context with the dataset, so that it can be searched later
        handler.saveContext(datasetName, Session)
        datasets.append(dataset)

    return datasets

def isConstant(ar):
    if len(ar)>1:
        return numpy.allclose(ar, ar[0])
    else:
        return True

def isRegular(ar):
    if len(ar)>1:
        return isConstant(ar[1:]-ar[:-1])
    else:
        return True

def whereIrregular(ar, atol=1.e-8, rtol=1.e-5):
    inds = numpy.arange(len(ar))
    diff = ar[1:]-ar[:-1]
    step = diff[0]
    cond = abs(diff-step)>=(atol + abs(step)*rtol)
    return inds[cond]

def compareFiles(fileobj, path, size, offline, checksum=None):
    """Compare a database file object and physical file.

    Returns True iff the files are the same.
    
    fileobj
      File object

    path
      String path of file to compare.
      
    size
      Size of physical file in bytes.

    offline
      Boolean, True iff the path is offline

    checksum
      String, checksum of the physical file
    """

    # If checksums are defined for both files, it is definitive
    # to compare them.
    fileVersion = fileobj.versions[-1]
    if checksum is not None and fileVersion.checksum is not None:
        return fileVersion.checksum==checksum

    # If file sizes differ, files are different.
    if fileVersion.size!=size:
        return False

    # For offline datasets, only compare sizes
    if offline:
        return True

    f = Cdunif.CdunifFile(path)
    if hasattr(f, 'tracking_id'):
        trackingId = f.tracking_id
    else:
        trackingId = None
    f.close()

    # If at least one file has a tracking ID, and they differ,
    # files are different.
    if fileVersion.tracking_id != trackingId:
        return False

    # If tracking IDs are defined and equal, files are the same.
    if trackingId is not None and fileVersion.tracking_id == trackingId:
        return True

    # If the checksum is defined for the new file, but not the old,
    # assume the files differ, so that the new checksum will be recorded.
    if checksum is not None and fileVersion.checksum is None:
        return False

    # Cannot decide definitively - assume they compare.
    return True

def checksum(path, client):
    """
    Calculate a file checksum.

    Returns the String checksum.

    path
      String pathname.

    client
      String client name. The command executed is '``client path``'. The client may be an absolute path ("/usr/bin/md5sum") or basename ("md5sum"). For a basename, the executable must be in the user's search path.
    """

    if not os.path.exists(path):
        raise ESGPublishError("No such file: %s"%path)

    command = "%s %s"%(client, path)
    info("Running: %s"%command)

    try:
        f = subprocess.Popen([client, path], stdout=subprocess.PIPE).stdout
    except:
        error("Error running command '%s %s', check configuration option 'checksum'."%command)
    lines = f.readlines()
    csum = lines[0].split()[0]

    return csum
