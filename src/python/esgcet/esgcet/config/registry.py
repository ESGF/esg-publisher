#!/usr/bin/env python

import sys
import logging

from esgcet.exceptions import *
from esgcet.messaging import debug, info, warning, error, critical, exception

class Registry(object):

    def __init__(self):
        self.registry = {}
        self.search_order = {}

    def register(self, projectName, moduleName, className, search_order):
        try:
            __import__(moduleName)
        except:
            warning('Cannot import handler %s:%s for project %s'%(moduleName, className, projectName))

        m = sys.modules[moduleName]
        cls = m.__dict__.get(className)
        if cls is None:
            warning('No such class in %s: %s'%(moduleName, className))

        self.registry[projectName] = cls
        self.search_order[projectName] = search_order

    def keys(self):
        return self.registry.keys()

    def items(self):
        return self.registry.items()

    def get(self, projectName, default=None):
        return self.registry.get(projectName, default)

    def order(self, projectName):
        return self.search_order[projectName]

registry = Registry()

def register(projectName, moduleName, className, search_order):
    registry.register(projectName, moduleName, className, search_order)

def getHandler(path, Session, validate=True):
    """
    Get a project handler from a file. The project is determined by trying to create each registered handler using the file.

    path
      String path of the file to read project info from.

    Session
      SQLAlchemy Session

    validate
      If True, create a validating handler which will raise an error if an invalid field value is read or input.
    """

    found = False
    items = registry.items()
    items.sort(lambda x, y: cmp(registry.order(x[0]), registry.order(y[0])))
    for name, cls in items:
        try:
            handler = cls(name, path, Session, validate)
        except ESGInvalidMetadataFormat:
            continue
        found = True
        break
    if not found:
        warning('No project found in file %s'%path)
        handler = None

    return handler

def getHandlerByName(projectName, path, Session, validate=True, offline=False):
    """
    Get a project handler by name.

    projectName
      String name of the project

    path
      String path of the file to read project info from. If not None, the file is validated
      to ensure that it has the correct project identifier.

    Session
      SQLAlchemy Session

    validate
      If True, create a validating handler which will raise an error if an invalid field value is read or input.

    offline
      If True, files are not scanned.
    """
    cls = registry.get(projectName, None)
    if cls is None:
        raise ESGPublishError("Invalid project name: %s, no handler found"%projectName)
    handler = cls(projectName, path, Session, validate, offline)
    return handler

def getHandlerFromDataset(dataset, Session, includeNullFields=True):
    """Create a handler from a dataset object.

    dataset
      Dataset object.

    Session
      SQLAlchemy Session

    includeNullFields=True
      If True, include all fieldnames as context keys, even if the value is None.
    """
    project = dataset.get_project(Session)
    handler = getHandlerByName(project, None, Session)
    handler.getContextFromDataset(dataset, Session, includeNullFields)

    return handler
