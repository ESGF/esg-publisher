"""Utility routines for publishing."""

import os
import stat
import numpy
import types
import string
import glob
import re
import sys
import traceback
import logging
import subprocess
import filecmp
import urlparse
import OpenSSL
import getpass
from esgcet.config import getHandler, getHandlerByName, splitLine, getConfig, getThreddsServiceSpecs
from esgcet.exceptions import *
from esgcet.messaging import debug, info, warning, error, critical, exception
from time import time

# Force stat modification times to be returned as integers for consistency.
# By default, os.stat(path).st_mtime returns a float.
os.stat_float_times(False)

UPDATE_TIMESTAMP = "/tmp/publisher-last-check"
DEFAULT_CERTS_LOCATION_SUFFIX = "/.globus/certificates"


class Bcolors:

    @property
    def HEADER(self):
        return self._get_escape('95')

    @property
    def OKBLUE(self):
        return self._get_escape('94')

    @property
    def OKGREEN(self):
        return self._get_escape('92')

    @property
    def WARNING(self):
        return self._get_escape('93')

    @property
    def FAIL(self):
        return self._get_escape('91')

    @property
    def ENDC(self):
        return self._get_escape('0')

    @property
    def BOLD(self):
        return self._get_escape('1')

    @property
    def UNDERLINE(self):
        return self._get_escape('4')

    def _get_escape(self, val):
        if self._colors_are_disabled():
            return ''
        else:
            return('\033[{}m'.format(val))

    def _colors_are_disabled(self):
        if self._disable_colors == None:
            config = getConfig()
            if config:
                self._disable_colors = \
                    config.getboolean('DEFAULT', 'disable_colors',
                                      default=False)
            else:
                return False  # allow colors until config is loaded
        return self._disable_colors                

    def __init__(self):
        self._disable_colors = None

bcolors = Bcolors()

def getTypeAndLen(att):
    """Get the type descriptor of an attribute.
    """
    if isinstance(att, numpy.ndarray):
        result = (att.dtype.char, len(att))
    elif isinstance(att, types.StringType) or isinstance(att, types.UnicodeType):
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

    nodefilts = handler.getFilters()
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

def nodeIterator(top, nodefilt, filefilt, followSymLinks=True, allFiles=False):
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

    allFiles = False
      Boolean flag. If True, iterate over all files that match the filter. Otherwise just return
      the first file that matches.

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
            if not foundOne or allFiles:

                # Find the first node filter that matches
                for filt in nodefilt:
                    result = re.match(filt, top)
                    debug("Comparing %s with filter %s ..."%(top, filt))
                    if result is not None:
                        debug("... match")
                        break
                    debug("... no match")
                    
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
    
def parseDatasetVersionId(datasetVersionId):
    """Parse a dataset ID into master_id and version.

    datasetVersionId has the form master_id#version or just master_id. If no version is found,
    version=-1 is returned.

    Returns (master_id, version).
    """
    fields = datasetVersionId.split('#')
    if len(fields)==1:
        result = (datasetVersionId, -1)
    elif len(fields)==2:
        result = (fields[0], string.atoi(fields[1]))
    else:
        raise ESGPublishError("Invalid dataset ID:%s"%datasetVersionId)
    return result

def parseSolrDatasetId(datasetId):
    """Parse a SOLR dataset ID into master_id and version.

    datasetId has the form 'master_id.version|data_node'

    Returns (master_id, version, data_node)

    """
    fields = datasetId.split('|')
    if len(fields)==1:
        datasetVersionId = datasetId
        dataNode = None
    else:
        datasetVersionId, dataNode = fields[:2]
    dfields = datasetVersionId.split('.')
    masterId = '.'.join(dfields[:-1])
    sversion = dfields[-1]
    if sversion[0] in ('v', 'V'):
        sversion = sversion[1:]
    try:
        version = string.atoi(sversion)
    except:
        version = -1
        masterId = datasetVersionId
    return (masterId, version, dataNode)

def generateDatasetVersionId(versionTuple):
    result = "%s#%d"%versionTuple
    return result

def extraFieldsGet(extraDict, gettuple, versionobj):
    dsetname, path, attname = gettuple
    if versionobj.isLatest():
        tup1 = (dsetname, -1, path, attname)
        attval = extraDict.get(tup1, None)
        if attval is None:
            tup2 = (dsetname, versionobj.version, path, attname)
            attval = extraDict.get(tup2, None)
    else:
        attval = extraDict.get(gettuple, None)
    return attval

