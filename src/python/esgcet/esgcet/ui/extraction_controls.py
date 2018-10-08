#!/usr/bin/env python
#
###############################################################################
#                                                                             #
# Module:       extraction_controls fuctions                                  #
#                                                                             #
# Copyright:    "See file Legal.htm for copyright information."               #
#                                                                             #
# Authors:      PCMDI Software Team                                           #
#               Lawrence Livermore National Laboratory:                       #
#                                                                             #
# Description:  Call this routine to start the database session.              #
#                                                                             #
###############################################################################

#-------------------------------------------------------------------------------------
# Make a connect to the database -- called from the esgpublish_gui -- one time call
#-------------------------------------------------------------------------------------
def call_sessionmaker( root ):
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from esgcet.config import loadConfig, initLogging, registerHandlers

    # init_file = "../scripts/esg.ini"
    init_file = None                    # Load installed init file
    echoSql = True

    # Load the configuration and set up a database connection
    config = loadConfig(init_file)
    root.engine = create_engine(config.getdburl('extract'), echo=root.echoSql, pool_recycle=3600)
    initLogging('DEFAULT', override_sa=root.engine)
    Session = sessionmaker(bind=root.engine, autoflush=True, autocommit=False)

    # Register project handlers
    registerHandlers()

    root.config = config
    root.Session = Session
    root.projectName = None
    root.firstFile = None
    root.dmap = None
    root.extraFields = None
    root.directoryMap = None
    root.datasetMapfile = None
    root.filefilt = None

#-------------------------------------------------------------------------------------
# Load the configuration and set up a database connection
#-------------------------------------------------------------------------------------
def load_configuration( parent ):
    import os
    import pub_controls
    from esgcet.config import getHandler, getHandlerByName, registerHandlers, CFHandler
    from sqlalchemy.orm import sessionmaker
    from esgcet.publish import multiDirectoryIterator, datasetMapIterator

    offline = parent.offline
    firstFile = parent.firstFile
    projectName = parent.projectName
    config = parent.config
    Session = parent.Session

    dmap = parent.dmap
    datasetNames = parent.datasetNames
    datasetMapfile = parent.datasetMapfile

    for datasetName in datasetNames:

        # Get a file iterator and sample file
        if datasetMapfile is not None:
            firstFile = dmap[datasetName][0][0]
            fileiter = datasetMapIterator(dmap, datasetName)
        else:
            direcTuples = parent.directoryMap[datasetName]
            firstDirec, sampleFile = direcTuples[0]
            firstFile = os.path.join(firstDirec, sampleFile)
            fileiter  = multiDirectoryIterator([direc for direc, sampfile in direcTuples],parent.filefilt)

        # Register project handlers
        registerHandlers()

        # If the project is not specified, try to read it from the first file
        validate = True
        if projectName is not None:
            handler = getHandlerByName(projectName,firstFile,Session,validate=validate,offline=offline)
        else:
            handler = getHandler(firstFile, Session, validate=validate)

        parent.handler = handler

    # View the collection of datasets
    tab_name= "Collection %i" % parent.top_ct
    parent.ntk.new_page( parent, tab_name )

#---------------------------------------------------------------------
# End of File
#---------------------------------------------------------------------
