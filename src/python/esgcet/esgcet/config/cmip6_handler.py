""""Handle CMIP6 data file metadata"""

import os
import re
import sys

from cmip5_product import getProduct

from esgcet.exceptions import *
from esgcet.config import BasicHandler, getConfig, compareLibVersions, splitRecord
from esgcet.messaging import debug, info, warning, error, critical, exception
from esgcet.publish import checkAndUpdateRepo

from cmip6_cv import PrePARE as validator

import numpy
import argparse
import imp

WARN = False



#from cfchecker import getargs, CFChecker

#PrePARE_PATH = '/usr/local/conda/envs/esgf-pub/bin/PrePARE.py'

version_pattern = re.compile('20\d{2}[0,1]\d[0-3]\d')

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
        """
        for CMIP6, this will first verify if the data is written by CMOR at the correct version set in the ini file.
        If so, the file is declared valid. If not, file will go through PrePARE (CV) check.  PrePARE runs CFChecker

        Raises ESGPublishError if settings are missing or file fails the checks.
        Raise ESGInvalidMetadataFormat if the file cannot be processed by this handler.
        """
        
        f = fileobj.path

        config = getConfig()
        projectSection = 'project:'+self.name
        min_cmor_version = config.get(projectSection, "min_cmor_version", default="0.0.0")
        file_cmor_version = fileobj.getAttribute('cmor_version', None)
        
        if compareLibVersions(min_cmor_version, file_cmor_version):
            debug('File %s cmor-ized at version %s, passed!"'%(f, file_cmor_version))
            return

            #  PrePARE is going to handle the CF check now
        # min_cf_version = config.get(projectSection, "min_cf_version", defaut="")        

        # if len(min_cf_version) == 0: 
        #     raise ESGPublishError("Minimum CF version not set in esg.ini")

        # fakeversion = ["cfchecker.py", "-v", min_cf_version
        # , "foo"]        
        # (badc,coards,uploader,useFileName,standardName,areaTypes,udunitsDat,version,files)=getargs(fakeversion)
        # CF_Chk_obj = CFChecker(uploader=uploader, useFileName=useFileName, badc=badc, coards=coards, cfStandardNamesXML=standardName, cfAreaTypesXML=areaTypes, udunitsDat=udunitsDat, version=version)
        # rc = CF_Chk_obj.checker(f)

        # if (rc > 0):
        #     raise ESGPublishError("File %s fails CF check"%f)

        table = None

        try:
            table = fileobj.getAttribute('table_id', None)

        except:
            raise ESGPublishError("File %s missing required table_id global attribute"%f)

        try:
                variable_id = fileobj.getAttribute('variable_id', None)

        except:
            raise ESGPublishError("File %s missing required variable_id global attribute"%f)

        cmor_table_path = config.get(projectSection, "cmor_table_path", defaut="")        

        if cmor_table_path == "":
            raise ESGPublishError("cmor_table_path not set in esg.ini")            

        checkAndUpdateRepo(cmor_table_path)

        table_file = cmor_table_path + '/CMIP6_' + table + '.json'
        fakeargs = [ '--variable', variable_id, table_file ,f]
        parser = argparse.ArgumentParser(prog='esgpublisher')
        parser.add_argument('--variable')        
        parser.add_argument('cmip6_table', action=validator.JSONAction)
        parser.add_argument('infile', action=validator.CDMSAction)
        parser.add_argument('outfile',
                nargs='?',
                help='Output file (default stdout)',
                type=argparse.FileType('w'),
                default=sys.stdout)
        args = parser.parse_args(fakeargs)

#        print "About to CV check:", f
 
        try:
            process = validator.checkCMIP6(args)
            if process is None:
                raise ESGPublishError("File %s failed the CV check - object create failure"%f)

            process.ControlVocab()

        except:

            raise ESGPublishError("File %s failed the CV check"%f)

    def check_pid_avail(self, project_config_section, config, version=None):
        """ Returns the pid_prefix

         project_config_section
            The name of the project config section in esg.ini

        config
            The configuration (ini files)

        version
            Integer or Dict with dataset versions
        """
        # disable PIDs for local index without versioning (IPSL use case)
        if isinstance(version, int) and not version_pattern.match(str(version)):
            warning('Version %s, skipping PID generation.' % version)
            return None

        return '21.14100'

    def get_pid_config(self, project_config_section, config):
        """ Returns the project specific pid config

         project_config_section
            The name of the project config section in esg.ini

        config
            The configuration (ini files)
        """
        # get the PID configs
        pid_messaging_service_exchange_name = 'esgffed-exchange'

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
                raise ESGPublishError("Option 'pid_credentials' missing in section '%s' of esg.ini. "
                                      "Please contact your tier1 data node admin to get the proper values." % project_config_section)
        else:
            raise ESGPublishError("Section '%s' not found in esg.ini." % project_config_section)

        return pid_messaging_service_exchange_name, pid_messaging_service_credentials

    def get_citation_url(self, project_section, config, dataset_name, dataset_version):
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
        return 'http://cera-www.dkrz.de/WDCC/meta/CMIP6/%s.v%s.json' % (dataset_name, dataset_version)
