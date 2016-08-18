"Handle IPCC5 data file metadata"

import os
import re

from cmip5_product import getProduct

from esgcet.exceptions import *
from esgcet.config import BasicHandler, getConfig
from esgcet.messaging import debug, info, warning, error, critical, exception

import numpy


WARN = False

from cfchecker import *


class IPCC5Handler(BasicHandler):

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
        BasicHandler.validateFile(fileobj)

        f = fileobj.path

        config = getConfig()
        projectSection = 'project:'+self.name

        min_cf_version = config.get(projectSection, "min_cf_version", defaut="")        

        if len(min_cf_version) == 0: 
            raise ESGPublishError("Minimum CF version not set in esg.ini")

        fakeversion = ["cfchecker.py", "-v", "1.0", "foo"]
        
        (badc,coards,uploader,useFileName,standardName,areaTypes,udunitsDat,version,files)=getargs(fakeversion)


        CF_Chk_obj = CFChecker(uploader=uploader, useFileName=useFileName, badc=badc, coards=coards, cfStandardNamesXML=standardName, cfAreaTypesXML=areaTypes, udunitsDat=udunitsDat, version=version)

        rc = CF_Chk_obj.checker(f)

        if (rc < 0):
            raise ESGPublishError("File %s fails CF check"%f)

        
        table = self.context.get('cmor_table')

        fakeargs = [ table_file ,f]
