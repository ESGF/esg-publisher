"Handle IPCC5 data file metadata"

import os
import re

from cmip5_product import getProduct

from esgcet.exceptions import *
from esgcet.config import BasicHandler, getConfig, compareLibVersions
from esgcet.messaging import debug, info, warning, error, critical, exception

import numpy

from cmip6_cv.CMIP6Validator import JSONAction, CDMSAction, checkCMIP6
import argparse


WARN = False

from cfchecker import *


class CMIP6Handler(BasicHandler):

    def __init__(self, name, path, Session, validate=True, offline=False):

        BasicHandler.__init__(self, name, path, Session, validate=validate, offline=offline)


    def openPath(self, path):
        """Open a sample path, returning a project-specific file object,
        (e.g., a netCDF file object or vanilla file object)."""
        fileobj = BasicHandler.openPath(self, path)
        fileobj.path = path
        return fileobj


    def validateFile(self, fileobj):
        """Raise ESGInvalidMetadataFormat if the file cannot be processed by this handler."""
        
        f = fileobj.path

        config = getConfig()
        projectSection = 'project:'+self.name

        
        min_cmor_version = config.get(projectSection, "min_cmor_version", default="0.0.0")

        file_cmor_version = fileobj.getAttribute('cmor_version', None)
        
        if compareLibVersions(min_cmor_version, file_cmor_version):
            debug('File %s cmor-ized at version %s, passed!"'%(f, file_cmor_version))
            return


        min_cf_version = config.get(projectSection, "min_cf_version", defaut="")        



        if len(min_cf_version) == 0: 
            raise ESGPublishError("Minimum CF version not set in esg.ini")

        fakeversion = ["cfchecker.py", "-v", "1.0", "foo"]
        
        (badc,coards,uploader,useFileName,standardName,areaTypes,udunitsDat,version,files)=getargs(fakeversion)


        CF_Chk_obj = CFChecker(uploader=uploader, useFileName=useFileName, badc=badc, coards=coards, cfStandardNamesXML=standardName, cfAreaTypesXML=areaTypes, udunitsDat=udunitsDat, version=version)

        rc = CF_Chk_obj.checker(f)

        if (rc > 0):
            raise ESGPublishError("File %s fails CF check"%f)


        table = None

        try:
            table = fileobj.getAttribute('table_id', None)

        except:
            raise ESGPublishError("File %s missing required table_id global attribute"%f)


        cmor_table_path = config.get(projectSection, "cmor_table_path", defaut="")        
        

        if cmor_table_path == "":
            raise ESGPublishError("cmor_table_path not set in esg.ini")            

        table_file = cmor_table_path + '/CMIP6_' + table + '.json'


        fakeargs = [ table_file ,f]

        parser = argparse.ArgumentParser(prog='esgpublisher')
        parser.add_argument('cmip6_table', action=JSONAction)
        parser.add_argument('infile', action=CDMSAction)

        args = parser.parse_args(fakeargs)


#        print "About to CV check:", f
 
        try:
            process = checkCMIP6(args)
            if process is None:
                raise ESGPublishError("File %s failed the CV check - object create failure"%f)

            process.ControlVocab()


        except:

            raise ESGPublishError("File %s failed the CV check"%f)

