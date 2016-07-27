#!/usr/bin/env python

import sys
import os
import string
import logging
import re
import urlparse
from ConfigParser import SafeConfigParser, NoOptionError, DEFAULTSECT
from xml.etree.ElementTree import parse
from esgcet.exceptions import *
from registry import register, registerHandlerName, setRegisterSearchOrder, getRegistry, ESGCET_PROJECT_HANDLER_GROUP, ESGCET_FORMAT_HANDLER_GROUP, ESGCET_METADATA_HANDLER_GROUP, ESGCET_THREDDS_CATALOG_HOOK_GROUP
from esgcet.messaging import debug, info, warning, error, critical, exception

# SQLAlchemy versions <0.6 have protocol "postgres", >=0.6 use "postgresql"
from sqlalchemy import __version__ as sqlalchemy_version

# Handler onfiguration options, one for each handler type
PROJECT_NAME_OPTION = "project_handler_name"
FORMAT_NAME_OPTION = "format_handler_name"
METADATA_NAME_OPTION = "metadata_handler_name"
THREDDS_CATALOG_HOOK_OPTION = "thredds_catalog_hook"

# Default options
DEFAULT_FORMAT_NAME_OPTION = "netcdf_builtin"
DEFAULT_METADATA_NAME_OPTION = "cf_builtin"

# Backward compatibility
HANDLER_OPTION = "handler"

config = None

class SaneConfigParser(SafeConfigParser):

    def __init__(self, name, defaults=None):
        SafeConfigParser.__init__(self, defaults=defaults)
        self.name = name

    def get(self, section, option, raw=False, vars=None, **options):
        if vars is None:
            vars = {'here' : os.getcwd()}
        elif not vars.has_key('here'):
            vars['here'] = os.getcwd()

        home = os.environ.get('HOME')
        if home is not None:
            vars['home'] = home

        pythonbin = os.path.join(sys.prefix, 'bin')
        vars['pythonbin'] = pythonbin

        try:
            if option == 'dburl':
                value = self.getdburl(section, raw=raw, vars=vars)
            else:
                value = SafeConfigParser.get(self, section, option, raw=raw, vars=vars)
        except NoOptionError:
            if options.has_key('default'):
                value = options['default']
            else:
                raise ESGPublishError("Configuration file option missing: %s in section: %s, file=%s"%(option, section, self.name))
        return value

    def getboolean(self, section, option, default=None):
        try:
            value = SafeConfigParser.getboolean(self, section, option)
        except AttributeError:
            value = default
        except ESGPublishError:
            value = default
        return value

    def getint(self, section, option, default=None):
        try:
            value = SafeConfigParser.getint(self, section, option)
        except AttributeError:
            value = default
        except ESGPublishError:
            value = default
        return value

    def getfloat(self, section, option, default=None):
        try:
            value = SafeConfigParser.getfloat(self, section, option)
        except AttributeError:
            value = default
        except ESGPublishError:
            value = default
        return value

    def getdburl(self, section, raw=False, vars=None):
        value = SafeConfigParser.get(self, section, 'dburl', raw=raw, vars=vars)
        fields = list(urlparse.urlparse(value))
        if fields[0] in ['postgres', 'postgresql']:
            if sqlalchemy_version >= '0.6':
                fields[0] = 'postgresql'
            else:
                fields[0] = 'postgres'
            value = urlparse.urlunparse(fields)
        return value

    def write(self, fp):
        """Write an .ini-format representation of the configuration state.
        with sorting added.
        """
        if self._defaults:
            fp.write("[%s]\n" % DEFAULTSECT)
            defaultItems = self._defaults.items()
            defaultItems.sort()
            for (key, value) in defaultItems:
                fp.write("%s = %s\n" % (key, str(value).replace('\n', '\n\t')))
            fp.write("\n")
        for section in self._sections:
            fp.write("[%s]\n" % section)
            sectionItems = self._sections[section].items()
            sectionItems.sort()
            for (key, value) in sectionItems:
                if key != "__name__":
                    fp.write("%s = %s\n" %
                             (key, str(value).replace('\n', '\n\t')))
            fp.write("\n")

