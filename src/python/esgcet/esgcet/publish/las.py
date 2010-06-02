import os
import numpy
import cdms2
import cdtime
import urlparse
import string
from lxml import etree
from lxml.etree import Element, ElementTree, SubElement as SE, tostring, Comment, Entity
from thredds import normTime, SEQ, readThreddsWithAuthentication
from utility import isRegular, whereIrregular
from esgcet.config import splitLine, splitRecord, getConfig
from esgcet.model import *
from esgcet.exceptions import *
from sqlalchemy.orm import join
from esgcet.messaging import debug, info, warning, error, critical, exception

LASCalendarMap = {
    cdtime.Calendar360 : '360_DAY',
    cdtime.GregorianCalendar : 'GREGORIAN',
    cdtime.NoLeapCalendar : 'NOLEAP',
    cdtime.MixedCalendar : 'GREGORIAN',
    }

def getCanonicalUnits(first_vector, time_unit, calendar):
    """
    For time_unit = "month", maps 'days since x-y-z' to 'months since x-y-z';
    For time_unit = "year", maps 'days since x-y-z' to 'years since x-y-z';
    Otherwise, returns the units of the first_vector
    """
    if time_unit in ["month", "year"]:
        t0 = cdtime.reltime(first_vector[0], first_vector.units)
        c0 = t0.tocomp(calendar)
        if time_unit=="month":
            canonical_units = "months since %s-%s"%(c0.year, c0.month)
        else:
            canonical_units = "years since %s"%(c0.year)
    else:
        canonical_units = first_vector.units
    return canonical_units

def mapVectors(vectorList, canonical_units, calendar):
    """
    Map a list of vectors to another list with the canonical units.
    """
    result = []
    for vec in vectorList:
        rellist = vec.asRelativeTime()
        mappedList = []
        for r in rellist:
            mappedList.append(r.torel(canonical_units, calendar).value)
        result.append(mappedList)
    return result

def offsetVectors(vectorList, canonical_units, calendar):
    """
    Map a list of vectors to another list with the canonical units,
    by adding a constant offset.
    """
    result = [vectorList[0]]
    for vec in vectorList[1:]:
        if vec.units==canonical_units:
            result.append(vec[:])
        else:
            t0 = cdtime.reltime(vec[0], vec.units)
            offset = t0.torel(canonical_units, calendar).value
            mappedVec = vec[:] + offset - vec[0]
            result.append(mappedVec)
    return result

def getCanonicalVector(vectorList, time_unit):
    """
    Translate a list of time vectors using canonical units. This allows
    interpretation of monthly and yearly data as regularly spaced even if
    the units are "days since x-y-z".
    """
    calendar = vectorList[0].getCalendar()
    canonical_units = getCanonicalUnits(vectorList[0], time_unit, calendar)
    if time_unit in ["month", "year"]:
        result = mapVectors(vectorList, canonical_units, calendar)
    else:
        result = offsetVectors(vectorList, canonical_units, calendar)
    
    return result, canonical_units, calendar

_REG = 1
_IRREG = 2
_AGG = 3
def _getLASAxis(axis, aggID, agg_dim_name):
    """
    Returns (_REG, axisID, start, size, step, axisType, axis.units) for regular spacing,
            (_IRREG, axisID, values, axisType, axis.units) for irreg)
            (_AGG, axisID, axisType, axis.units) for the aggregate dimension
    """
    if axis.isLongitude():
        axisType = "x"
        axisName = "lon"
    elif axis.isLatitude():
        axisType = "y"
        axisName = "lat"
    elif axis.isLevel():
        axisType = "z"
        axisName = "lev"
    elif axis.isTime():
        axisType = "t"
        axisName = "time"
    axisID = "%s-%s-%s"%(axisName, axisType, aggID)
    if axis.id!=agg_dim_name:
        axisValues = axis[:]
    if axis.id==agg_dim_name:
        result = (_AGG, axisID, axisType, axis.units)
    elif len(axisValues)>1 and isRegular(axisValues):
        regaxis = _REG
        start = axisValues[0]
        size = len(axisValues)
        step = axisValues[1] - axisValues[0]
        result = (regaxis, axisID, start, size, step, axisType, axis.units)
    else:
        regaxis = _IRREG
        values = axisValues
        result = (regaxis, axisID, values, axisType, axis.units)
    return result

