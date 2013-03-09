import sys
import re
import time, datetime

from esgcet.publish import parseDatasetVersionId
from esgcet.model import Dataset, DatasetVersion, Event, eventName, eventNumber
from esgcet.config import getHandlerByName
from esgcet.exceptions import *
from esgcet.messaging import warning
from sqlalchemy import or_

# Query operations
EQ=1
LIKE=2

def leng(item):
    if item is not None:
        return len(item)
    else:
        return 4

def getItemCount(header, tuples):
    itemCount = [len(item) for item in header]
    for item in tuples:
        try:
            itemCount = map(lambda x,y: max(x,y), itemCount, [leng(t) for t in item])
        except:
            print item
            raise
    return itemCount

def printResult(header, tuples, out=sys.stdout, printHeaders=True):
    """Print a query result.

    header
      A list of property names.

    tuples
      A list of result tuples. Each tuple has the same length as the header, and each item in the tuple corresponds to the
      respective header item. For example, if the header is ['field1', 'field2'] then ``tuples`` might have the value [(dataset1_field1, dataset1_field2), (dataset2_field1, dataset2_field2), ...]

    out
      Output file object.

    printHeaders
      Boolean flag. If True, print header and trailer lines.
      
    """
    itemCount = getItemCount(header, tuples)
    width = reduce(lambda x,y: x+y, itemCount)+3*len(itemCount)-1
    breakline = '+'+width*'-'+'+'
    if printHeaders:
        format = '| '+reduce(lambda x,y: x+' | '+y, ["%%-%ds"%item for item in itemCount])+' |'
    else:
        format = reduce(lambda x,y: x+' | '+y, ["%%-%ds"%item for item in itemCount])
    if printHeaders:
        print >>out, breakline
        print >>out, format%tuple(header)
        print >>out, breakline
    count = 0
    for item in tuples:
        count += 1
        try:
            print >>out, format%item
        except:
            print >>out, 'Barf!'
            print >>out, item
            sys.exit(0)
    if printHeaders:
        print >>out, breakline
        print >>out, '%d results found'%count

def parseQuery(arg):
    """Parse a query argument.

    Returns a tuple of the form (name, op, value) where op is EQ or LIKE.

    arg
      Query argument of the form name=value. If value has a % wildcard character, the op is LIKE.
    """
    try:
        name, value = arg.split('=')
    except:
        raise Exception("Query arguments have the form property=value")
    name = name.strip()
    value = value.strip()
    if value.find('%')!=-1:
        op = LIKE
    else:
        op = EQ
    return name, op, value

def filterQuery(query, properties, nullableProperties):
    for name, opvalue in properties.items():
        op, value = opvalue
        dsetattr = getattr(Dataset, name)
        if op==EQ:
            query = query.filter(dsetattr == value)
        elif op==LIKE:
            if name != 'id' and name not in nullableProperties:
                query = query.filter(dsetattr.like(value))
            elif name in nullableProperties:
                if value=='%':
                    query = query.filter(or_(dsetattr==None, dsetattr.like(value)))
                else:
                    query = query.filter(dsetattr.like(value))
            else:
                raise Exception("Only test for equality of ids")
            
    return query

def getAttributes(dset, attHeaders):
    result = []
    for attname in attHeaders:
        attr = dset.attributes.get(attname, None)
        if attr is not None:
            value = attr.value
        else:
            value = None
        result.append(value)
    return result

def matchValue(queryValue, value):
    pat = queryValue.replace('%', '.*')
    # Note: '%' matches None. This is so that we can add new categories
    # for a project and still match records already added
    return ((value is not None) and (re.match(pat, value) is not None)) or (queryValue=='%' and value is None)

def filterProperties(values, properties, headers):
    match = True
    for attname, value in zip(headers, values):
        opvalue = properties.get(attname, None)
        if opvalue is None:
            continue                    # If property not explicitly specified, then it matches
        else:
            op, queryValue = opvalue
        if op==EQ and queryValue!=value:
            match = False
            break
        elif op==LIKE and not matchValue(queryValue, value):
            match = False
            break

    return match
        
def getEvents(dset, dsetVersion, eventHeaders, latestEvents):
    result = []
    latestEvent = latestEvents[dsetVersion.version]
    for attname in eventHeaders:
        if attname=='publish_time':
            
            value = latestEvent.datetime.strftime("%Y-%m-%d %H:%M:%S")
        elif attname=='publish_status':
            value = eventName[latestEvent.event]
        else:
            raise Exception("Unknown event attribute: %s"%attname)
        result.append(value)
    return result

