"""Wrappers for publication scripts, such as esgpublish, esgscan_directory, replication API, etc."""

import sys
import logging
import os
import string
import stat
import re

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from esgcet.publish import extractFromDataset, aggregateVariables, filelistIterator, fnmatchIterator, fnIterator, directoryIterator, multiDirectoryIterator, progressCallback, StopEvent, readDatasetMap, datasetMapIterator, iterateOverDatasets, publishDatasetList, processIterator, processNodeMatchIterator, CREATE_OP, DELETE_OP, RENAME_OP, UPDATE_OP, REPLACE_OP, checksum
from esgcet.config import loadConfig, getHandler, getHandlerByName, initLogging, registerHandlers, CFHandler, splitLine, getOfflineLister
from esgcet.exceptions import *
from esgcet.messaging import debug, info, warning, error, critical, exception
from esgcet.model import Dataset

dbengine = None
def initdb(init_file=None, echoSql=False, log_filename=None):
    global dbengine

    config = loadConfig(init_file)
    if dbengine is None:
        dbengine = create_engine(config.getdburl('extract'), echo=echoSql, pool_recycle=3600)
    initLogging('DEFAULT', override_sa=dbengine, log_filename=log_filename)
    Session = sessionmaker(bind=dbengine, autoflush=True, autocommit=False)
    return config, Session

def esgpublishWrapper(**kw):

    from esgcet.query import queryDatasetMap

    aggregateDimension = kw.get("aggregateDimension", "time")
    datasetMapfile = kw.get("datasetMapfile", None)
    datasetName = kw.get("datasetName", None)
    directoryList = kw.get("directoryList", None)
    echoSql = kw.get("echoSql", False)
    filefilt = kw.get("filefilt", '.*\.nc$')
    init_file = kw.get("init_file", None)
    initcontext = kw.get("initcontext", {})
    keepVersion = kw.get("keepVersion", False)
    las = kw.get("las", False)
    log_filename = kw.get("log_filename", None)
    masterGateway = kw.get("masterGateway", None)
    message = kw.get("message", None)
    offline = kw.get("offline", False)
    parent = kw.get("parent", None)
    perVariable = kw.get("perVariable", None)
    projectName = kw.get("projectName", None)
    properties = kw.get("properties", {})
    publish = kw.get("publish", False)
    publishOnly = kw.get("publishOnly", False)
    publishOp = kw.get("publishOp", CREATE_OP)
    readFiles = kw.get("readFiles", False)
    readFromCatalog = kw.get("readFromCatalog", False)
    reinitThredds=kw.get("reinitThredds", None)
    rescan = kw.get("rescan", False)
    rescanDatasetName = kw.get("rescanDatasetName", [])
    resultThreddsDictionary = None
    service = kw.get("service", None)
    summarizeErrors = kw.get("summarizeErrors", False)
    testProgress1 = kw.get("testProgress1", None)
    testProgress2 = kw.get("testProgress2", None)
    thredds = kw.get("thredds", False)
    threddsCatalogDictionary = kw.get("threddsCatalogDictionary", None)
    version = kw.get("version", None)

    # If offline, the project must be specified
    if offline and (projectName is None):
        raise ESGPublishError("Must specify project with --project for offline datasets")

    # Must specify version for replications
    if masterGateway is not None and version is None:
        raise ESGPublishError("Must specify version with --new-version for replicated datasets")

    # Load the configuration and set up a database connection
    config, Session = initdb(init_file=init_file, echoSql=echoSql, log_filename=log_filename)

    # Register project handlers
    registerHandlers()

    # If the dataset map is input, just read it ...
    dmap = None
    directoryMap = None
    extraFields = None
    if datasetMapfile is not None:
        dmap, extraFields = readDatasetMap(datasetMapfile, parse_extra_fields=True)
        datasetNames = dmap.keys()

    elif rescan:
        # Note: No need to get the extra fields, such as mod_time, since
        # they are already in the database, and will be used for file comparison if necessary.
        dmap, offline = queryDatasetMap(rescanDatasetName, Session)
        datasetNames = dmap.keys()

    # ... otherwise generate the directory map.
    else:
        # Online dataset(s)
        if not offline:

            if projectName is not None:
                handler = getHandlerByName(projectName, None, Session)
            else:
                multiIter = multiDirectoryIterator(directoryList, filefilt=filefilt)
                firstFile, size = multiIter.next()
                listIter = list(multiIter)
                handler = getHandler(firstFile, Session, validate=True)
                if handler is None:
                    raise ESGPublishError("No project found in file %s, specify with --project."%firstFile)
                projectName = handler.name

            props = properties.copy()
            props.update(initcontext)
            if not readFiles:
                directoryMap = handler.generateDirectoryMap(directoryList, filefilt, initContext=props, datasetName=datasetName)
            else:
                directoryMap = handler.generateDirectoryMapFromFiles(directoryList, filefilt, initContext=props, datasetName=datasetName)

            datasetNames = [(item,-1) for item in directoryMap.keys()]

        # Offline dataset. Format the spec as a dataset map : dataset_name => [(path, size), (path, size), ...]
        else:
            handler = getHandlerByName(projectName, None, Session, offline=True)
            dmap = {}
            listerSection = getOfflineLister(config, "project:%s"%projectName, service)
            offlineLister = config.get(listerSection, 'offline_lister_executable')
            commandArgs = "--config-section %s "%listerSection
            commandArgs += " ".join(directoryList)
            for dsetName, filepath, sizet in processNodeMatchIterator(offlineLister, commandArgs, handler, filefilt=filefilt, datasetName=datasetName, offline=True):
                size, mtime = sizet
                if dmap.has_key((dsetName,-1)):
                    dmap[(dsetName,-1)].append((filepath, str(size)))
                else:
                    dmap[(dsetName,-1)] = [(filepath, str(size))]

            datasetNames = dmap.keys()

    datasetNames.sort()
    if len(datasetNames)==0:
        warning("No datasets found.")

    # Iterate over datasets
    if not publishOnly:
        datasets = iterateOverDatasets(projectName, dmap, directoryMap, datasetNames, Session, aggregateDimension, publishOp, filefilt, initcontext, offline, properties, keepVersion=keepVersion, newVersion=version, extraFields=extraFields, masterGateway=masterGateway, comment=message, readFiles=readFiles)

    result = publishDatasetList(datasetNames, Session, publish=publish, thredds=thredds, las=las, parentId=parent, service=service, perVariable=perVariable, threddsCatalogDictionary=threddsCatalogDictionary, reinitThredds=reinitThredds, readFromCatalog=readFromCatalog)

    return result