def getConfig():
    return config

def splitRecord(option, sep='|'):
    """Split a multi-line record in a .ini file.

    Returns a list of the form [[field, field, ...], [field, field, ...]]

    option
      String option in the .ini file.

    sep
      Separator character.

    For example, if the init file option is

    ::

        creator_options =
          Contact_1 | foo | http://bar
          Contact_2 | boz@bat.net | 

    then the code::

        lines = config.get(section, 'creator_options')
        result = splitRecord(lines)

    returns::

    [['Contact_1', 'foo', 'http://bar'], ['Contact_2', 'boz@bat.net', '']]

    """
    result = []
    for record in option.split('\n'):
        if record == '':
            continue
        fields = map(string.strip, record.split(sep))
        result.append(fields)

    return result

mapHeaderPattern = re.compile(r'map\s*\((?P<fromcat>[^(:)]*):(?P<tocat>[^(:)]*)\)')
def splitMapHeader(line):
    result = re.match(mapHeaderPattern, line)
    if result is None:
        raise ESGPublishError("Invalid map header: %s"%line)
    groupdict = result.groupdict()
    fromcat = splitLine(groupdict['fromcat'], sep=',')
    tocat = splitLine(groupdict['tocat'], sep=',')
    return fromcat, tocat

def splitMap(option, sep='|'):
    """Split a multi-line map in a .ini file.
    The result is a dictionary mapping the 'from' tuples to the 'to' tuples.
    """
    lines = option.split('\n')
    fromcat, tocat = splitMapHeader(lines[0])
    nfrom = len(fromcat)
    nto = len(tocat)
    result = {}
    for record in lines[1:]:
        if record == '':
            continue
        fields = map(string.strip, record.split(sep))
        fromfields = tuple(fields[0:nfrom])
        tofields = tuple(fields[nfrom:])
        if result.has_key(fromfields):
            raise ESGPublishError("Duplicate 'from' fields in map entry: %s"%record)
        if len(fromfields) != nfrom or len(tofields) != nto:
            raise ESGPublishError("Map entry does not match header: %s"%record)
        result[fromfields] = tofields

    return fromcat, tocat, result

def genMap(records):
    result = {}
    for item in records:
        result[item[0]] = item[1:]
    return result

def splitLine(line, sep='|'):
    """Split a line into fields.

    Returns a list of string fields.

    line
      String line to split.

    sep
      Separator character.
    """
    fields = map(string.strip, line.split(sep))
    return fields

def loadConfig1(init_dir, project, load_projects):

    configFile = getConfigFile(init_dir)
    config1 = SaneConfigParser(configFile)
    config1.read(configFile)

    default_sections = config1.sections()

    if project and 'project:%s'%project not in default_sections:
        configFile = getConfigFile(init_dir, project)
        config1.read(configFile)

    # read all project ini files
    elif load_projects:
        projectOption = config1.get('initialize', 'project_options')
        projectSpecs = splitRecord(projectOption)

        for project, projectDesc, search_order in projectSpecs:
            if 'project:%s'%project not in default_sections:
                configFile = getConfigFile(init_dir, project)
                config1.read(configFile)

        if not config1:
            raise ESGPublishError('Configuration file parsing failed')

    return config1

def getConfigFile(init_dir, project=None):
    if project:
        default_filename = 'esg.%s.ini'%project
        default_envname = 'ESG%sINI'%str.upper(project)
    else:
        default_filename = 'esg.ini'
        default_envname = 'ESGINI'

    # first check environment varibale for ESGINI
    configFile = os.environ.get(default_envname)
    if configFile is None:
        # if env not found check default location of esg.<project>.ini
        if os.path.isfile(os.path.join(os.path.normpath(init_dir), default_filename)):
            configFile = os.path.join(os.path.normpath(init_dir), default_filename)
        else:
            raise ESGPublishError("No project configuration file specified, try setting '%s"%default_envname)
    elif (configFile is None) or (not os.path.exists(configFile)):
        raise ESGPublishError("Cannot find configuration file (specified in $%s)"%default_envname)

    return configFile

