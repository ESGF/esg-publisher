#!/usr/bin/env python

import sys
import logging
import inspect

from pkg_resources import iter_entry_points
from esgcet.exceptions import *
from esgcet.messaging import debug, info, warning, error, critical, exception

# Entry points. For a given entry point group, the entry points are either:
#   - HANDLER_NAME_ENTRY_POINT and HANDLER_ENTRY_POINT, or
#   - HANDLER_DICT_ENTRY_POINT
HANDLER_NAME_ENTRY_POINT = "handler_name"
HANDLER_ENTRY_POINT = "handler"
HANDLER_DICT_ENTRY_POINT = "handler_dictionary"

# Entry point groups, one for each handler type
ESGCET_PROJECT_HANDLER_GROUP = "esgcet.project_handlers"
ESGCET_FORMAT_HANDLER_GROUP = "esgcet.format_handlers"
ESGCET_METADATA_HANDLER_GROUP = "esgcet.metadata_handlers"
ESGCET_THREDDS_CATALOG_HOOK_GROUP = "esgcet.thredds_catalog_hooks"

# Note: To add an entry point group associated with each project:
#
# In registry.py (this file):
# - Add an entry point group name
# - Create the registry associated with the entry point group
# - modify getHandlerByEntryPointGroup and getRegistry for the entry point group
#
# In config.py:
# - Add a configuration option, and set it for each project in esg.ini
# - modify config:registerHandlers to register handlers in this entry point group,
#   and set default handlers if appropriate
#
# (optional) In project.ProjectHandler:__init__, associate the handler type with
# each instance of a project handler.

class Registry(object):

    """
    A registry associates projects to a particular type of handler.
    """

    def __init__(self, entryPointGroup):
        self.entryPointGroup = entryPointGroup
        self.registry = {}              # project_name => handler
        self.search_order = {}
        # self.entry_points: handler_name => (handler, distribution, mustload), for all available distributions
        # self.entry_points is 'lazy loaded' by loadEntryPoints
        #   If mustload is True, handler is an entry point that must be loaded to get the class
        #   else if mustload is False, the handler is already a class (e.g. a builtin handler)
        self.entry_points = None

    def loadEntryPoints(self):
        """
        Get the entry points for the entry point group associated with this registry,
        and build an entry point dictionary.
        """
        optionDict = {}
        distPlugins = {}                # distPlugins: entry_point_distribution => distribution_dict
                                        #   where distribution_dict: entry_point_name => handler_class
        
        for ep in iter_entry_points(self.entryPointGroup):
            if distPlugins.has_key(ep.dist):
                distPlugins[ep.dist][ep.name] = ep
            else:
                distPlugins[ep.dist] = {ep.name : ep}

        for dist, v in distPlugins.items():
            if v.has_key(HANDLER_NAME_ENTRY_POINT):
                if v.has_key(HANDLER_ENTRY_POINT):
                    handlerName = v[HANDLER_NAME_ENTRY_POINT].module_name
                    if optionDict.has_key(handlerName):
                        handlerValue = v[HANDLER_ENTRY_POINT]
                        handlerClassName, prevDist, mustload = optionDict[handlerName]
                        if handlerValue != handlerClassName:
                            error("Conflicting handler names found:\n  In distribution %s, %s => (%s);\n  In distribution %s, %s => (%s)\n  To remove the error uninstall one of the packages with 'easy_install -mxN package_name'."%(dist,handlerName,handlerValue,prevDist,handlerName,handlerClassName))
                    else:
                        optionDict[handlerName] = (v[HANDLER_ENTRY_POINT], dist, True)
                else:
                    warning("Distribution %s does not define a %s option."%(k, HANDLER_ENTRY_POINT))
            elif v.has_key(HANDLER_DICT_ENTRY_POINT):
                handlerDict = v[HANDLER_DICT_ENTRY_POINT].load()
                for handlerName, handlerClassName in handlerDict.items():
                    if optionDict.has_key(handlerName):
                        handlerValue = v[HANDLER_ENTRY_POINT]
                        handlerClassName, prevDist, mustload = optionDict[handlerName]
                        if handlerValue != handlerClassName:
                            error("Conflicting handler names found:\n  In distribution %s, %s => (%s);\n  In distribution %s, %s => (%s)\n  To remove the error uninstall one of the packages with 'easy_install -mxN package_name'."%(dist,handlerName,handlerValue,prevDist,handlerName,handlerClassName))
                    else:
                        optionDict[handlerName] = (handlerClassName, dist, False)
        return optionDict

    def register(self, projectName, moduleName, className):
        try:
            __import__(moduleName)
        except:
            warning('Cannot import handler %s:%s for project %s'%(moduleName, className, projectName))

        m = sys.modules[moduleName]
        cls = m.__dict__.get(className)
        if cls is None:
            warning('No such class in %s: %s'%(moduleName, className))

        self.registry[projectName] = cls

    def registerHandlerName_1(self, projectName, handlerName):
        try:
            cls, dist, mustload = self.entry_points[handlerName]
        except KeyError:
            raise ESGPublishError("Cannot find a handler with name=%s (in group %s), for project %s"%(handlerName, self.entryPointGroup, projectName))
        if mustload:
            try:
                cls = cls.load()
            except ImportError:
                raise ESGPublishError("Handler class not found: %s"%str(cls))
        return cls

    def registerHandlerName(self, projectName, handlerName):
        if self.entry_points is None:
            self.entry_points = self.loadEntryPoints()
        projectHandler = self.registerHandlerName_1(projectName, handlerName)
        self.registry[projectName] = projectHandler

    def setSearchOrder(self, projectName, search_order):
        self.search_order[projectName] = search_order

    def keys(self):
        return self.registry.keys()

    def items(self):
        return self.registry.items()

    def get(self, projectName, default=None):
        return self.registry.get(projectName, default)

    def order(self, projectName):
        return self.search_order[projectName]