def getDerived(dset, dsetVersion, derivedHeaders, handler):
    result = []
    for attname in derivedHeaders:
        if attname=='version':
            value = str(dsetVersion.version)
        elif attname=='parent':
            dsetname = dset.name
            try:
                value  = handler.getParentId(dsetname)
            except:
                warning("Cannot determine parent id for dataset %s"%dsetname)
                value = ''
        elif attname=='version_name':
            value = dsetVersion.name
        elif attname=='comment':
            value = dsetVersion.comment
        result.append(value)
    return result

def setEvent(event, attname, value):
        if attname=='publish_time':
            st = time.strptime(value, "%Y-%m-%d %H:%M:%S")
            event.datetime = apply(datetime.datetime, st[0:6])
        elif attname=='publish_status':
            try:
                event.event = eventNumber[value]
            except:
                validStatus = eventNumber.keys()
                raise ESGQueryError("Invalid publish status: %s, must be one of %s"%(value, `validStatus`))
        else:
            raise Exception("Unknown event attribute: %s"%attname)

def getQueryFields(handler, return_list=True):
    """
    Get a list of query fields.

    handler
      The project handler.

    return_list:
      Boolean flag:

      - True: Return a list of all query fields.
      - False: Return a tuple (*basicFields*, *eventFields*, *categories*) where:
      
        * *basicFields* apply to all datasets;
        * *eventFields* are events associated with the dataset;
        * *categories* are the handler-specific categories.
        * *derivedFields* are fields such as *parent*, derived from other objects.

    listall:
      Boolean, if True include DatasetVersion headers
    """
    
    basicHeaders = ['id', 'name', 'project', 'model', 'experiment', 'run_name', 'offline', 'master_gateway']
    eventHeaders = ['publish_time', 'publish_status']
    derivedHeaders = ['parent', 'version', 'version_name', 'comment']
    categories = handler.getFieldNames()
    if return_list:
        allProperties = list(set(basicHeaders+categories+eventHeaders+derivedHeaders))
        allProperties.sort()
        return allProperties
    else:
        return (basicHeaders, eventHeaders, categories, derivedHeaders)

def getNullableFields():
    """
    Get a list of fields that can have a NULL value in the database. Wildcard queries on these fields
    will compare against None rather than a blank string.
    """
    result = ['master_gateway']
    return result

def queryDatasets(projectName, handler, Session, properties, select=None, listall=False):
    """Issue a query on datasets.

    Returns a tuple (*result*, *headers*), where *result* is a list of tuples and *header* is the list of properties.
    Each tuple in the result corresponds to the respective field in the header.

    projectName
      String project name.

    handler
      The project handler.

    Session
      Dataset Session, as returned from sessionmaker.

    properties
      A dictionary: property => (op, value), where ``op`` is the
      comparison operation (see ``parseQuery``) and ``value`` is the
      value of the property. Only datasets having the property which
      matches the value are returned.

    select:
      String of the form 'field,field,...'. Only return the indicated fields

    listall:
      Boolean, if True list all versions of the dataset.

    """

    basicHeaders, eventHeaders, categories, derivedHeaders = getQueryFields(handler, return_list=False)
    attHeaders = []
    for category in categories:
        if category not in basicHeaders+eventHeaders and handler.isMandatory(category):
            attHeaders.append(category)
    for key, value in properties.items():
        if key not in basicHeaders+eventHeaders+attHeaders+derivedHeaders:
            attHeaders.append(key)
    headers = basicHeaders+attHeaders+eventHeaders+derivedHeaders
    if select is not None:
        selectHeaders = [item.strip() for item in select.split(',')]
        for field in selectHeaders:
            if field not in headers:
                raise ESGQueryError("Invalid field: %s"%field)
        headerdict = dict(zip(headers, range(len(headers))))

    # Assemble properties
    basicProperties = {}
    eventProperties = {}
    attProperties = {}
    derivedProperties = {}
    for key, value in properties.items():
        if key in basicHeaders:
            if key=='offline':
                testvalue = value[1]
                if testvalue not in ['t','f','True','False','%']:
                    raise ESGQueryError("offline value should be one of: 't','f','True','False','%%'; was %s"%`testvalue`)
                elif testvalue!='%':
                    basicProperties[key] = value
            else:
                basicProperties[key] = value
        elif key in eventHeaders:
            eventProperties[key] = value
        elif key in derivedHeaders:
            derivedProperties[key] = value
        else:
            attProperties[key] = value

    session = Session()

    # Issue query on dataset / dataet_versions, filtered by basic properties
    nullableProperties = getNullableFields()
    if listall:
        query = session.query(Dataset, DatasetVersion).filter(Dataset.id==DatasetVersion.dataset_id).filter(Dataset.project==projectName)
        query = filterQuery(query, basicProperties, nullableProperties)
        result = query.order_by(Dataset.name, DatasetVersion.version).all()
    else:
        query = session.query(Dataset).filter_by(project=projectName)
        query = filterQuery(query, basicProperties, nullableProperties)
        result1 = query.order_by(Dataset.name).all()
        result = [(item, item.getLatestVersion()) for item in result1]

    # Filter results by attribute and event properties
    tupleResult = []
    prevDset = None
    for dset, dsetVersion in result:

        attResult = getAttributes(dset, attHeaders)
        if not filterProperties(attResult, attProperties, attHeaders):
            continue

        if dset is not prevDset:
            latestEvents = {}           # version_number => latest event
            for event in dset.events[::-1]:
                if not latestEvents.has_key(event.object_version):
                    latestEvents[event.object_version] = event
        eventResult = getEvents(dset, dsetVersion, eventHeaders, latestEvents)
        if not filterProperties(eventResult, eventProperties, eventHeaders):
            continue

        derivedResult = getDerived(dset, dsetVersion, derivedHeaders, handler)
        if not filterProperties(derivedResult, derivedProperties, derivedHeaders):
            continue

        entry = [`dset.id`, dset.name, dset.project, dset.model, dset.experiment, dset.run_name, `dset.offline`, dset.master_gateway]+attResult+eventResult+derivedResult
        if select is None:
            tupleResult.append(tuple(entry))
        else:
            tupleResult.append(tuple([entry[headerdict[item]] for item in selectHeaders]))

    session.close()

    if select is not None:
        headers = selectHeaders

    return tupleResult, headers