def loadConfig(init_dir, project=None, load_projects=True):
    """
    Load the 'ini' style configuration file.

    Returns a ConfigParser.SafeConfigParser object with the configuration file(s) preloaded.
    If the configuration has already been read, the existing parser is returned.

    Default is to load esg.ini and all esg.<project>.ini files from init_dir.

    init_dir
      String path to all .ini configuration files.
    project
        String project name. Load esg.ini and esg.<project>.ini for given project.
    load_projects
        Boolean, if false load esg.ini but not esg.<project>.ini files
    """
    global config

    if config is None:
        config = loadConfig1(init_dir, project, load_projects)
    return config

def initLogging(section, override_sa=None, log_filename=None):
    """
    Initialize logging based on specs in the config file section.
    If override_sa is set to an engine, sqlalchemy logging uses the specs as well.

    The logger hierarchy is::

      - root logger (name = '')
      - sqlalchemy (name = 'sqlalchemy')
      - engine (name = 'sqlalchemy.engine.base.Engine.0x...'

    section
      String configuration file section.

    override_sa
      SQLAlchemy engine instance. If set:

      - Only the root logger handles output. This allows SQLAlchemy output to be redirected with the log_filename parameter.
    log_filename
      String value of the output log filename. Overrides configuration log_filename parameter.
    """
    global config

    if config is None:
        config = loadConfig(None)
    if log_filename is None:
        log_filename = config.get(section, 'log_filename', default=None)
    log_format = config.get(section, 'log_format', raw=True, default=None)
    log_datefmt = config.get(section, 'log_datefmt', default=None)
    log_level = logging.getLevelName(config.get(section, 'log_level', default=None))
    kwargs = {}
    for key, value in zip(['filename', 'format', 'datefmt', 'level'], [log_filename, log_format, log_datefmt, log_level]):
        if value is not None:
            kwargs[key] = value
    logging.basicConfig(**kwargs)

    # Remove sqlalchemy handler. Then only the root logger handles output.
    if override_sa is not None:
        saLogger = logging.getLogger('sqlalchemy')
        if len(saLogger.handlers) > 0:
            saLogger.removeHandler(saLogger.handlers[0])

def loadStandardNameTable(path):
    """Load the CF standard name table at path.
    Returns a list of StandardNames.
    """
    from esgcet.model import StandardName, MAX_STANDARD_NAME_LENGTH
    if path is None:
        try:
            from pkg_resources import resource_filename
            path = resource_filename('esgcet.config.etc', 'cf-standard-name-table.xml')
        except:
            raise ESGPublishError("No standard name table specified.")

    try:
        tree = parse(path)
    except Exception, e:
        raise ESGPublishError("Error parsing %s: %s"%(path, e))
    root = tree.getroot()
    standardNames = {}
    for node in root:
        if node.tag == 'entry':
            name = node.attrib['id'].strip()
            if len(name) > MAX_STANDARD_NAME_LENGTH:
                warning("Standard_name is too long.  Schema requires standard_name to be <= %d characters\n  %s"%(MAX_STANDARD_NAME_LENGTH, name))
                continue

            units = amip = grib = description = ''
            for subnode in node:
                if subnode.tag == 'canonical_units':
                    units = subnode.text.strip()
                elif subnode.tag == 'amip':
                    amip = subnode.text
                elif subnode.tag == 'grib':
                    grib = subnode.text
                elif subnode.tag == 'description':
                    description = subnode.text
                else:
                    raise ESGPublishError("Invalid standard name table tag: %s"%subnode.tag)

            standardName = StandardName(name, units, amip=amip, grib=grib, description=description)
            standardNames[name] = standardName

    for node in root:
        if node.tag == 'alias':
            name = node.attrib['id'].strip()
            units = amip = grib = description = ''
            for subnode in node:
                if subnode.tag == 'entry_id':
                    try:
                        entry = standardNames[subnode.text.strip()]
                    except:
                        raise ESGPublishError("No entry for standard name alias: %s"%subnode.text)
                else:
                    raise ESGPublishError("Invalid standard name table tag: %s"%subnode.tag)

            standardName = StandardName(name, entry.units, entry.amip, entry.grib, entry.description)
            standardNames[name] = standardName

    result = standardNames.values()
    result.sort(lambda x, y: cmp(x.name, y.name))
    return result

