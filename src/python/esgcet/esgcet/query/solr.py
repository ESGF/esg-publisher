# Support for SOLR queries

import sys
import string
import re

from lxml import etree
from lxml.etree import XMLSyntaxError
from urllib2 import urlopen, HTTPError
from urlparse import urlsplit

DEFAULT_CHUNKSIZE = 1000
DATASET = 1
FILE = 2
MODEL = 3
AGGREGATION = 4

typeCode = {'d': DATASET,
            'f': FILE,
            'm': MODEL,
            'a': AGGREGATION,
            }
typeName = {DATASET:'Dataset',
            FILE:'File',
            MODEL:'Model',
            AGGREGATION:'Aggregation',
            }

class DataStore(object):

    def isCached(self, tracking_id, size):
        pass

    def setArchived(self, tracking_id, path):
        pass

    def updateUtdFiles(self, datasetFiles, dataset_id, currentTrackingId, path):
        pass

    def deprecateFile(tracking_id, data_node, size, path):
        pass

    def dump(self):
        pass

    def close(self):
        pass

class DictionaryDataStore(DataStore):

    # tracking_id => [esg_id, dataset_id, data_node, size, archived, path, checksum]
    ESG_ID = 0
    DATASET_ID = 1
    DATA_NODE = 2
    SIZE = 3
    ARCHIVED = 4
    PATH = 5
    CHECKSUM = 6
    DEPR_PATH = 2

    def __init__(self):
        self.utdFiles = {}
        self.deprFiles = {}

    def isCached(self, tracking_id, size):
        result = False
        if tracking_id in self.utdFiles:
            result = (self.utdFiles[tracking_id][DictionaryDataStore.SIZE]==size)
        return result

    def setArchived(self, tracking_id):
        self.utdFiles[tracking_id][DictionaryDataStore.ARCHIVED] = True
        self.utdFiles[tracking_id][DictionaryDataStore.PATH] = True

    def updateUtdFiles(self, datasetFiles, dataset_id, currentTrackingId, path):
        """Update utdFiles, and set the current file as archived."""
        for file_id, checksum, size, trackingId in datasetFiles:
            if trackingId in self.utdFiles:
                print 'Warning: tracking_id %s already in cache'%trackingId
            esg_id, data_node = file_id.split('|')
            dset_id, data_node = dataset_id.split('|')
            archived = (currentTrackingId==trackingId)
            if not archived:
                path = None
            self.utdFiles[trackingId] = [esg_id, dset_id, data_node, long(size), archived, path, checksum]

    def deprecateFile(self, tracking_id, data_node, size, path):
        self.deprFiles[tracking_id] = [data_node, size, path]

    def dump(self):
        print 'Up-to-date Files:'

        i = 0
        for key, value in self.utdFiles.items():
            print i, value[DictionaryDataStore.ARCHIVED], value[DictionaryDataStore.ESG_ID]
            i+=1

        print 'Deprecated Files:'
        for key, value in self.deprFiles.items():
            print value[DictionaryDataStore.DEPR_PATH]

class ShelfDataStore(DictionaryDataStore):

    def __init__(self, dbname, deprName):
        import shelve
        self.utdFiles = shelve.open(dbname)
        self.deprFiles = shelve.open(deprName)

    def setArchived(self, tracking_id, path):
        temp = self.utdFiles[tracking_id]
        temp[DictionaryDataStore.ARCHIVED] = True
        temp[DictionaryDataStore.PATH] = path
        self.utdFiles[tracking_id] = temp

    def close(self):
        self.utdFiles.close()
        self.deprFiles.close()

