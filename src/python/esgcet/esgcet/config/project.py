#!/usr/bin/env python

import logging
import sys
import os
import string
import re

from esgcet.exceptions import *
from esgcet.config import getConfig, splitLine, splitRecord, genMap, splitMap, initializeExperiments
from registry import getHandlerByEntryPointGroup, ESGCET_FORMAT_HANDLER_GROUP, ESGCET_METADATA_HANDLER_GROUP, ESGCET_THREDDS_CATALOG_HOOK_GROUP
from esgcet.messaging import debug, info, warning, error, critical, exception

ENUM = 1
STRING = 2
FIXED = 3
TEXT = 4

MAND = 1
OPT = 2

WIDGET_TYPE = 0
IS_MANDATORY = 1
IS_THREDDS_PROPERTY = 2
WIDGET_ORDER = 3

MAX_RECURSION_DEPTH = 10

_patpat = re.compile(r'%\(([^()]*)\)s') # Matches the %(name)s pattern


def compareLibVersions(v1, v2):

    if v2 is None:
        return False

    p1 = v1.split()
    p2 = v2.split()


    diff = len(p1) - len(p2)
    
    if (diff > 0):
        for i in range(diff):

            p2.append("0")
    
    for x, y in zip(p1, p2):

        if y < x:
            return False

    return True





def getCategoryType(s):
    sl = s.lower().strip()
    if sl=="enum":
        result = ENUM
    elif sl=="string":
        result = STRING
    elif sl=="fixed":
        result = FIXED
    elif sl=="text":
        result = TEXT
    else:
        raise ESGPublishError("Invalid category type: %s"%s)
    return result

def getBoolean(s):
    sl = s.lower().strip()
    if sl in ("true", "t"):
        result = True
    elif sl in ("false", "f"):
        result = False
    else:
        raise ESGPublishError("Invalid boolean: %s"%s)
    return result