def loadModelsTable(path):
    if path is None:
        try:
            from pkg_resources import resource_filename
            path = resource_filename('esgcet.config.etc', 'esgcet_models_table.txt')
        except:
            raise ESGPublishError("No models table specified.")
    return textTableIter(path)    

def textTableIter(path, sep='|', splitter=splitLine):
    """Iterator that returns a list of options corresponding to one record."""
    f = open(path)
    line = f.readline()
    lineno = 0
    while line:
        lineno += 1
        line = line.strip()
        if len(line) > 0 and line[0] != '#':
            yield lineno, splitter(line)
        line = f.readline()
    return

def registerHandlers(project=None):
    """Read the project handlers from the init file handler parameters, and add to the registry."""

    # Get the project names
    projectOption = config.get('initialize', 'project_options')
    projectSpecs = splitRecord(projectOption)
    projectRegistry = getRegistry(ESGCET_PROJECT_HANDLER_GROUP)
    formatRegistry = getRegistry(ESGCET_FORMAT_HANDLER_GROUP)
    metadataRegistry = getRegistry(ESGCET_METADATA_HANDLER_GROUP)
    threddsRegistry = getRegistry(ESGCET_THREDDS_CATALOG_HOOK_GROUP)

    for projectName, projectDesc, search_order in projectSpecs:
        # process only the given project
        if (project is not None) and (projectName != project):
            continue

        # For each project: get the handler
        handler = config.get('project:'+projectName, HANDLER_OPTION, default=None)
        handlerName = config.get('project:'+projectName, PROJECT_NAME_OPTION, default=None)

        # Get the handler class and register it
        if handlerName is not None:
            registerHandlerName(projectRegistry, projectName, handlerName)
            setRegisterSearchOrder(projectName, search_order)
        elif handler is not None:
            m, cls = handler.split(':')
            register(projectRegistry, projectName, m, cls)
            setRegisterSearchOrder(projectName, search_order)
        else:
            info("No project handler spec found for project %s"%projectName)

        # Get the format handler class and register it
        formatHandlerName = config.get('project:'+projectName, FORMAT_NAME_OPTION, default=None)
        if formatHandlerName is not None:
            registerHandlerName(formatRegistry, projectName, formatHandlerName)
        else:
            registerHandlerName(formatRegistry, projectName, DEFAULT_FORMAT_NAME_OPTION)

        # Get the metadata handler class and register it
        metadataHandlerName = config.get('project:'+projectName, METADATA_NAME_OPTION, default=None)
        if metadataHandlerName is not None:
            registerHandlerName(metadataRegistry, projectName, metadataHandlerName)
        else:
            registerHandlerName(metadataRegistry, projectName, DEFAULT_METADATA_NAME_OPTION)

        # Get the thredds catalog hook if any
        threddsCatalogHookName = config.get('project:'+projectName, THREDDS_CATALOG_HOOK_OPTION, default=None)
        if threddsCatalogHookName is not None:
            registerHandlerName(threddsRegistry, projectName, threddsCatalogHookName)