# Initialize a registry for each project-related handler
projectRegistry = Registry(ESGCET_PROJECT_HANDLER_GROUP)
formatRegistry = Registry(ESGCET_FORMAT_HANDLER_GROUP)
metadataRegistry = Registry(ESGCET_METADATA_HANDLER_GROUP)
threddsRegistry = Registry(ESGCET_THREDDS_CATALOG_HOOK_GROUP)

def register(registry, projectName, moduleName, className):
    registry.register(projectName, moduleName, className)

def registerHandlerName(registry, projectName, handlerName):
    registry.registerHandlerName(projectName, handlerName)

def setRegisterSearchOrder(projectName, search_order):
    projectRegistry.setSearchOrder(projectName, search_order)

def instantiateHandler(cls, *args, **extra_args):
    """
    Instantiate the handler class with the specified arguments and extra arguments,
    but filtering out anything that it doesn't support.
    """
    passed_args = {}
    supported_args = inspect.getargspec(cls.__init__).args
    for k, v in extra_args.iteritems():
        if k in supported_args:
            passed_args[k] = v
        else:
            debug("Discarding arg '%s' not supported by handler" % k)
    return cls(*args, **passed_args)

def getHandler(path, Session, validate=True, **extra_args):
    """
    Get a project handler from a file. The project is determined by trying to create each registered handler using the file.

    path
      String path of the file to read project info from.

    Session
      SQLAlchemy Session

    validate
      If True, create a validating handler which will raise an error if an invalid field value is read or input.

    any other keyword args are passed to the handler
    """

    found = False
    items = projectRegistry.items()
    items.sort(lambda x, y: cmp(projectRegistry.order(x[0]), projectRegistry.order(y[0])))
    for name, cls in items:
        try:
            handler = instantiateHandler(cls, name, path, Session, validate, **extra_args)
        except ESGInvalidMetadataFormat:
            continue
        found = True
        break
    if not found:
        warning('No project handler found for file %s'%path)
        handler = None

    return handler

def getHandlerByName(projectName, path, Session, validate=True, offline=False, **extra_args):
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

    any other keyword args are passed to the handler
    """
    projectHandlerClass = projectRegistry.get(projectName, None)
    if projectHandlerClass is None:
        raise ESGPublishError("Invalid project name: %s, no handler found"%projectName)
    handler = instantiateHandler(projectHandlerClass, projectName, path, Session, validate, offline, **extra_args)
    return handler

def getHandlerFromDataset(dataset, Session, includeNullFields=True, **extra_args):
    """Create a handler from a dataset object.

    dataset
      Dataset object.

    Session
      SQLAlchemy Session

    includeNullFields=True
      If True, include all fieldnames as context keys, even if the value is None.

    any other keyword args are passed to the handler
    """
    project = dataset.get_project(Session)
    handler = getHandlerByName(project, None, Session, **extra_args)
    handler.getContextFromDataset(dataset, Session, includeNullFields)

    return handler

def getHandlerByEntryPointGroup(entryPointGroup, projectName, errorIfMissing=True):
    """
    Get a handler other than a project handler.

    Returns a handler associated with the entry point group.

    entryPointGroup
      String entry point group name.

    projectName
      String name of the project
    """
    handler = None
    if entryPointGroup==ESGCET_FORMAT_HANDLER_GROUP:
        handler = formatRegistry.get(projectName)
    elif entryPointGroup==ESGCET_METADATA_HANDLER_GROUP:
        handler = metadataRegistry.get(projectName)
    elif entryPointGroup==ESGCET_THREDDS_CATALOG_HOOK_GROUP:
        handler = threddsRegistry.get(projectName)

    if errorIfMissing and (handler is None):
        raise ESGPublishError("Cannot get handler for project=%s, entry point group=%s"%(projectName, entryPointGroup))

    return handler

def getRegistry(entryPointGroup):
    """
    Get the registry associated with an entry point group

    Returns a registry object.

    entryPointGroup
      String entry point group name.

    """
    if entryPointGroup == ESGCET_PROJECT_HANDLER_GROUP:
        registry = projectRegistry
    elif entryPointGroup == ESGCET_FORMAT_HANDLER_GROUP:
        registry = formatRegistry
    elif entryPointGroup == ESGCET_METADATA_HANDLER_GROUP:
        registry = metadataRegistry
    elif entryPointGroup == ESGCET_THREDDS_CATALOG_HOOK_GROUP:
        registry = threddsRegistry
    else:
        raise ESGPublishError("Cannot get registry for entry point group=%s"%entryPointGroup)

    return registry