class ProjectHandler(object):

    """
    Base class for project handlers. A *handler* implements the logic associated with obtaining metadata
    for a specific project. Typically a handler is created for each dataset.

    A handler has two important data structures:

    - *context* (see ``getContext``): A dictionary mapping string *fields* (aka *categories*) to values,
      for a specific dataset.
      The values in the context may be obtained from a file, command line options, or GUI input.
      The allowed keys for the context are project-specific, and are defined in the initialization
      file with the ``categories`` directive.
    - *map dictionary* (see ``getMaps``): A map is a dictionary containing name/value pairs, as defined
      in the ``maps`` section of the initialization file. Usage of a map is defined in the handler.
      For example, the IPCC4 handler maps (submodel, time_frequency) pairs to CMOR table IDs.

    These methods should be overridden by concrete handler classes:

    - getResolution
    - readContext
    - validateFile

    These methods have basic implementations, but subclasses may
    need to override them:

    - getContext
    - openPath
    - validateContext

    """

    def __init__(self, name, path, Session, validate=True, offline=False):
        """
        Create a project handler.

        name
          String project name.

        path
          String pathname of a file. If not None, the file is validated to check that it is associated
          with the project.

        Session
          SQLAlchemy Session.

        validate
          If True, create a validating handler which will raise an error if an invalid field value is read or input.

        offline
          If True, files are not scanned.
          
        """
        self.name = name
        self.formatHandlerClass = getHandlerByEntryPointGroup(ESGCET_FORMAT_HANDLER_GROUP, name)
        self.metadataHandlerClass = getHandlerByEntryPointGroup(ESGCET_METADATA_HANDLER_GROUP, name)
        self.metadataHandler = None     # Metadata handler instance associated with this project
        self.threddsCatalogHook = getHandlerByEntryPointGroup(ESGCET_THREDDS_CATALOG_HOOK_GROUP, name, errorIfMissing=False)

        # Try to open the sample file in a project-specific way
        self.path = path

        if not offline and path is not None:
            try:
                fileobj = self.openPath(path)
            except:
                raise ESGPublishError('Error opening %s. Is the data offline?'%path)
            fileobj.close()

        self.validate = (validate in [None, True])
        self.offline = offline
        self.fieldNames = {}            # fieldNames[key] = (categoryType, isMandatory, isThreddsProperty, displayOrder)
        self.context = {}               # context[category] = value
        self.validValues = {}
        self.validMaps = {}             # validMaps[key] = {value1 : entry1, ...}
                                        # Ex: validMaps['creator'] = {'Creator_1':(email_1,), 'Creator_2':(email_2,), ...}
        self.categoryDefaults = {}      # categoryDefaults[key] = default_value
        self.initializeFields(Session)
        self.mapdict = None             # mapdict: tofield => [(fromfields, map, to_index), (fromfields, map, to_index), ...]
        self.contextCached = False      # Set to True to avoid re-reading the context in getContext().

    def openPath(self, path):
        """Open a sample path, returning a project-specific file object,
        (e.g., a netCDF file object or vanilla file object)."""
        fileobj = self.formatHandlerClass.open(path, mode='r')
        return fileobj

    def getMetadataHandler(self, sessionMaker=None):
        """Get the metadata handler associated with this project. The metadata handler
        is created and cached if necessary.
        """
        if self.metadataHandler is None:
            self.metadataHandler = self.metadataHandlerClass(Session=sessionMaker)
        return self.metadataHandler

    def getThreddsCatalogHook(self):
        return self.threddsCatalogHook

    def validateFile(self, fileobj):
        """Raise ESGInvalidMetadataFormat if the file cannot be processed by this handler."""
        config = getConfig()
        projectSection = 'project:'+self.name

        if config.has_option(projectSection, 'min_cmor_version'):
            min_cmor_version = config.get(projectSection, "min_cmor_version", default="0.0.0")

            file_cmor_version = fileobj.getAttribute('cmor_version', None)

            if not compareLibVersions(min_cmor_version, file_cmor_version):
                raise ESGInvalidMetadataFormat("file " + self.path  + " cmor version = " + file_cmor_version  +  ", running checks - minimum = " + min_cmor_version )
            

    def initializeFields(self, Session):
        """Initialize field names and options based on the configuration file."""
        from esgcet.model import Model, Experiment
        config = getConfig()
        projectSection = 'project:'+self.name
        categoryOption = config.get(projectSection, 'categories')
        categorySpecs = splitRecord(categoryOption)
        for category, categoryTypeS, isMandatoryS, isThreddsPropertyS, displayOrderS in categorySpecs:
            categoryType = getCategoryType(categoryTypeS)
            isMandatory = getBoolean(isMandatoryS)
            isThreddsProperty = getBoolean(isThreddsPropertyS)
            displayOrder = string.atoi(displayOrderS)
            self.fieldNames[category] = (categoryType, isMandatory, isThreddsProperty, displayOrder)

        categoryDefaultsOption = config.get(projectSection, 'category_defaults', default=None, raw=True)
        if categoryDefaultsOption is not None:
            categoryDefaultsSpecs = splitRecord(categoryDefaultsOption)
            for category, categoryDefault in categoryDefaultsSpecs:
                self.categoryDefaults[category] = categoryDefault

        session = Session()

        # Find any new experiments. This allows experiments to be added to the config file without
        # running esginitialize.
        if self.fieldNames.has_key('experiment') and self.fieldNames['experiment'][WIDGET_TYPE]==ENUM:
            initializeExperiments(config, self.name, session)

        for category in self.getFieldNames():
            # At the moment some fields are predefined
            if category=="project":
                projects = splitRecord(config.get(projectSection, 'project_options', default=''))
                self.validValues['project'] = [x[0] for x in projects]
            elif category=="model":
                models = session.query(Model).filter_by(project=self.name).all()
                self.validValues['model'] = [x.name for x in models]
            elif category=="experiment":
                experiments = session.query(Experiment).filter_by(project=self.name).all()
                self.validValues['experiment'] = [x.name for x in experiments]
            elif category=="creator":
                creators = splitRecord(config.get(projectSection, 'creator_options', default=''))
                self.validValues['creator'] = [x[0] for x in creators]
                self.validMaps['creator'] = genMap(creators)
            elif category=="publisher":
                publishers = splitRecord(config.get(projectSection, 'publisher_options', default=''))
                self.validValues['publisher'] = [x[0] for x in publishers]
                self.validMaps['publisher'] = genMap(publishers)
            else:
                categoryType = self.getFieldType(category)
                if categoryType==ENUM:
                    option = category+"_options"
                    self.validValues[category] = splitLine(config.get(projectSection, option), ',')

            self.context[category] = ''

        session.close()

    def getFieldNames(self):
        """Get an ordered list of field names.

        Returns a list of field names for this project, as specified in the initialization file.
        """
        names = self.fieldNames.keys()
        names.sort(lambda x, y: cmp(self.fieldNames[x][WIDGET_ORDER], self.fieldNames[y][WIDGET_ORDER]))
        return names

    def getFieldType(self, field):
        """Get the field type, either:
        
        - ENUM: an enumerated list,
        - STRING: a single-line string, editable
        - FIXED: a string, not editable.
        - TEXT: multi-line string, editable
        - None, if the field is not configured

        The values ENUM, STRING, FIXED, and TEXT are imported from package esgcet.config.

        field
          String field name.
        """
        fieldopts = self.fieldNames.get(field, None)
        if fieldopts is not None:
            return fieldopts[WIDGET_TYPE]
        else:
            return None

    def getFieldOptions(self, field):
        """Get the list of valid options for a field. If the field is not enumerated, returns None.

        field
          String field name.
        """
        return self.validValues.get(field, None)

    def getField(self, field):
        """Get the current field value, or None if not defined.

        field
          String field name.
        """
        result = self.context.get(field, None)
        return result

    def isMandatory(self, field):
        """Return True if the field must be set.

        field
          String field name.
        """
        fieldopts = self.fieldNames.get(field, None)
        return (fieldopts is not None and fieldopts[IS_MANDATORY])

    def isCategory(self, field):
        """Return True if the field is a category defined in the initialization file.

        field
          String field name.
        """
        return self.fieldNames.has_key(field)

    def isThreddsProperty(self, field):
        """Return True if the field will be output as a THREDDS property.

        field
          String field name.
        """
        fieldopts = self.fieldNames.get(field, None)
        return (fieldopts is not None and fieldopts[IS_THREDDS_PROPERTY])

    def saveContext(self, datasetName, Session):
        """Save the context to the database.

        datasetName
          String dataset identifier.

        Session
          Database session factory.

        """
        from esgcet.publish.utility import getTypeAndLen
        from esgcet.model import Dataset, DatasetAttribute, map_to_charset

        session = Session()
        dset = session.query(Dataset).filter_by(name=datasetName).first()

        for key, value in self.context.items():
            atttype, attlen = getTypeAndLen(value)
            attribute = DatasetAttribute(key, map_to_charset(value), atttype, attlen, is_category=True, is_thredds_category=self.isThreddsProperty(key))
            dset.attributes[attribute.name] = attribute

        session.commit()
        session.close()

    def generateNameFromContext(self, parameter, **extraParams):
        """
        Generate a name from a config file parameter, relative to the current
        handler context. Mapped format strings are also resolved.

        Returns a string name.

        parameter
          The configuration file option, e.g., 'dataset_id'

        extraParams
          Extra options, added to the current context before resolving the name.
          On return self.context is not modified.
        """
        tempcontext = {}
        tempcontext.update(self.context)
        tempcontext.update(extraParams)
        section = 'project:'+self.name
        config = getConfig()
        generatedName = self.generateNameFromContext_1(parameter, config, section, 1, **tempcontext)
        return generatedName

    def generateNameFromContext_1(self, parameter, config, section, depth, **tempcontext):
        if depth>MAX_RECURSION_DEPTH:
            raise ESGPublishError("Recursion level too deep: Cannot generate value of %s for project %s, context = %s"%(parameter, self.name, `self.context`))

        generatedName = None
        try:
            generatedName = config.get('project:'+self.name, parameter, False, tempcontext)
        except:

            # The parameter value could not be resolved just from the context.
            # Try adding mapped fields to the temporary context.
            try:
                try:
                    paramvalue = config.get(section, parameter, raw=True)
                except:
                    # If the parameter is not found, try %(parameter)s to get mapped parameters
                    paramvalue = "%%(%s)s"%parameter
                idfields = re.findall(_patpat, paramvalue)
                fieldAdded = False
                for field in idfields:
                    if tempcontext.has_key(field):
                        continue
                    value = self.getFieldFromMaps(field, tempcontext)
                    if value is None:
                        try:
                            value = self.generateNameFromContext_1(field, config, section, depth+1, **tempcontext)
                        except:
                            pass
                    if value is not None:
                        tempcontext[field] = value
                        fieldAdded = True

                # Only continue interpolating if the temporary context has been augmented
                if fieldAdded:
                    generatedName = self.generateNameFromContext_1(parameter, config, section, depth+1, **tempcontext)
            except:
                raise ESGPublishError("Cannot generate value of %s for project %s, context = %s"%(parameter, self.name, `self.context`))
        if generatedName is None:
            raise ESGPublishError("No %s parameter found for project %s"%(parameter, self.name))
        return generatedName

    def getContext(self, **context):
        """
        Read all metadata fields from the file associated with the handler. Calls ``readContext`` to read the file.

        Returns a context dictionary of fields discovered in the file.

        context
          Dictionary of initial field values, keyed on field names. If a field is initialized, it is not overwritten.
        """
        if self.contextCached:
            return self.context

        if not self.offline:
            f = self.openPath(self.path)
            fileContext = self.readContext(f)
            f.close()
        else:
            fileContext = {}

        self.context['project'] = self.name
        for key, value in fileContext.items():
            self.context[key] = value

        for key, value in context.items():
            self.context[key] = value

        self.generateDerivedContext()

        self.contextCached = True
        return self.context

    def setContext(self, context):
        """
        Set the handler context.

        context
          Dictionary of new key/value pairs.
          
        """
        self.context = context

    def updateContext(self, context, addDefaults=False):
        """
        Add or replace values in the context.

        Returns the context.

        context
          Dictionary of new key/value pairs. If the key is already in the handler context, the value is replaced.
          
        addDefaults
          Boolean flag. If True, set the default context values from the category_defaults option. If the key
          is already in the context, the context value is *not* changed.

        """
        section = 'project:'+self.name
        self.context.update(context)
        if addDefaults:
            for key, pattern in self.categoryDefaults.items():
                if not self.context.has_key(key) or self.context[key]=='':
                    value = self.generateNameFromContext(key, **{key:pattern})
                    self.context[key] = value
                    
        return self.context

    def getContextFromDataset(self, dataset, Session=None, includeNullFields=True):
        """Load the context from a persistent dataset object.

        Returns the context.

        dataset
          Dataset object.

        Session
          SQLAlchemy Session. If not None, the dataset is reattached to a session.

        includeNullFields=True
          If True, include all fieldnames as context keys, even if the value is None.
        """

        # Reassociate the dataset with a session
        if Session is not None:
            session = Session()
            session.add(dataset)

        # Define properties common to all datasets
        self.context['project'] = dataset.project
        self.context['model'] = dataset.model
        self.context['experiment'] = dataset.experiment
        self.context['run_name'] = dataset.run_name

        # Get properties stored as attributes
        for property in self.getFieldNames():
            attr = dataset.attributes.get(property, None)
            if attr is not None:
                self.context[property] = attr.value
            elif includeNullFields:
                self.context[property] = None

        if Session is not None:
            session.close()
        self.contextCached = True       # getContext() will not overwrite self.context
        return self.context

    def isEnumerated(self, field):
        return (self.getFieldType(field) == ENUM)

    def compareEnumeratedValue(self, value, options, delimiter=""):