def initializeExperiments(config, projectName, session):
    from esgcet.model import Experiment, Project

    projectSection = 'project:'+projectName
    experimentOption = config.get(projectSection, 'experiment_options')
    experimentSpecs = splitRecord(experimentOption)
    try:
        for projectId, experimentName, experimentDesc in experimentSpecs:
            if projectId != projectName:
                continue

            # Check if the experiment exists
            experiment = session.query(Experiment).filter_by(name=experimentName, project=projectName).first()
            if experiment is None:
                info("Adding experiment %s for project %s"%(experimentName, projectName))
                experiment = Experiment(experimentName, projectName, experimentDesc)
                project = session.query(Project).filter_by(name=projectName).first()
                if project is None:
                    raise ESGPublishError('No such project: %s'%projectName)
                project.experiments.append(experiment)
                session.add(experiment)
                session.commit()
    except ValueError:
        raise ESGPublishError('experiment_options is misconfigured in section %s: %s'%(projectSection, experimentOption))

def getOfflineLister(config, section, service=None):
    """Get the offline lister section for a service.

    config
      Configuration instance, e.g. from getConfig().

    section
      Project configuration section name.

    service
      Name of the service, such as "HRMatPCMDI". If not specified and only one offline service exists,
      return the lister for that service, otherwise raise an error.
    """

    offlineListerOption = config.get('DEFAULT', 'offline_lister')
    offlineListerSpecs = splitRecord(offlineListerOption)

    if len(offlineListerSpecs) == 1:
        result = offlineListerSpecs[0][1]
    else:
        # If no service specified, just get the first one
        if service is None:
            threddsOfflineSpecs = getThreddsServiceSpecs(config, section, 'thredds_offline_services')
            service = threddsOfflineSpecs[0][2]

        # Find the lister for the named service
        for serviceName, lister in offlineListerSpecs:
            if service == serviceName:
                result = lister
                break
        else:
            raise ESGPublishError("Service not found in offline_lister configuration: %s"%service)

    return result

def getThreddsAuxiliaryServiceSpecs(config, section, option, multiValue=False):
    """Get the specs for an THREDDS service option, such as thredds_service_applications.

    Return a dictionary: service_name => value. If multiValue is true, value is a list of strings,
    otherwise is a string. If the option is not set in the configuration file, return None

    config
      Configuration instance, e.g. from getConfig().

    section
      Project configuration section name.

    option
      String option name

    multiValue
      Boolean, if True return list of string values, if False return string values.
    """
    threddsOption = config.get(section, option, default=None)
    if threddsOption is None:
        return None

    threddsSpecs = splitRecord(threddsOption)
    result = {}
    for serviceName, value in threddsSpecs:
        if multiValue:
            if result.has_key(serviceName):
                result[serviceName].append(value)
            else:
                result[serviceName] = [value]
        else:
            result[serviceName] = value

    return result

def getThreddsServiceSpecs(config, section, option):
    """Get the specs for a THREDDS service option.

    config
      Configuration instance, e.g. from getConfig().

    section
      Project configuration section name.

    option
      String option name
    """
    threddsOption = config.get(section, option)
    threddsSpecs = splitRecord(threddsOption)
    for item in threddsSpecs:
        if len(item) == 3:
            item.append(None)
        elif len(item) == 4:
            if item[3].strip() == '':
                item[3] == None
        else:
            raise ESGPublishError("Invalid configuration option %s: %s"%(option, `item`))
        serviceBase = item[1].strip()
        serviceType = item[0].strip()

        # Ensure that LAS service base does NOT have a trailing slash ...
        if serviceType == 'LAS':
            if serviceBase[-1] == os.sep:
                item[1] = serviceBase[:-1]
        # ... and that a non-LAS service base has a trailing slash
        elif serviceBase[-1] != os.sep:
            serviceBase += os.sep
            item[1] = serviceBase

    return threddsSpecs