def updateDatasetFromContext(context, datasetName, Session):
    """

    Update a persistent dataset with values from context (name/value dictionary). The context may have
    fields such as event fields, not associated with the project handler.

    context
      A property (name/value) dictionary.

    datasetName
      String dataset identifier.

    Session
      Database session factory.

    """

    dset = Dataset.lookup(datasetName, Session)
    if dset is None:
        raise ESGQueryError("Dataset not found: %s"%datasetName)
    projectName = dset.get_project(Session)
    handler = getHandlerByName(projectName, None, Session)
    basicHeaders, eventHeaders, categories, derivedHeaders = getQueryFields(handler, return_list=False)
    properties = context.copy()

    # Set basic and event properties
    session = Session()
    session.add(dset)
    for key,value in properties.items():
        if key in basicHeaders:
            if key!='id':
                if key=='name':
                    if len(handler.parseDatasetName(value, {}))==0:
                        warning("Dataset name: %s does not match dataset_id pattern in config file."%value)
                setattr(dset, key, value)
            else:
                warning("Cannot update id field")
            del properties[key]
        elif key in eventHeaders:
            event = dset.events[-1]
            setEvent(event, key, value)
            del properties[key]

    # Set attribute headers
    handler.setContext(properties)
    handler.saveContext(datasetName, Session)
    
    session.commit()
    session.close()

def queryDatasetMap(datasetNames, Session, extra_fields=False):
    """Query the database for a dataset map.

    datasetNames is a list of (datasetName, version) tuples.

    Returns (dataset_map, offline_map) where dataset_map is a dictionary:

       (dataset_id, version) => [(path, size), (path, size), ...]

    and offline_map is a dictionary:

       dataset_id => True | False, where True iff the corresponding dataset is offline.

    If extra_fields = True. returns (dataset_map, offline_map, extraFields) where 
    
      extrafields[(dataset_id, absolute_file_path, *field_name*)] => field_value

      where *field_name* is one of:

      - ``mod_time``

    """

    dmap = {}
    offlineMap = {}
    extraFields = {}
    for versionId in datasetNames:
        name,useVersion = parseDatasetVersionId(versionId)
        dset = Dataset.lookup(name, Session)
        session = Session()
        if dset is None:
            raise ESGQueryError("Dataset not found: %s"%name)
        session.add(dset)
        if useVersion==-1:
            useVersion = dset.getVersion()

        versionObj = dset.getVersionObj(useVersion)
        if versionObj is None:
            raise ESGPublishError("Version %d of dataset %s not found, cannot republish."%(useVersion, dset.name))
        filelist = versionObj.getFiles() # file versions
        dmap[(name,useVersion)] = [(file.getLocation(), `file.getSize()`) for file in filelist]

        if extra_fields:
            for file in filelist:
                modtime = file.getModtime()
                location = file.getLocation()
                if modtime is not None:
                    extraFields[(name, useVersion, location, 'mod_time')] = modtime
                checksum = file.getChecksum()
                if checksum is not None:
                    extraFields[(name, useVersion, location, 'checksum')] = checksum
                    extraFields[(name, useVersion, location, 'checksum_type')] = file.getChecksumType()
                    
        offlineMap[name] = dset.offline
        session.close()

    if extra_fields:
        return (dmap, offlineMap, extraFields)
    else:
        return (dmap, offlineMap)