# TODO:  here we can add additional delimiters (replace space with comma, etc)        
       

        if len(delimiter) > 0:
            arr = []
            if delimiter == 'space':

                arr = value.split(' ')
            elif delimiter == 'comma':
                arr = value.split(',')
            else:
                raise ESGPublishError("Unsupported facet delimiter %s", delimiter)
            for vv in arr:
                if not vv in options:
                    return False
            
            return True
        else:
                
            return (value in options)

    def mapValidFieldOptions(self, field, options):
        """
        Map to case-sensitive list of options for field.
        """
        return options

    def mapEnumeratedValues(self, context):
        """
        Map enumerated values to case-sensitive values if possible.

        There is no return value. The context argument is a dictionary
        that may be modified by replacing values with corresponding validated values.
        """
        pass

    def validateContext(self, context):
        """
        Validate context values:

        - Mandatory values must be non-blank, and if enumerated have a valid value
        - If enumerated, non-mandatory values must be blank or have a valid value
        otherwise if enumerated the field must be either be blank or one of the valid values

        Raises ESGPublishError if a validation error occurs

        If the validate configuration option is set to False in the project section,
        validation always succeeds.
        """
        if not self.validate:
            return
        
        for key in context.keys():
            fieldType = self.getFieldType(key)

            # Ignore non-configured fields
            if fieldType is None:
                continue
            
            isenum = (fieldType==ENUM)
            if isenum:
                options = self.getFieldOptions(key)
            value = context[key]

            config = getConfig()

            project_section = 'project:%s' % self.name
            delimiter = config.get(project_section, key + "_delimiter", default="")

            if value in ['', None]:
                # if value not in default context, try to get it from key_pattern or *_map
                option = '%s_pattern' % key
                if config.has_option(project_section, option):
                    value = config.get(project_section, option, False, context)
                    context[key] = value
                elif config.has_option(project_section, 'maps'):
                    for map_option in splitLine(config.get(project_section, 'maps', default=''), ','):
                        from_keys, to_keys, value_dict = splitMap(config.get(project_section, map_option))
                        if key in to_keys:
                            from_values = tuple(context[k] for k in from_keys)
                            to_values = value_dict[from_values]
                            value = to_values[to_keys.index(key)]
                            context[key] = value

            if self.isMandatory(key):
                if value in ['', None]:
                    if isenum:
                        raise ESGInvalidMandatoryField("Mandatory field '%s' not set, must be one of %s"%(key, `options`))
                    else:
                        raise ESGInvalidMandatoryField("Mandatory field '%s' not set"%key)
                elif isenum and not self.compareEnumeratedValue(value, options, delimiter):
                    validOptions = self.mapValidFieldOptions(key, options)
                    raise ESGInvalidMandatoryField("Invalid value of mandatory field '%s': %s, must be one of %s"%(key, value, `validOptions`))
            elif isenum:     # non-mandatory field
                options += ['', None]
                if not self.compareEnumeratedValue(value, options, delimiter):
                    validOptions = self.mapValidFieldOptions(key, options)
                    raise ESGPublishError("Invalid value of '%s': %s, must be one of %s"%(key, value, `validOptions`))

    def getResolution(self):
        """
        Get the THREDDS resolution value.

        Returns a string.
        """
        return None

    def getMaps(self):
        """Get a dictionary of maps from the project section.
        """
        config = getConfig()
        section = 'project:'+self.name
        if self.mapdict is None:
            mapdict = {}
            projectMaps = splitLine(config.get(section, 'maps', default=""), ',')
            for option in projectMaps:
                if option=="":
                    continue
                fromcat, tocat, projectMap = splitMap(config.get(section, option))
                for to_index, field in enumerate(tocat):
                    value = (fromcat, projectMap, to_index)
                    if mapdict.has_key(field):
                        mapdict[field].append(value)
                    else:
                        mapdict[field] = [value]
            self.mapdict = mapdict
        return self.mapdict

    def getFieldFromMaps(self, field, groupdict):
        """Get a field value from this project's maps, which are optionally defined in
        the initialization file.

        Returns the field value, or None if not found.

        field
          Field string name.

        groupdict
          Dictionary defining the 'from' fields for the maps.
        """
        mapdict = self.getMaps()
        keyset = set(groupdict.keys())
        if not mapdict.has_key(field):
            return None
        for fromfields, projectMap, to_index in mapdict[field]:
            if set(fromfields).issubset(keyset):
                key = tuple([groupdict[fromfield] for fromfield in fromfields])
                value = projectMap.get(key)
                if value is not None:
                    return value[to_index]
        return None

    def generateDatasetId(self, option, idfields, groupdict, multiformat=None):
        """
        Generate a dataset ID from a config file option.

        Returns the ID.

        option
          Name of the dataset ID option

        idfields
          List of string fields needed to generate the ID, or a list of lists
          if multiformat is not None.

        groupdict
          Dictionary to generate the ID from.

        multiformat
          Set for multi-field formats, such as dataset_id.

        """
        config = getConfig()
        section = 'project:'+self.name
        mapdict = self.getMaps()
        keys = groupdict.keys()

        foundValue = False
        if multiformat is not None:
            for fieldlist, format in zip(idfields, multiformat):
                try:
                    result = self.generateDatasetId_1(option, fieldlist, groupdict, config, section, mapdict, keys, format=format)
                except:
                    continue
                else:
                    foundValue = True
                    break
        else:
            try:
                result = self.generateDatasetId_1(option, idfields, groupdict, config, section, mapdict, keys)
            except:
                pass
            else:
                foundValue = True

        if not foundValue:
            raise ESGPublishError("Cannot generate a value for option %s, please specify the dataset id explicitly."%option)

        return result

    def generateDatasetId_1(self, option, idfields, groupdict, config, section, mapdict, keys, format=None):
        """
        Helper function for generateDatasetId.

        """

        # If any id fields are missing, fill them in from a map if possible
        for field in idfields:
            if field not in keys:
                value = self.getFieldFromMaps(field, groupdict)
                if value is not None:
                    groupdict[field] = value

        # Map dictionary arguments to 'valid' values where possible
        self.mapEnumeratedValues(groupdict)

        # Generate the dataset ID
        if format is None:
            datasetId = config.get(section, option, False, groupdict)
        else:
            config.set(section, "_temp_", format)
            datasetId = config.get(section, "_temp_", False, groupdict)
            config.remove_option(section, "_temp_")
        return datasetId


    def getFilters(self, option='directory_format'):
        """Return a list of regular expression filters associated with the option in the configuration file.
         This can be passed to ``nodeIterator`` and ``processNodeMatchIterator``.
        """
        config = getConfig()
        section = 'project:'+self.name
        directory_format = config.get(section, option, raw=True)
        formats = splitLine(directory_format)
        filters = []
        for format in formats:
            pat = format.strip()
            pat2 = pat.replace('\.','__ESCAPE_DOT__')
            pat3 = pat2.replace('.', r'\.')
            pat4 = pat3.replace('__ESCAPE_DOT__', r'\.')
            # pattern = re.sub(_patpat, r'(?P<\1>[^/.]*)', pat4)
            pattern = re.sub(_patpat, r'(?P<\1>[^/]*)', pat4)
            filter = '^'+pattern+'$'
            filters.append(filter)
        return filters


    def getDatasetIdFields(self):
        """Get a list of (lists of) fields associated with the dataset ID. This may be passed to ``generateDatasetId``.
        """
        config = getConfig()
        section = 'project:'+self.name
        dataset_id_formats = splitLine(config.get(section, 'dataset_id', raw=True))
        idfields = [re.findall(_patpat, format) for format in dataset_id_formats]
        return idfields, dataset_id_formats

    def generateDirectoryMap(self, directoryList, filefilt, initContext=None, datasetName=None, use_version=False):
        """Generate a directory map. Recursively scan each directory in *directoryList*,
        locating each directory with at least one file matching filefilt.

        Returns a directory map (dictionary) mapping
        dataset_id => [(directory_path, filepath), (directory_path, filepath), ...]
        where the dataset_id is generated by matching the 'directory_format' configuration option to
        each directory path. The map has one entry per directory, where it is assumed that
        all files in the directory belong to the same dataset.

        directoryList
          List of directories to scan. The scan searches for directories matching the 'directory_format'
          configuration file option for this project, and having at least one file matching *filefilt*.

        filefilt
          Regular expression as defined by the Python **re** module. Matched against the file basename.

        initContext
          Dictionary of field => value items. Entries override values found from matching the directory paths.

        datasetName
          Name of the dataset. If not specified, generate with ``generateDatasetId()``.
        """
        from esgcet.publish import nodeIterator

        # If the dataset name is specified, no need to get directory format filters
        
        if datasetName is None:
            # Get the dataset_id and filters
            filters = self.getFilters()
            config = getConfig()
            section = 'project:'+self.name
            dataset_id_formats = splitLine(config.get(section, 'dataset_id', raw=True))
            idfields = [re.findall(_patpat, format) for format in dataset_id_formats]
        else:
            filters = [r'.*$']

        # Iterate over nodes
        mapdict = self.getMaps()
        datasetMap = {}
        for direc in directoryList:
            if direc[-1]=='/':
                direc = direc[:-1]
            nodeiter = nodeIterator(direc, filters, filefilt)
            for nodepath, filepath, groupdict in nodeiter:
                if initContext is not None:
                    groupdict.update(initContext)
                if not groupdict.has_key('project'):
                    groupdict['project'] = self.name
                if datasetName is None:
                    try:
                        datasetId = self.generateDatasetId('dataset_id', idfields, groupdict, multiformat=dataset_id_formats)
                        if use_version and 'version' in groupdict:
                            drsversion = groupdict['version']
                            if not re.match('^[0-9]+$', drsversion[0]): # e.g. vYYYYMMDD
                                drsversion = drsversion[1:]
                            datasetId += '#%s'%drsversion
                    except:
                        allfields = reduce(lambda x,y: set(x)+set(y), idfields)
                        missingFields = list((set(allfields)-set(groupdict.keys()))-set(config.options(section)))
                        raise ESGPublishError("Cannot generate a value for dataset_id. One of the following fields could not be determined from the directory structure: %s\nDirectory = %s"%(`missingFields`, nodepath))
                else:
                    warning("Empty dataset name.  Check that directory hierarchy format matches the configured format string in esg.ini")
                    datasetId = datasetName
                if datasetMap.has_key(datasetId):
                    datasetMap[datasetId].append((nodepath, filepath))
                else:
                    datasetMap[datasetId] = [(nodepath, filepath)]

        if (len(datasetMap) == 0 ):
            warning("Empty datasetMap.  Check that directory hierarchy format matches the configured format string in esg.ini")
        return datasetMap

    def parseDatasetName(self, datasetName, context):
        """Parse a dataset name.

        Returns a dictionary, mapping field => value. The config file option 'dataset_id'
        is used to parse the name into fields.

        datasetName
          String dataset identifier.

        context
          Initial context dictionary. This argument is altered on output.

        """
        config = getConfig()
        section = 'project:'+self.name
        datasetIdFormatList = config.get(section, 'dataset_id', raw=True, default=None)
        if datasetIdFormatList is None:
            # warning("No dataset_id option found for project %s"%self.name)
            return context
        datasetIdFormats = splitLine(datasetIdFormatList)

        formatMatched = False
        for idFormat in datasetIdFormats:

            # '.' => '\.'
            newinit = re.sub(r'\.', r'\.', idFormat.strip())
            
            # %(name)s => (?P<name>[^.]*)
            newinit = re.sub(_patpat, r'(?P<\1>[^.]*)', newinit)

            # If experiment is enumerated, match on the experiment options. This allows
            # experiment ids to contain periods (.) .
            experimentOptions = self.getFieldOptions('experiment')

            # Map to case-sensitive options
            experimentOptions = self.mapValidFieldOptions('experiment', experimentOptions)
            if idFormat.find('%(experiment)s')!=-1 and experimentOptions is not None:
                if len(experimentOptions) > 0:
                    optionOr = reduce(lambda x,y: x+'|'+y, experimentOptions)
                    experimentPattern = r'(?P<experiment>%s)'%optionOr
                    newinit = newinit.replace('(?P<experiment>[^.]*)', experimentPattern)
            
            if newinit[-1]!='$':
                newinit += '$'

            match = re.match(newinit, datasetName)

            if match is None:
                continue
            else:
                result = match.groupdict()
                formatMatched = True
            for key, value in result.items():
                if context.has_key(key) and value!=context[key]:
                    warning("Dataset ID=%s, but %s=%s"%(datasetName, key, context[key]))
                else:
                    context[str(key)] = value
            break

        if not formatMatched:
            warning("Dataset ID: %s does not match the dataset_id format(s): %s"%(datasetName, `datasetIdFormats`))

        return context

    def getParentId(self, datasetName):
        """Get the parent ID of a dataset. This is a no-op, since the P2P system
        does not support hierarchical datasets.

        Returns the string parent identifier.

        datasetName
          String dataset identifier.
        """

        parentId = 'ROOT'
        return parentId

    def readContext(self, sdfile, **kw):
        """Get a dictionary of key/value pairs from an open file.

        sdfile
          instance of FormatHandler

        """
        raise ESGMethodNotImplemented

    def generateDerivedContext(self):
        """Generate properties based on existing context values.

        self.context is modified as a side effect.
        """
        pass

    def resetContext(self):
        """Reset the context to an empty dictionary.
        """
        self.context = {}
        self.contextCached = False

    def generateDirectoryMapFromFiles(self, directoryList, filefilt, initContext=None, datasetName=None):
        """Generate a directory map using file metadata. Recursively scan each directory in *directoryList*,
        locating each file matching filefilt.

        Returns a directory map (dictionary) mapping
        dataset_id => [(directory_path, filepath), (directory_path, filepath), ...]
        where the dataset_id is generated from metadata in each file. The map has one entry per file
        that matches filefilt. Compare with ``generateDirectoryMap``.

        directoryList
          List of directories to scan. The scan searches for directories matching the 'directory_format'
          configuration file option for this project, and having at least one file matching *filefilt*.

        filefilt
          Regular expression as defined by the Python **re** module. Matched against the file basename.

        initContext
          Dictionary of field => value items. Entries override values found in the file.

        datasetName
          Name of the dataset. If not specified, generate with ``generateDatasetId()``.
        """

        from esgcet.publish import multiDirectoryIterator

        datasetMap = {}
        multiIter = multiDirectoryIterator(directoryList, filefilt=filefilt)
        for path, sizet in multiIter:
            self.resetContext()
            self.path = path
            context = self.getContext()
            if initContext is not None:
                self.context.update(initContext)
            if datasetName is None:
                try:
                    generatedDatasetName = self.generateNameFromContext('dataset_id')
                except ESGPublishError:
                    print 'Error generating dataset for file:', path
                    raise
            else:
                generatedDatasetName = datasetName
            entry = (os.path.dirname(path), path)
            if generatedDatasetName in datasetMap:
                datasetMap[generatedDatasetName].append(entry)
            else:
                datasetMap[generatedDatasetName] = [entry]

        return datasetMap

    def threddsIsValidVariableFilePair(self, variable, fileobj):
        """Returns True iff the variable and file should be published
        to a per-variable THREDDS catalog for this project.

        variable
          A Variable instance.

        fileobj
          A File instance.
        """
        return True


    def check_pid_avail(self, project_config_section, config, version=None):
        """ Returns the pid_prefix if project uses PIDs, otherwise returns None

         project_config_section
            The name of the project config section in esg.ini

        config
            The configuration (ini files)

        version
            Integer or Dict with dataset versions
        """
        pid_prefix = None
        if config.has_section(project_config_section):
            pid_prefix = config.get(project_config_section, 'pid_prefix', default=None)
        return pid_prefix


    def get_pid_config(self, project_config_section, config):
        """ Returns the project specific pid config

         project_config_section
            The name of the project config section in esg.ini

        config
            The configuration (ini files)
        """
        pid_messaging_service_exchange_name = None
        if config.has_section(project_config_section):
            pid_messaging_service_exchange_name = config.get(project_config_section, 'pid_exchange_name', default=None)
        if not pid_messaging_service_exchange_name:
            raise ESGPublishError("Option 'pid_exchange_name' is missing in section '%s' of esg.ini." % project_config_section)

        # get credentials from config:project section of esg.ini
        if config.has_section(project_config_section):
            pid_messaging_service_credentials = []
            credentials = splitRecord(config.get(project_config_section, 'pid_credentials', default=''))
            if credentials:
                priority = 0
                for cred in credentials:
                    if len(cred) == 7 and isinstance(cred[6], int):
                        priority = cred[6]
                    elif len(cred) == 6:
                        priority += 1
                    else:
                        raise ESGPublishError("Misconfiguration: 'pid_credentials', section '%s' of esg.ini." % project_config_section)

                    ssl_enabled = False
                    if cred[5].strip().upper() == 'TRUE':
                        ssl_enabled = True

                    pid_messaging_service_credentials.append({'url': cred[0].strip(),
                                                              'port': cred[1].strip(),
                                                              'vhost': cred[2].strip(),
                                                              'user': cred[3].strip(),
                                                              'password': cred[4].strip(),
                                                              'ssl_enabled': ssl_enabled,
                                                              'priority': priority})

            else:
                raise ESGPublishError("Option 'pid_credentials' is missing in section '%s' of esg.ini." % project_config_section)
        else:
            raise ESGPublishError("Section '%s' not found in esg.ini." % project_config_section)

        return pid_messaging_service_exchange_name, pid_messaging_service_credentials

    def get_citation_url(self, project_config_section, config, dataset_name, dataset_version, test_publication):
        """ Returns the citation_url if a project uses citation, otherwise returns None

         project_section
            The name of the project section in the ini file

        config
            The configuration (ini files)

        dataset_name
            Name of the dataset

        dataset_version
            Version of the dataset
        """
        if config.has_option(project_config_section, 'citation_url'):
            try:
                pattern = self.getFilters(option='dataset_id')
                attributes = re.match(pattern[0], dataset_name).groupdict()
                if 'version' not in attributes:
                    attributes['version'] = str(dataset_version)
                if 'dataset_id' not in attributes:
                    attributes['dataset_id'] = dataset_name
                return config.get(project_config_section, 'citation_url', 0, attributes)
            except:
                warning('Unable to generate a citation url for %s' % dataset_name)
                return None
        else:
            return None