def _getLASGrid(f, variable, aggID, agg_dim_name):
    """
    Returns [gridID, axisTuple, axisTuple, ...], iaggregate (-1 if no aggregate dimension)
    """
    gridID = "grid-%s"%aggID
    lasgrid = [gridID]
    v = f[variable.short_name]
    axes = v.getAxisList()
    i = 1
    iagg = -1                            # Index of the aggregation dimension
    for axis in axes:
        if len(axis.shape)>1:
            warning("Variable %s in dataset %s has a non-rectilinear grid, skipping"%(variable.short_name, aggID))
            return None
        lasaxis = _getLASAxis(axis, aggID, agg_dim_name)
        lasgrid.append(lasaxis)
        if lasaxis[0]==_AGG:
            iagg = i
        i += 1
    return lasgrid, iagg

def _genLASDatasets(datasetElement, gridsElement, axesElement, dsetCategoryElement, dataset, datasetName, excludeVariables, aggServiceSpecs, threddsBase, canonicalTimeUnit=None):
    aggdim_name = dataset.aggdim_name
    lasgrids = []
    calendarMap = {}
    for variable in dataset.variables:
        if variable.short_name in excludeVariables:
            continue
        variableID = "%s.%s"%(datasetName, variable.short_name)
        if variable.has_errors or dataset.aggdim_units is None:
            continue
        aggID = "%s.aggregation"%variableID
        serviceType, serviceBase, name = aggServiceSpecs
        print "agg_id = %s, serviceBase = %s"%(aggID, serviceBase)

        # Sort filevars according to aggdim_first normalized to the dataset basetime
        filevars = []
        has_null_aggdim = False
        for filevar in variable.file_variables:
            if filevar.aggdim_first is None:
                has_null_aggdim = True
                break
            filevars.append((filevar, normTime(filevar, dataset.aggdim_units)))
        if has_null_aggdim:
            continue
        filevars.sort(lambda x,y: cmp(x[1], y[1]))
        
        nvars = 0
        aggvalues = []
        index = 0
        for filevar, aggdim_first in filevars:
            fvdomain = map(lambda x: (x.name, x.length, x.seq), filevar.dimensions)
            fvdomain.sort(lambda x,y: cmp(x[SEQ], y[SEQ]))
            if len(fvdomain)>0 and fvdomain[0][0]==aggdim_name:
                ncoords = fvdomain[0][1]
                info("%s %d %s"%(filevar.file.path, ncoords, "indices=%d:%d"%(index, index+ncoords-1)))
                index += ncoords
                f = cdms2.open(filevar.file.path)
                aggvar = f[aggdim_name].clone()
                if nvars==0:
                    grid, iagg = _getLASGrid(f, variable, aggID, aggdim_name)
                    if grid is None:    # Non-rectilinear grid?
                        nvars = 0
                        break
                    lasgrids.append(grid)
                f.close()
                aggvalues.append(aggvar)
                nvars += 1

        # Create the aggregation if at least one filevar has the aggregate dimension
        # and the aggregate dimension is regularly spaced.
        if nvars>0:
            canonicalVector, canonicalUnits, calendar = getCanonicalVector(aggvalues, canonicalTimeUnit)
            lasCalendar = LASCalendarMap.get(calendar, None)
            fields = canonicalUnits.split(" ")
            if fields[0] in ["day", "days"]:
                lasUnits = "day"
            elif fields[0] in ["hour", "hours"]:
                lasUnits = "hour"
            else:
                lasUnits = canonicalTimeUnit
            aggvector = numpy.concatenate(canonicalVector)
            aggelem = SE(datasetElement, aggID, name=aggID)
            variables = SE(aggelem, "variables")
            varid = "%s-%s"%(variable.short_name, aggID)
            varurl = "%s%s%s#%s"%(threddsBase, serviceBase, aggID, variable.short_name)
            varelem = SE(variables, varid, name=variable.long_name, units=variable.units, url=varurl)
            gridlink = SE(varelem, "link", match="/lasdata/grids/%s"%grid[0])
            varCategoryElement = SE(dsetCategoryElement, "category", name=variableID)
            aggCategoryElement = SE(varCategoryElement, "category", name=aggID)
            filterElement = SE(aggCategoryElement, "filter", action="apply-dataset")
            filterElement.set("contains-tag", aggID)
            if isRegular(aggvector) and len(aggvector)>1:
                if iagg>0:
                    agg_axis_tuple = grid[iagg]
                    aggAxisID = agg_axis_tuple[1]
                    aggAxisType = agg_axis_tuple[-2]
                    aggAxisUnits = agg_axis_tuple[-1]
                    start = `cdtime.reltime(aggvector[0], canonicalUnits).tocomp(calendar)`
                    size = len(aggvector)
                    step = aggvector[1] - aggvector[0]
                    grid[iagg] = (_REG, aggAxisID, start, size, step, aggAxisType, lasUnits)
                    if aggAxisType=="t" and lasCalendar is not None:
                        calendarMap[aggAxisID] = lasCalendar
            else:
                inds = whereIrregular(aggvector)
                info("Aggregate vector %s for %s is not regularly spaced."%(aggdim_name, variable.short_name))
                if iagg>0:
                    agg_axis_tuple = grid[iagg]
                    aggAxisID = agg_axis_tuple[1]
                    aggAxisType = agg_axis_tuple[-2]
                    aggAxisUnits = agg_axis_tuple[-1]
                    if aggAxisType=="t":
                        axis = cdms2.createAxis(aggvector)
                        axis.units = canonicalUnits
                        axis.setCalendar(calendar)
                        newvector = axis.asComponentTime(calendar)
                    else:
                        newvector = aggvector
                    grid[iagg] = (_IRREG, aggAxisID, newvector, aggAxisType, aggAxisUnits)
                    info("  near indices: %s, values:%s"%(`list(inds[0:10])`, `[newvector[ind] for ind in inds[0:10]]`))
                    if aggAxisType=="t" and lasCalendar is not None:
                        calendarMap[aggAxisID] = lasCalendar
                else:
                    info("  near indices: %s, values:%s"%(`list(inds[0:10])`, `aggvector[inds][0:10]`))

    for grid in lasgrids:
        gridID = grid[0]
        gridElement = SE(gridsElement, gridID)
        for axis in grid[:0:-1]:
            axislink = SE(gridElement, "link", match="/lasdata/axes/%s"%axis[1])

    for grid in lasgrids:
        for axis in grid[:0:-1]:
            axisID = axis[1]
            axisType = axis[-2]
            axisUnits = axis[-1]
            axisElem = SE(axesElement, axisID, type=axisType, units=axisUnits)
            if calendarMap.has_key(axisID):
                axisElem.set("calendar", calendarMap[axisID])
            if axis[0]==_REG:
                start, size, step = axis[2:5]
                SE(axisElem, "arange", start="%s"%start, size="%d"%size, step="%f"%step)
            elif axis[0]==_IRREG:
                values = axis[2]
                for value in values:
                    valueElem = SE(axisElem, "v")
                    valueElem.text = "%s"%value

