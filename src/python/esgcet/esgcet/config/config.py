#!/usr/bin/env python

import sys
import os
import string
import logging
import re
from ConfigParser import SafeConfigParser, NoOptionError, DEFAULTSECT
from xml.etree.ElementTree import parse
from esgcet.exceptions import *
from registry import register
from esgcet.messaging import debug, info, warning, error, critical, exception

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
        if record=='':
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
        if record=='':
            continue
        fields = map(string.strip, record.split(sep))
        fromfields = tuple(fields[0:nfrom])
        tofields = tuple(fields[nfrom:])
        if result.has_key(fromfields):
            raise ESGPublishError("Duplicate 'from' fields in map entry: %s"%record)
        if len(fromfields)!=nfrom or len(tofields)!=nto:
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

def loadConfig1(configFile):
    if configFile is None:

        # First check the environment variable ESGINI
        configFile = os.environ.get('ESGINI')
        if configFile is not None:
            if not os.path.exists(configFile):
                raise ESGPublishError("Cannot find configuration file (specified in $ESGINI): %s"%configFile)
            else:
                config1 = SaneConfigParser(configFile)
                config1.read(configFile)
        else:
            
            # Then look in $HOME/.esgcet/esg.ini
            home = os.environ.get('HOME')
            if home is not None:
                configFile = os.path.join(home, '.esgcet', 'esg.ini')
            if configFile is not None and os.path.exists(configFile):
                config1 = SaneConfigParser(configFile)
                config1.read(configFile)

            # If not found, look in the Python installation directory
            else:
                try:
                    from pkg_resources import resource_stream
                except:
                    raise ESGPublishError("No configuration file specified.")

                fp = resource_stream('esgcet.config.etc', 'esg.ini')
                config1 = SaneConfigParser(`fp`)
                config1.readfp(fp)
    else:    
        if not os.path.exists(configFile):
            raise ESGPublishError("Cannot find configuration file: %s"%configFile)
        config1 = SaneConfigParser(configFile, defaults={'here':os.getcwd()})
        config1.read(configFile)
    return config1

def loadConfig(configFile):
    """
    Load the 'ini' style configuration file.

    Returns a ConfigParser.SafeConfigParser object with the file preloaded. If the configuration has already been read, the existing parser is returned. The configuration file is located as follows:

    - If configFile is None, use the first existing file::

      - Use $HOME/.esgcet/esg.ini
      - The system-wide default esg.ini, in the Python site-packages/esgcet/config/etc/esg.ini. Note this file may be inside a .egg file. The init file can be extracted with unzip.

    - otherwise use configFile if it exists
    - else look in the current directory.

    configFile
      String pathname of the .ini configuration file. If None, find the configuration file as described above.
    """
    global config

    if config is None:
        config = loadConfig1(configFile)
    return config

def initLogging(section, override_sa=None):
    """
    Initialize logging based on specs in the config file section. If override_sa is set to an engine, sqlalchemy logging uses the specs as well.

    The logger hierarchy is::

      - root logger (name = '')
      - sqlalchemy (name = 'sqlalchemy')
      - engine (name = 'sqlalchemy.engine.base.Engine.0x...'

    section
      String configuration file section.

    override_sa
      SQLAlchemy engine instance. If set:
      
      - Only the root logger handles output. This allows SQLAlchemy output to be redirected with the log_filename parameter.
      - If the log_level parameter is gteater than logging.INFO, SQLAlchemy output is suppressed.
    """
    global config

    if config is None:
        config = loadConfig(None)
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
        if len(saLogger.handlers)>0:
            saLogger.removeHandler(saLogger.handlers[0])
        if log_level is not None:
            override_sa.logger.setLevel(log_level)

def loadStandardNameTable(path):
    """Load the CF standard name table at path.
    Returns a list of StandardNames.
    """
    from esgcet.model import StandardName
    if path is None:
        try:
            from pkg_resources import resource_filename
            path = resource_filename('esgcet.config.etc', 'cf-standard-name-table.xml')
        except:
            raise ESGPublishError("No standard name table specified.")

    tree = parse(path)
    root = tree.getroot()
    standardNames = {}
    for node in root:
        if node.tag=='entry':
            name = node.attrib['id'].strip()
            units = amip = grib = description = ''
            for subnode in node:
                if subnode.tag=='canonical_units':
                    units = subnode.text.strip()
                elif subnode.tag=='amip':
                    amip = subnode.text
                elif subnode.tag=='grib':
                    grib = subnode.text
                elif subnode.tag=='description':
                    description = subnode.text
                else:
                    raise ESGPublishError("Invalid standard name table tag: %s"%subnode.tag)

            standardName = StandardName(name, units, amip=amip, grib=grib, description=description)
            standardNames[name] = standardName
            
    for node in root:
        if node.tag=='alias':
            name = node.attrib['id'].strip()
            units = amip = grib = description = ''
            for subnode in node:
                if subnode.tag=='entry_id':
                    try:
                        entry = standardNames[subnode.text.strip()]
                    except:
                        raise ESGPublishError("No entry for standard name alias: %s"%subnode.text)
                else:
                    raise ESGPublishError("Invalid standard name table tag: %s"%subnode.tag)

            standardName = StandardName(name, entry.units, entry.amip, entry.grib, entry.description)
            standardNames[name] = standardName

    result = standardNames.values()
    result.sort(lambda x,y: cmp(x.name, y.name))
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
    while line:
        if line[0]!='#':
            yield splitter(line)
        line = f.readline()
    return

def registerHandlers():
    """Read the project handlers from the init file handler parameters, and add to the registry."""
    # Get the project names
    projectOption = config.get('initialize', 'project_options')
    projectSpecs = splitRecord(projectOption)
    for projectName, projectDesc, search_order in projectSpecs:

        # For each project: get the handler
        handlerName = config.get('project:'+projectName, 'handler')
        
        # Get the handler class and register it
        if handlerName is None:
            info("No handler spec found for project %s"%projectName)
        else:
            m, cls = handlerName.split(':')
            register(projectName, m, cls, search_order)

def initializeExperiments(config, projectName, session):
    from esgcet.model import Experiment, Project

    projectSection = 'project:'+projectName
    experimentOption = config.get(projectSection, 'experiment_options')
    experimentSpecs = splitRecord(experimentOption)
    try:
        for projectId, experimentName, experimentDesc in experimentSpecs:
            if projectId!=projectName:
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
        raise ESGPublishError('Invalid input: %s %s %s'%( projectId, experimentName, experimentDesc))
    
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

    if len(offlineListerSpecs)==1:
        result = offlineListerSpecs[0][1]
    else:
        # If no service specified, just get the first one
        if service is None:
            threddsOfflineSpecs = getThreddsServiceSpecs(config, section, 'thredds_offline_services')
            service = threddsOfflineSpecs[0][2]

        # Find the lister for the named service
        for serviceName, lister in offlineListerSpecs:
            if service==serviceName:
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
        if len(item)==3:
            item.append(None)
        elif len(item)==4:
            if item[3].strip()=='':
                item[3]==None
        else:
            raise ESGPublishError("Invalid configuration option %s: %s"%(option, `item`))
        serviceBase = item[1].strip()

        # Ensure that service base has a trailing slash
        if serviceBase[-1]!=os.sep:
            serviceBase += os.sep
            item[1] = serviceBase

    return threddsSpecs
    