def readDatasetMap(mappath, parse_extra_fields=False):
    """Read a dataset map.

    A dataset map is a text file, each line having the form:

    dataset_id | absolute_file_path | size [ | ``from_file`` =<path> [ | extra_field=extra_value ...]]

    where dataset_id has the form dataset_name[#version]

    Returns (if parse_extra_fields=False) a dataset map - a dictionary: dataset_id => [(path, size), (path, size), ...]
    If parse_extra_fields=True, returns a tuple (dataset_map, extra_dictionary). See parse_extra_fields.
      

    mappath
      Name of the dataset map.

    parse_extra_fields
      Boolean; if True then parse any extra fields of the form *extra_field=extra_value*, and return
      a dictionary with items of the form:

      extrafields[(dataset_name, version_number, absolute_file_path, *field_name*)] => field_value

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
            versionName, path, size = fields[0:3]
            datasetName,versionno = parseDatasetVersionId(versionName)
            if len(fields)>3:
                for field in fields[3:]:
                    efield, evalue = field.split('=')
                    extraFieldMap[(datasetName, versionno, path, efield.strip())] = evalue.strip()
            if datasetMap.has_key((datasetName, versionno)):
                datasetMap[(datasetName, versionno)].append((path, size))
            else:
                datasetMap[(datasetName, versionno)] = [(path, size)]
        else:
            datasetId, path, size = splitLine(line)[0:3]
            versionId = parseDatasetVersionId(datasetId)
            if datasetMap.has_key(versionId):
                datasetMap[versionId].append((path, size))
            else:
                datasetMap[versionId] = [(path, size)]

    mapfile.close()

    for value in datasetMap.values():
        value.sort()
        
    if parse_extra_fields:
        return (datasetMap, extraFieldMap)
    else:
        return datasetMap

def datasetMapIterator(datasetMap, datasetId, versionNumber, extraFields=None, offline=False):
    """Create an iterator from a dataset map entry.

    Returns an iterator that returns (path, size) at each iteration. If sizes are omitted from the file, the sizes are inserted, provided the files are online.
    
    datasetMap
      Dictionary dataset map as returned by **readDatasetMap**.

    datasetId
      Dataset string identifier.
      
    versionNumber
      String version number.

    extraFields
      Extra dataset map fields, as from **readDatasetMap**.

    offline
      Boolean, if true don't try to stat the file.

    """

    for path, csize in datasetMap[(datasetId, versionNumber)]:
        csize = csize.strip()
        if csize=="":
            size = os.stat(path)[stat.ST_SIZE]
        else:
            size = string.atol(csize)
        mtime = None
        if extraFields is not None:
            mtime = extraFields.get((datasetId, versionNumber, path, 'mod_time'))
        if mtime is None:
            if not offline:
                mtime = os.stat(path)[stat.ST_MTIME]
            else:
                mtime = None
        else:
            mtime = float(mtime)
        yield (path, (size, mtime))

def iterateOverDatasets(projectName, dmap, directoryMap, datasetNames, Session, aggregateDimension, operation, filefilt, initcontext, offlineArg,
                        properties, testProgress1=None, testProgress2=None, handlerDictionary=None, perVariable=None, keepVersion=False, newVersion=None,
                        extraFields=None, masterGateway=None, comment=None, forceAggregate=False, readFiles=False, nodbwrite=False,
                        pid_connector=None, test_publication=False, handlerExtraArgs={}, commitEvery=None, validate_standard_name=True):
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

    handlerExtraArgs={}
      A dictionary of extra keyword arguments to pass when instantiating the handler.

    perVariable=None
      Boolean, overrides ``variable_per_file`` config option.

    keepVersion
      Boolean, True if the dataset version should not be incremented.

    newVersion
      Integer or dictionary. Set the new version number
      explicitly. If a dictionary, maps dataset_id => version. By
      default the version number is incremented by 1. See keepVersion.

    extraFields
      Extra dataset map fields, as from **readDatasetMap**.

    masterGateway
      The gateway that owns the master copy of the datasets. If None, the dataset is not replicated.
      Otherwise the TDS catalog is written with a 'master_gateway' property, flagging the dataset(s)
      as replicated.

    comment=None
      String comment to associate with new datasets created.

    forceAggregate=False
      If True, run the aggregation step regardless.

    readFiles=False
      If True, interpret directoryMap as having one entry per file, instead of one per directory.

    pid_connector
        esgfpid.Connector object to register PIDs

    commitEvery
        Integer specifying how frequently to commit file info to database when scanning files

    """
    from esgcet.publish import extractFromDataset, aggregateVariables

    versionIsMap = (type(newVersion) is types.DictType)
    if versionIsMap:
        saveVersionMap = newVersion

    prevProject = None
    datasets = []
    ct = len(datasetNames)
    for iloop in range(ct): 
        datasetName,versionno = datasetNames[iloop]

        # Must specify version for replications
        if masterGateway:
            if not newVersion and versionno < 0:
                raise ESGPublishError("Must specify a version for replicated datasets, e.g. in the mapfile or with --new-version/--version-list.")

        # If using a version map, lookup the version for this dataset
        if versionIsMap:
            try:
                newVersion = saveVersionMap[datasetName]
            except KeyError:
                raise ESGPublishError("Dataset not found in version map: %s"%datasetName)
            
        context = initcontext.copy()

        # Get offline flag
        if type(offlineArg) is dict:
            offline = offlineArg[datasetName]
        else:
            offline = offlineArg

        # Don't try to aggregate offline datasets
        if offline:
            forceAggregate=False

        # Get a file iterator and sample file
        if dmap is not None:
            if len(dmap[(datasetName,versionno)])==0:
                warning("No files specified for dataset %s, version %d."%(datasetName,versionno))
                continue
            firstFile = dmap[(datasetName,versionno)][0][0]
            fileiter = datasetMapIterator(dmap, datasetName, versionno, extraFields=extraFields, offline=offlineArg)
        else:
            direcTuples = directoryMap[datasetName]
            firstDirec, sampleFile = direcTuples[0]
            firstFile = os.path.join(firstDirec, sampleFile)
            if not readFiles:
                fileiter  = multiDirectoryIterator([direc for direc, sampfile in direcTuples], filefilt)
            else:
                fileiter = fnIterator([sampfile for direc, sampfile in direcTuples])

        # If the project is not specified, try to read it from the first file
        if handlerDictionary is not None and handlerDictionary.has_key(datasetName):
            handler = handlerDictionary[datasetName]
        elif projectName is not None:
            handler = getHandlerByName(projectName, firstFile, Session, validate=True, offline=offline, **handlerExtraArgs)
        else:
            handler = getHandler(firstFile, Session, validate=True, **handlerExtraArgs)
            if handler is None:
                raise ESGPublishError("No project found in file %s, specify with --project."%firstFile)
            projectName = handler.name
            info("Using project name = %s"%projectName)
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

        # add dataset_version to context to allow version to be a mandatory field
        if versionno > -1:
            context['dataset_version'] = versionno
        elif newVersion is not None:
            context['dataset_version'] = newVersion

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
        cfHandler = handler.getMetadataHandler(sessionMaker=Session)

        dataset=None
        if testProgress1 is not None:
           testProgress1[1] = (100./ct)*iloop
           if not offline:
              testProgress1[2] = (100./ct)*iloop + (50./ct)
           else:
              testProgress1[2] = (100./ct)*iloop + (100./ct)

        dataset = extractFromDataset(datasetName, fileiter, Session, handler, cfHandler, aggregateDimensionName=aggregateDimension,
                                     offline=offline, operation=operation, progressCallback=testProgress1, perVariable=perVariable,
                                     keepVersion=keepVersion, newVersion=newVersion, extraFields=extraFields, masterGateway=masterGateway,
                                     comment=comment, useVersion=versionno, forceRescan=forceAggregate, nodbwrite=nodbwrite,
                                     pid_connector=pid_connector, test_publication=test_publication, commitEvery=commitEvery, **context)

        # If republishing an existing version, only aggregate if online and no variables exist (yet) for the dataset.

        runAggregate = (not offline)
        if hasattr(dataset, 'reaggregate'):
            runAggregate = (runAggregate and dataset.reaggregate)
        runAggregate = runAggregate or forceAggregate

        # Turn off aggregations if skip_aggregations is set
        # This applies even if forceAggregate is set to True elsewhere in the
        # code when republishing an earlier version of the dataset
        section = 'project:%s' % context.get('project')
        config = getConfig()
        skipAggregate = config.getboolean(section, 'skip_aggregations', False)

        if runAggregate and skipAggregate:
            runAggregate = False
            info("Skipping aggregations due to skip_aggregations config option")

        if testProgress2 is not None:
           testProgress2[1] = (100./ct)*iloop + 50./ct
           testProgress2[2] = (100./ct)*(iloop + 1)
        if runAggregate and (not nodbwrite):
            aggregateVariables(datasetName, Session, aggregateDimensionName=aggregateDimension, cfHandler=cfHandler,
                               progressCallback=testProgress2, datasetInstance=dataset, validate_standard_name=validate_standard_name)
        elif testProgress2 is not None:
            # Just finish the progress GUI
            issueCallback(testProgress2, 1, 1, 0.0, 1.0)
            
        # Save the context with the dataset, so that it can be searched later
        if (not nodbwrite):
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