def generateLAS(datasetName, dbSession, outputFile, handler, datasetInstance=None, canonicalTimeUnit=None):

    session = dbSession()

    # Lookup the dataset
    if datasetInstance is None:
        dset = session.query(Dataset).filter_by(name=datasetName).first()
    else:
        dset = datasetInstance
        # session.save_or_update(dset)
        session.add(dset)
    if dset is None:
        raise ESGPublishError("Dataset not found: %s"%datasetName)
    offline = dset.offline

    # Lookup the related objects
    project = session.query(Project).filter_by(name=dset.project).first()
    model = session.query(Model).filter_by(name=dset.model, project=dset.project).first()
    experiment = session.query(Experiment).filter_by(name=dset.experiment, project=dset.project).first()

    # Update the handler from the database. This ensures that the handler context is in sync
    # with the dataset.
    context = handler.getContextFromDataset(dset)
    datasetDesc = handler.generateNameFromContext('dataset_name_format', project_description=project.description, model_description=model.description, experiment_description = experiment.description)

    # Get configuration options
    config = getConfig()
    if config is None:
        raise ESGPublishError("No configuration file found.")
    section = 'project:%s'%dset.project
    threddsAggregationOption = config.get(section, 'thredds_aggregation_services')
    threddsAggregationSpecs = splitRecord(threddsAggregationOption)
    threddsURL = config.get(section, 'thredds_url')
    scheme, netloc, thredds_path, thredds_parameters, thredds_query, thredds_fragments = urlparse.urlparse(threddsURL)
    threddsBase = urlparse.urlunparse((scheme, netloc, '', '', '', ''))
    excludeVariables = splitLine(config.get(section, 'thredds_exclude_variables', ''), sep=',')
    if not offline:
        perVariable = config.getboolean(section, 'variable_per_file', False)
    else:
        perVariable = False

    if perVariable:
        # Per-variable datasets
        datasets = Element("datasets")
        grids = Element("grids")
        axes = Element("axes")
        lasCategories = Element("las_categories")
        dsetCategory = SE(lasCategories, "category", name=datasetDesc)

        # Get the LAS canonical time unit from the configuration las_time_unit_map if defined
        if canonicalTimeUnit is None:
            canonicalTimeUnit = handler.getFieldFromMaps("las_time_unit", context)

        _genLASDatasets(datasets, grids, axes, dsetCategory, dset, datasetName, excludeVariables, threddsAggregationSpecs[0], threddsBase, canonicalTimeUnit=canonicalTimeUnit)
        info("Writing LAS catalog %s"%outputFile.name)
        print >>outputFile, tostring(datasets, pretty_print=True),
        print >>outputFile, tostring(grids, pretty_print=True),
        print >>outputFile, tostring(axes, pretty_print=True),
        print >>outputFile, tostring(lasCategories, pretty_print=True),

        event = Event(dset.name, dset.getVersion(), WRITE_LAS_CATALOG_EVENT)
        dset.events.append(event)

    session.commit()
    session.close()
    