def esgscanWrapper(directoryList, **kw):

    if len(directoryList)==0:
        raise ESGPublishError('No directory specified')

    output = sys.stdout
    appendMap = None
    appendPath = kw.get("appendPath", None)
    if appendPath is not None:
        if os.path.exists(appendPath):
            appendMap = readDatasetMap(appendPath)
        else:
            appendMap = {}
        output = open(appendPath, 'a')
    datasetName = kw.get("datasetName", None)
    filefilt = kw.get("fileFilt", '.*\.nc$')
    init_file = kw.get("initFile", None)
    offline = kw.get("offline", False)
    outputPath = kw.get("outputPath", None)
    if outputPath is not None:
        output = open(outputPath, 'w')
    else:
        output = sys.stdout
    projectName = kw.get("projectName", None)
    readFiles = kw.get("readFiles", False)
    service = kw.get("service", None)

    # Load the configuration and set up a database connection
    config, Session = initdb(init_file=init_file)

    # Register project handlers
    registerHandlers()

    if not offline:

        # Determine if checksumming is enabled
        line = config.get('DEFAULT', 'checksum', default=None)
        if line is not None:
            checksumClient, checksumType = splitLine(line)
        else:
            checksumClient = None

        if projectName is not None:
            handler = getHandlerByName(projectName, None, Session)
        else:
            multiIter = multiDirectoryIterator(directoryList, filefilt=filefilt)
            firstFile, size = multiIter.next()
            handler = getHandler(firstFile, Session, validate=True)
            if handler is None:
                raise ESGPublishError("No project found in file %s, specify with --project."%firstFile)
            projectName = handler.name

        if not readFiles:
            datasetMap = handler.generateDirectoryMap(directoryList, filefilt, datasetName=datasetName)
        else:
            datasetMap = handler.generateDirectoryMapFromFiles(directoryList, filefilt, datasetName=datasetName)

        # Output the map
        keys = datasetMap.keys()
        keys.sort()
        for datasetId in keys:
            direcTuple = datasetMap[datasetId]
            direcTuple.sort()
            for nodepath, filepath in direcTuple:

                # If readFiles is not set, generate a map entry for each file in the directory
                # that matches filefilt ...
                if not readFiles:
                    itr = directoryIterator(nodepath, filefilt=filefilt, followSubdirectories=False)
                # ... otherwise if readFiles is set, generate a map entry for each file
                else:
                    itr = fnIterator([filepath])

                for filepath, sizet in itr:
                    size, mtime = sizet
                    extraStuff = "mod_time=%f"%float(mtime)

                    if checksumClient is not None:
                        csum = checksum(filepath, checksumClient)
                        extraStuff += " | checksum=%s | checksum_type=%s"%(csum, checksumType)

                    # Print the map entry if:
                    # - The map is being created, not appended, or
                    # - The existing map does not have the dataset, or
                    # - The existing map has the dataset, but not the file.
                    if (appendMap is None) or (not appendMap.has_key(datasetId)) or ((filepath, "%d"%size) not in appendMap[datasetId]):
                        print >>output, "%s | %s | %d | %s"%(datasetId, filepath, size, extraStuff)
    else:                               # offline
        if projectName is not None:
            handler = getHandlerByName(projectName, None, Session, offline=True)
        else:
            raise ESGPublishError("Must specify --project for offline datasets.")
        listerSection = getOfflineLister(config, "project:%s"%projectName, service)
        offlineLister = config.get(listerSection, 'offline_lister_executable')
        commandArgs = "--config-section %s "%listerSection
        commandArgs += " ".join(directoryList)
        for dsetName, filepath, sizet in processNodeMatchIterator(offlineLister, commandArgs, handler, filefilt=filefilt, datasetName=datasetName, offline=True):
            size, mtime = sizet
            extrastuff = ""
            if mtime is not None:
                extrastuff = "| mod_time=%f"%float(mtime)
            if (appendMap is None) or (not appendMap.has_key(dsetName)) or ((filepath, "%d"%size) not in appendMap[dsetName]):
                print >>output, "%s | %s | %d %s"%(dsetName, filepath, size, extrastuff)

    if output is not sys.stdout:
        output.close()

    