class RDBDataStore(DataStore):

    def __init__(self, dburl, dbname=None):
        import psycopg2
        result = urlsplit(dburl)
        if dbname is None:
            dbname = result.path
        if dbname[0]=='/':
            dbname = dbname[1:]
        self.connection = psycopg2.connect(database=dbname, user=result.username, host=result.hostname, port=result.port)
        self.cursor = self.connection.cursor()

    def isCached(self, tracking_id, size):
        self.cursor.execute("SELECT tracking_id, size, path FROM esgf_replica.utd_files WHERE tracking_id=%s", (tracking_id,))
        queryResult = self.cursor.fetchone()
        if queryResult is not None:
            tid, siz, cachePath = queryResult
            result = (siz==size)
        else:
            result = False
            cachePath = None
        return result, cachePath

    def setArchived(self, tracking_id, path, modtime=None, scratch=False, batch=None):
        if scratch:
            archived = 'f'
            if batch is None:
                self.cursor.execute("UPDATE esgf_replica.utd_files SET archived=%s, path=%s, mod_time=%s, scratch=%s where tracking_id=%s", (archived, path, modtime, 't', tracking_id))
            else:
                self.cursor.execute("UPDATE esgf_replica.utd_files SET archived=%s, path=%s, mod_time=%s, scratch=%s, batch=%s where tracking_id=%s", (archived, path, modtime, 't', batch, tracking_id))
        else:
            archived = 't'
            if batch is None:
                self.cursor.execute("UPDATE esgf_replica.utd_files SET archived=%s, path=%s, mod_time=%s where tracking_id=%s", (archived, path, modtime, tracking_id))
            else:
                self.cursor.execute("UPDATE esgf_replica.utd_files SET archived=%s, path=%s, mod_time=%s, batch=%s where tracking_id=%s", (archived, path, modtime, batch, tracking_id))
        self.connection.commit()

    def updateUtdFiles(self, datasetFiles, dataset_id, currentTrackingId, currentPath, scratch=False):
        """Update table utd_files, and set the current file as archived."""

        dsetTrackingIds = {}            # Check tracking IDs in this dataset for duplicates
        result = False                  # Set True if the current tracking ID is found in the file list

        # First delete files in utd_files for this dataset
        dset_id, data_node = dataset_id.split('|')
        self.cursor.execute("DELETE FROM esgf_replica.utd_files WHERE dataset_id=%s", (dset_id,))

        for item in datasetFiles:
            badItem = False
            if len(item)==4:
                file_id, checksum, size, trackingId = item
            elif len(item)==3:
                file_id, size, trackingId = item
                checksum = None
                if len(trackingId)!=36:
                    badItem = True
            else:
                badItem = True
            if badItem:
                print 'Error: one of checksum, size, or tracking_id missing for file: %s'%`item`
                continue
            if trackingId in dsetTrackingIds:
                print 'Error: duplicate tracking ID %s in files %s, %s, skipping'%(trackingId, file_id, dsetTrackingIds[trackingId])
                continue
            dsetTrackingIds[trackingId] = file_id

            esg_id, data_node = file_id.split('|')

            if scratch:
                archived = 'f'
            else:
                archived = (currentTrackingId==trackingId)
            if not (currentTrackingId==trackingId):
                path = None             # Fill in path later in setArchived
            else:
                path = currentPath
                result = True
            try:
                self.cursor.execute("INSERT INTO esgf_replica.utd_files (tracking_id, esg_id, dataset_id, data_node, size, archived, path, checksum, scratch) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (trackingId, esg_id, dset_id, data_node, long(size), archived, path, checksum, scratch))
            except Exception as e:
                print 'Error inserting: %s'%`(trackingId, esg_id, dset_id, data_node, long(size), archived, path, checksum)`
                print '     %s'%e

        self.connection.commit()
        return result

    def deprecateFile(self, tracking_id, data_node, size, path):
        if path is not None:
            self.cursor.execute("DELETE FROM esgf_replica.depr_files WHERE path=%s", (path,))
            self.cursor.execute("INSERT INTO esgf_replica.depr_files VALUES (%s, %s, %s, %s)", (tracking_id, data_node, long(size), path))
        self.cursor.execute("DELETE from esgf_replica.utd_files WHERE tracking_id=%s", (tracking_id,))
        self.connection.commit()

    def deprecateFileSet(self, deprecatedFileSet, utdFileDict, data_node, dryrun):
        """Deprecate all files in deprecatedFileSet, having the form [(tracking_id, size), ...]
        Remove the records from utd_files. If the path is non-null, add the file to depr_files.
        utdFileDict maps the keys in deprecatedFileSet to (esg_id, dataset_id, data_node, path, checksum, archive, scratch).
        """
        for item in deprecatedFileSet:
            tracking_id, size = item
            esg_id, dataset_id, data_node, path, checksum, archive, scratch = utdFileDict[item]
            command1, arg1 = ("DELETE FROM esgf_replica.utd_files WHERE tracking_id=%s", (tracking_id,))
            if dryrun:
                print command1, `arg1`
            else:
                self.cursor.execute(command1, arg1)
            self.addDeprecatedFile(tracking_id, data_node, size, path, dryrun)

    def addFileSet(self, newFileSet, catalogFileDict, latestDatasetId, dryrun):
        """Add the files in newFileSet to utd_files.
        newFileSet is tuples (tracking_id, size). catalogFileDict maps the tuples to (esg_id, data_node, checksum).
        Set paths to null.
        """

        dset_id, data_node = latestDatasetId.split('|')
        for item in newFileSet:
            tracking_id, size = item
            esg_id, data_node, checksum = catalogFileDict[item]
            command, arg = ("INSERT INTO esgf_replica.utd_files (tracking_id, esg_id, dataset_id, data_node, size, archived, path, checksum, scratch) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (tracking_id, esg_id, dset_id, data_node, long(size), False, None, checksum, None))
            if dryrun:
                print command, `arg`
            else:
                try:
                    self.cursor.execute(command, arg)
                except Exception as e:
                    print 'Error inserting into utd_files: %s'%`arg`
                    print '     %s'%e

        if not dryrun:
            self.connection.commit()

    def getUtdFilesDict(self, masterId):
        """Get the utd files records corresponding to the master ID.
        Returns a dictionary mapping (tracking_id, size) => (esg_id, dataset_id, data_node, path, checksum, archive, scratch)
        """
        self.cursor.execute("SELECT tracking_id, size, esg_id, dataset_id, data_node, path, checksum, archived, scratch FROM esgf_replica.utd_files WHERE dataset_id like %s", (masterId+'%',))
        result = {}
        for item in self.cursor.fetchall():
            result[(item[0], str(item[1]))] = item[2:]
        return result

    def updateUtd(self, tracking_id, path, archive, scratch, dryrun):
        """Update the existing utd entry for tracking ID, with values for path, archive, and scratch.
        """
        command, arg = ("UPDATE esgf_replica.utd_files SET archived=%s, path=%s, scratch=%s where tracking_id=%s", (archive, path, scratch, tracking_id))
        if dryrun:
            print command, `arg`
        else:
            self.cursor.execute(command, arg)
            self.connection.commit()

    def addDeprecatedFile(self, tracking_id, data_node, size, path, dryrun):
        """Add an entry to depr_files.
        """
        print 'Deprecating %s'%path
        command2, arg2 = ("DELETE FROM esgf_replica.depr_files WHERE path=%s", (path,))
        command3, arg3 = ("INSERT INTO esgf_replica.depr_files VALUES (%s, %s, %s, %s)", (tracking_id, data_node, long(size), path))
        if dryrun:
            print command2, `arg2`
            print command3, `arg3`
        else:
            self.cursor.execute(command2, arg2)
            try:
                self.cursor.execute(command3, arg3)
            except Exception as e:
                print 'Error inserting: %s'%`arg3`
                print '     %s'%e
            self.connection.commit()

    def commit(self):
        self.connection.commit()

    def close(self):
        self.cursor.close()
        self.connection.close()

    def dump(self):
        i = 0
        self.cursor.execute("SELECT archived, esg_id FROM esgf_replica.utd_files")
        for archived, esg_id in self.cursor:
            print i, archived, esg_id
            i+=1

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

def printQueryResult(header, tuples, out=sys.stdout, printHeaders=True):
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

try:
    from esgcet.query import printResult
except:
    printResult = printQueryResult
    
# Formulate a SOLR query, returning the http query string.
#
# facets: list of (string,value) tuples
# fields: list of strings
# freetext: string arg to free text query, or None
# objtype: DATASET, FILE, or MODEL
# service: search service URL
# facetValues: list of strings
def formulateQuery(facets, fields, freetext, objtype, service, offset, limit, facetValues=None):
    queryList = ["type=%s"%typeName[objtype]]
    if facetValues is not None:
        facetString = string.join(facetValues,',')
        queryList.append("facets=%s"%facetString)
    if freetext is not None:
        queryList.append("query=%s"%freetext)
    if len(fields)>0:
        if 'id' not in fields:
            fields.append('id')
        fieldString = string.join(fields,',')
        queryList.append("fields=%s"%fieldString)
    if len(facets)>0:
        for field,value in facets:
            queryList.append("%s=%s"%(field,value))
    queryList.append("offset=%d"%offset)
    queryList.append("limit=%d"%limit)
    queryString = string.join(queryList,'&')
    query = "%s?%s"%(service,queryString)
    return query

def readChunk(service, query):
    try:
        tree = etree.parse(query)
    except IOError as xe:
        print xe
        try:
            u = urlopen(query)
        except HTTPError as he:
            errorHtml = he.read()
            m = re.search(r'message.*?<u>(.*?)</u>', errorHtml)
            if m is not None:
                print 'Error:', m.group(1)
            sys.exit(1)
    return tree

def downloadResult(query, outpath, outpathIsStdout):
    try:
        u = urlopen(query)
    except HTTPError as he:
        errorHtml = he.read()
        m = re.search(r'message.*?<u>(.*?)</u>', errorHtml)
        if m is not None:
            print 'Error:', m.group(1)
        sys.exit(1)
    result = u.read()
    outpath.write(result)
    u.close()
    if not outpathIsStdout:
        outpath.close()

# Parse the response header for available facet values
# Returns (([valueList],), header), numFound as for parseTrailer
def parseHeader(tree):
    root = tree.getroot()
    headerElem = root[0]
    for item in headerElem.iter('arr'):
        if item.get('name')=='facet.field':
            valueList = [(sub.text,) for sub in item]
            header = ['field']
            break
    else:
        raise RuntimeError("No facet.field list found")
    result = root[1]
    numFound = int(result.get('numFound'))
    return ([valueList], header), numFound

# Parse a SOLR XML response
# tree is an lxml ElementTree
# If includeId is true, the response records include (id,'id',id) where applicable.
# Returns (results, number_found, number_documents) where
# results is a list [(objid, field, value), (objid, field, value), ...], 
# number_found is the total number of results independent of chunk size,
# and number_documents is the number of results parsed by this call.
def parseResponse(tree, includeId, scoreInFields=False):
    root = tree.getroot()
    result = root[1]
    numFound = int(result.get('numFound'))
    start = int(result.get('start'))
    newResults = []
    numDocs = 0
    for doc in result:
        objid = ''
        interResults = []               # [(field, value), (field, value), ...]
        for elem in doc:
            name = elem.get('name')
            if not scoreInFields and name=='score':
                continue
            if name=='id':
                objid = elem.text
                if includeId:
                    interResults.append(('id', objid))
            elif elem.tag=='arr':
                for sub in elem:
                    if sub.tag=='str':
                        interResults.append((name, sub.text))
            else:
                interResults.append((name, elem.text))
        results = [(objid, field, value) for field, value in interResults]
        newResults.extend(results)
        numDocs += 1
    return newResults, numFound, numDocs

# Parse the trailer for facet values and counts.
# Returns ((valueLists, header), numFound where
#   valueLists = [list1, list2, ... listn]
#   listn is a list [(facetOption, facetCount), (facetOption, facetCount), ...]
#   header = [facetName1, facetName2, ...] of same length as valueLists
#   numFound is the total number of records that would be returned
def parseTrailer(tree, facetValues, includeId):
    root = tree.getroot()
    result = root[1]
    numFound = int(result.get('numFound'))
    numResults = 0                      # No actual data records returned
    valueLists = []
    header = []
    trailer = root[2]
    if trailer.get('name') != 'facet_counts':
        raise RuntimeError("Could not find facet counts in response")
    facetFields = trailer[1]
    if facetFields.get('name')!='facet_fields':
        raise RuntimeError("Could not find facet fields in response")
    for item in facetFields:
        field = item.get('name')
        subResults = [(sub.get('name'), sub.text) for sub in item]
        valueLists.append(subResults)
        header.append(item.get('name'))
    return (valueLists, header), numFound

# Print a list of results.
# results = [(id,field,value), (id,field,value), ...]
def outputResults(results, format, header=None, prettyPrint=False, printHeaders=True, delimiter=None, out=sys.stdout):
    if format=='narrow':
        if prettyPrint:
            header = ['id', 'field', 'value']
            printResult(header, results, printHeaders=printHeaders, out=out)
        else:
            if delimiter is not None:
                for item in results:
                    print >>out, delimiter.join(item)
            else:
                for item in results:
                    print >>out, item
    elif format=='wide':
        # valuedict: (id, field) => value
        objset = set()
        fieldset = set()
        valueDict = {}
        for objid,field,value in results:
            objset.add(objid)
            fieldset.add(field)
            valueDict[(objid, field)] = value

        objlist = list(objset)
        objlist.sort()
        if 'id' in fieldset:
            fieldset.remove('id')
        fieldlist = list(fieldset)
        fieldlist.sort()
        wideResults = []
        for obj in objlist:
            wideResults.append(tuple([obj]+[valueDict.get((obj,field), '') for field in fieldlist]))
        if prettyPrint:
            printResult(['id']+fieldlist, wideResults, printHeaders=printHeaders, out=out)
        else:
            if delimiter is not None:
                for item in wideResults:
                    print >>out, delimiter.join(item)
            else:
                for item in wideResults:
                    print >>out, item
    else:
        print 'Format not yet implemented:', format
        sys.exit(1)

# Print facet results.
# results = [(v1, ..., vn), (v1, ..., vn), ...]
# header = [f1, f2, ..., fn]
def outputFacetResults(results, header, prettyPrint=False, printHeaders=True, delimiter=None, out=sys.stdout):
    if prettyPrint:
        printResult(header, results, printHeaders=printHeaders, out=out)
    else:
        if delimiter is not None:
            for item in results:
                print delimiter.join(item)
        else:
            for item in results:
                print item

def querySolr(facets, fields, freetext, objtype, service, userLimit, facetValues, verbose, retries=0, retry_wait=3):
    """
    Query a SOLR index.

    facets: List of facets to query, with the form [(facet_name1, facet_value1), (facet_name2, facet_value2), ...]
    fields: Fields to be returned, a list of strings of the form [field1, field2, ...]
    freetext: String free text field to query
    objtype: objtype to return, either DATASET (default), FILE, or AGGREGATION
    service: SOLR service URL, for example "http://pcmdi9.llnl.gov/esg-search/search"
    userLimit: maximum number of records to return, an integer or long
    facetValues: facet names, to return facets that meet the query, or '*' to get a list of available facets.
                 A list of strings.
    verbose: If True, print the HTTP query. Default is False.
    retries: Integer number of times to retry if SOLR failed to return an answer
    retry_wait: Integer number of seconds to wait between retries
    """

    import time

    fullResults = []
    includeId = (fields==['id'])
    numFound = 0
    moredata = True
    nread = 0
    nleft = userLimit
    offset = 0
    chunksize = DEFAULT_CHUNKSIZE
    tries = max(retries+1, 1)

    # While remaining data:
    while moredata:

        # Formulate a query
        limit = min(nleft, chunksize)
        query = formulateQuery(facets, fields, freetext, objtype, service, offset, limit, facetValues=facetValues)
        if verbose:
            print >>sys.stderr, 'Query: ', query

        # Read a chunk
        for ntry in range(tries):
            try:
                chunk = readChunk(service, query)
            except XMLSyntaxError:
                print 'Error: Bad SOLR response, retrying'
                time.sleep(retry_wait)
            else:
                break

        # Parse the response. For facet value searches, parse the response trailer
        scoreInFields = ('score' in fields)
        results, numFound, numResults = parseResponse(chunk, includeId, scoreInFields)
        fullResults.extend(results)

        # More data if some results were found and the number of records read < total
        nread += numResults
        nleft -= limit
        moredata = (numResults>0) and (nread<min(numFound, userLimit))
        offset += limit

    return fullResults, nread

def transposeResults(results):
    """Transpose results of the form
    [(id1, field1, value1), (id1, field2, value2), ...]
    to
    [(id1, value1, value2, ...), (id2, value1, value2, ...), ...]
    """
    objset = set()
    fieldset = set()
    valueDict = {}
    for objid,field,value in results:
        objset.add(objid)
        fieldset.add(field)
        valueDict[(objid, field)] = value

    objlist = list(objset)
    objlist.sort()
    if 'id' in fieldset:
        fieldset.remove('id')
    fieldlist = list(fieldset)
    fieldlist.sort()
    wideResults = []
    for obj in objlist:
        wideResults.append(tuple([obj]+[valueDict.get((obj,field), '') for field in fieldlist]))
    return wideResults
    