def generateLASOutputPath(datasetName, dbSession, handler, createDirectory=True):

    # Get the root and basename.
    config = getConfig()
    if config is None:
        raise ESGPublishError("No configuration file found.")

    session = dbSession()

    lasRoot = config.get('DEFAULT', 'las_root')
    lasAggRoot = config.get('DEFAULT', 'las_aggregate_root')
    project_name = handler.name
    filename = "%s.xml"%datasetName
    direc = os.path.join(lasRoot, lasAggRoot, project_name)

    # Create the subdirectory if necessary
    if createDirectory and not os.path.exists(direc):
        os.mkdir(direc, 0775)

    path = os.path.join(direc, filename)

    # Build the catalog name
    location = os.path.join(lasAggRoot, project_name, filename)

    # Add the database catalog entry
    catalog = session.query(LASCatalog).filter_by(dataset_name=datasetName).first()
    if catalog is None:
        catalog = LASCatalog(datasetName, location)
        session.add(catalog)

    session.commit()
    session.close()
    
    return path
    
# IMPORTANT! There cannot be an initial carriage return in the output, otherwise the LAS reinit will fail with "no root element"
_las_header = """<?xml version='1.0' ?>
<!DOCTYPE spec SYSTEM "spec.dtd" [

<!-- Declaration of operations files to be included -->
<!ENTITY operations SYSTEM "operations.xml">

<!ENTITY insitu_operations SYSTEM "insitu_operations.xml">

<!-- Declaration of dataset files to be included -->
<!ENTITY fromtds SYSTEM "fromtds.xml">
%s
]>
"""
_las_properties = etree.fromstring(""" <!-- Default properties for this server -->
 <properties>

  <product_server>
   <ui_timeout>20</ui_timeout>
   <ps_timeout>3600</ps_timeout>
   <use_cache>true</use_cache>
  </product_server>

  <ferret>
   <land_type>contour</land_type>
   <fill_type>fill</fill_type>
  </ferret>

 </properties>
""")

def updateLASMasterCatalog(dbSession):
    """Rewrite the LAS master catalog.
    """

    # Get the catalog path
    config = getConfig()
    if config is None:
        raise ESGPublishError("No configuration file found.")
    lasRoot = config.get('DEFAULT', 'las_root')
    lasMasterCatalogName = config.get('DEFAULT', 'las_master_catalog_name')

    session = dbSession()
    lasCatalogs = session.query(LASCatalog).select_from(join(LASCatalog, Dataset, LASCatalog.dataset_name==Dataset.name)).all()
    entities = ['<!ENTITY %s SYSTEM "%s">\n'%(catalog.dataset_name, catalog.location) for catalog in lasCatalogs]

    header = _las_header%string.join(entities,'')
    lasdata = Element("lasdata")
    output_dir = SE(lasdata, "output_dir")
    output_dir.text = "/usr/local/tomcat/webapps/las/output"
    institution = SE(lasdata, "institution", name="ESGCET", contact="Roland.Schweitzer@noaa.gov", url="http://earthsystemgrid.org")
    lasdata.append(_las_properties)
    operations = SE(lasdata, "operations", url="http://pcmdi3.llnl.gov:80/las/ProductServer.do")
    operations.append(Entity('operations'))
    operations.append(Entity('insitu_operations'))

    for catalog in lasCatalogs:
        ent = Entity(catalog.dataset_name)
        lasdata.append(ent)

    master = os.path.join(lasRoot, lasMasterCatalogName)
    info("Writing LAS master catalog %s"%master)
    f = open(master, 'w')
    print >>f, header
    print >>f, etree.tostring(lasdata, pretty_print=True)
    f.close()

    session.commit()
    session.close()

def reinitializeLAS():
    """
    Reinitialize the Live Access Server. This forces the catalogs to be reread.

    Returns the HTML string returned from the URL.

    """
    config = getConfig()
    if config is None:
        raise ESGPublishError("No configuration file found.")

    lasReinitUrl = config.get('DEFAULT', 'las_reinit_url')
    info("Reinitializing LAS server")

    try:
        reinitResult = readThreddsWithAuthentication(lasReinitUrl, config)
    except Exception, e:
        raise ESGPublishError("Error reinitializing the Live Access Server: %s"%e)
        
    return reinitResult