def compareFiles(fileVersion, handler, path, size, offline, checksum=None):
    """Compare a database file object and physical file.

    Returns True iff the files are the same.
    
    fileVersion
      File version object

    handler
      Project handler.

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
    if checksum is not None and fileVersion.checksum is not None:
        return fileVersion.checksum==checksum

    # If file sizes differ, files are different.
    if fileVersion.size!=size:
        return False

    # For offline datasets, only compare sizes
    if offline:
        return True

    f = handler.openPath(path)
    trackingId = f.getAttribute('tracking_id', None, None)
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

def compareFilesByPath(path1, path2, handler, size1=None, compare=False):
    """Compare two files.

    Returns True iff the files are the same.
    
    path1
      String path of first file to compare.
    
    path2
      String path of second file to compare.
    
    handler
      Project handler.

    size1
      Size of first file, as returned by the stat module.

    compare
      Boolean, if True compare the contents.
    """

    # If file sizes differ, files are not equal
    if size1 is None:
        stats = os.stat(path1)
        size1 = stats[stat.ST_SIZE]
        
    stats = os.stat(path2)
    if size1 != stats[stat.ST_SIZE]:
        return False

    # If at least one file has a tracking ID, and they differ, the files are not equal
    f = handler.openPath(path1)
    trackingId1 = f.getAttribute('tracking_id', None, None)
    f.close()
    f = handler.openPath(path2)
    trackingId2 = f.getAttribute('tracking_id', None, None)
    f.close()
    if ((trackingId1 is not None) or (trackingId2 is not None)) and trackingId1!=trackingId2:
        return False

    # Optionally, just compare the files
    if compare:
        return filecmp.cmp(path1, path2, shallow=False)

    # If both files have tracking ID and they agree, the files are equal
    if (trackingId1 is not None) and (trackingId2 is not None) and trackingId1==trackingId2:
        return True

    # Cannot decide definitively - assume they don't compare.
    return False

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


def getHessianServiceURL(project_config_section=None):
    """Get the configured value of hessian_service_url"""

    config = getConfig()
    serviceURL = None
    if project_config_section and config.has_section(project_config_section):
        serviceURL = config.get(project_config_section, 'hessian_service_url', default=None)
    if not serviceURL:
        serviceURL = config.get('DEFAULT', 'hessian_service_url')

    return serviceURL


def getRestServiceURL(project_config_section=None):
    """Get the configured value of rest_service_url. If not set,
    derive host from hessian_service_url and use '/esg-search/ws' as the path.
    """

    config = getConfig()
    hessianServiceURL = None
    serviceURL = None
    # get project specific hessian service url
    if serviceURL is None:
        if project_config_section and config.has_section(project_config_section):
            hessianServiceURL = config.get(project_config_section, 'hessian_service_url', default=None)
        if not hessianServiceURL:
            hessianServiceURL = config.get('DEFAULT', 'hessian_service_url')
        host = urlparse.urlparse(hessianServiceURL).netloc
        serviceURL = urlparse.urlunparse(('https', host, '/esg-search/ws', '', '', ''))
    return serviceURL


def tracebackString(indent=0):
    """
    Returns the traceback of the current exception as an indented string.
    """
    lines = traceback.format_exc(sys.exc_info()[2]).split("\n")
    prefix = " " * indent
    return string.join([prefix + line + "\n" for line in lines])


def establish_pid_connection(pid_prefix, test_publication, project_config_section, config, handler, publish=True):
    """Establish a connection to the PID service

    pid_prefix
        PID prefix to be used for given project

    test_publication
        Boolean to flag PIDs as test

     project_config_section
        The name of the project config section in esg.ini

    config
        Loaded config file(s)

    handler
        Project handler to be used for given project

    publish
        Flag to trigger publication and unpublication
    """

    try:
        import esgfpid
    except ImportError:
        raise "PID module not found. Please install the package 'esgfpid' (e.g. with 'pip install')."

    pid_messaging_service_exchange_name, pid_messaging_service_credentials = handler.get_pid_config(project_config_section, config)
    pid_data_node = urlparse.urlparse(config.get('DEFAULT', 'thredds_url')).netloc
    thredds_service_path = None
    if publish:
        thredds_file_specs = getThreddsServiceSpecs(config, 'DEFAULT', 'thredds_file_services')
        for serviceType, base, name, compoundName in thredds_file_specs:
            if serviceType == 'HTTPServer':
                thredds_service_path = base
                break

    pid_connector = esgfpid.Connector(handle_prefix=pid_prefix,
                                      messaging_service_exchange_name=pid_messaging_service_exchange_name,
                                      messaging_service_credentials=pid_messaging_service_credentials,
                                      data_node=pid_data_node,
                                      thredds_service_path=thredds_service_path,
                                      test_publication=test_publication)
    return pid_connector


def getTableDir(cmor_table_path, ds_version, use_subdirs):
    """
    Get the directory of CMOR tables appropriate for use by PrePARE for checking 
    against version ds_version, using one of two strategies.

    If use_subdirs=False, assume that the cmor_table_path is a git clone.
    Call checkAndUpdateRepo, and then return the supplied table path itself.

    If use_subdirs=True, assume that the cmor_table_path is a directory containing 
    read-only subidrectories for the different versions of the tables (as fetched 
    using esgfetchtables).  Returns the relevant subdirectory after checking that 
    it exists.
    """

    if use_subdirs:
        path = os.path.join(cmor_table_path, ds_version)
        if not os.path.isdir(path):
            raise ESGPublishError('tables directory {} does not exist'.format(path))
        return path
    else:
        checkAndUpdateRepo(cmor_table_path, ds_version)
        return cmor_table_path


def checkedRun(command):
    """
    Run a command and check that it returns 0 status.
    """
    status = os.system(command)
    if status != 0:
        raise ESGPublishError(('command {} failed with status {}'
                               ).format(command, status))


def checkAndUpdateRepo(cmor_table_path, ds_version):
    """
        Checks for a file written to a predefined location.  if not present or too old, will pull the repo based on the input path argument and update the timestamp.
    """
    # This is run during handler initialization and not for each file validation

    # Pull repo if fetched more than one day ago
    # or if never fetched before
    if os.path.exists(UPDATE_TIMESTAMP):
        mtime = os.path.getmtime(UPDATE_TIMESTAMP)
        now = time()
        if now - mtime > (86400.0):
            pull_cmor_repo = True
        else:
            pull_cmor_repo = False
    else:
        pull_cmor_repo = True

    if pull_cmor_repo:
        try:
            # Go into CMOR table path
            # Git fetch CMOR table repo
            # Go back to previous working directory
            checkedRun(('cd {} && git fetch --quiet'
                        ).format(cmor_table_path))
            # Update local timestamp
            f = open(UPDATE_TIMESTAMP, "w")
            f.write("CMOR table updated at {}".format(time()))
            f.close()
            debug("Local CMOR table repository fetched or updated")
        except Exception as e :
            warning("Attempt to update the cmor table repo and encountered an error: " + str(e))

    # Change repo branch in any case
    try:
        # Go into CMOR table path
        # Stash any changes from previous checkout 
        # Checkout to the appropriate CMOR table tag
        # Go back to previous working directory
        checkedRun(('cd {} && git stash --quiet && git checkout {} --quiet'
                    ).format(cmor_table_path, ds_version))
        # Update local timestamp
        f = open(UPDATE_TIMESTAMP, "w")
        f.write("CMOR table updated at {}".format(time()))
        f.close()
        debug("Consider CMOR table tag: {}".format(ds_version))
    except Exception as e:
        raise ESGPublishError("Error data_specs_version tag %s not found in the CMOR tables or other error.  Please contact support"%ds_version)

    # Get most up to date CMIP6_CV in any case
    if ds_version != "master":
        try:
            # Go into CMOR table path
            # PrePARE requires to have the most up to date CMIP6 CV.
            # Update CMIP6_CV.json from master branch.
            # Go back to previous working directory
            checkedRun(('cd {} && git checkout master CMIP6_CV.json --quiet'
                        ).format(cmor_table_path))
            debug("CMIP6 CV updated from master")
        except Exception as e:
            raise ESGPublishError("Master branch does not exists or CMIP6_CV.json not found or other error.  Please contact support" % ds_version)


def getServiceCertsLoc():            
    try:
        service_certs_location = getConfig().get('DEFAULT', 'hessian_service_certs_location')

    except:
        home = os.environ.get("HOME")
        if home is not None:
            service_certs_location = home + DEFAULT_CERTS_LOCATION_SUFFIX        
            
    if service_certs_location is None:
        raise ESGPublishError("hessian_service_certs_location needs to be set in esg.ini")


    if not os.path.exists(service_certs_location):
        raise ESGPublishError("Error: " + service_certs_location + " does not exist.  Please run myproxy-logon with -b to bootstrap the certificates, or set an alternate location using the hessian_service_certs_location setting in esg.ini")
    return service_certs_location

