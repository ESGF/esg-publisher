""""Handle CMIP6 data file metadata"""

import re

from cmip6_cv import PrePARE
from esgcet.config import BasicHandler, getConfig, compareLibVersions, splitRecord
from esgcet.exceptions import *
from esgcet.messaging import debug, info, warning
from esgcet.publish import getTableDir

WARN = False

DEFAULT_CMOR_TABLE_PATH = "/usr/local/cmip6-cmor-tables/Tables"

version_pattern = re.compile('20\d{2}[0,1]\d[0-3]\d')


class CMIP6Handler(BasicHandler):

    def __init__(self, name, path, Session, validate=True, offline=False, replica=False):
        self.replica = replica
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

        validator = PrePARE.PrePARE

        f = fileobj.path

        # todo refactoring these could loaded upfront in the constructor
        config = getConfig()
        project_section = 'project:' + self.name
        project_config_section = 'config:' + self.name
        min_cmor_version = config.get(project_section, "min_cmor_version", default="0.0.0")
        min_ds_version = config.get(project_section, "min_data_specs_version", default="0.0.0")
        data_specs_version = config.get(project_config_section, "data_specs_version", default="master")
        cmor_table_path = config.get(project_config_section, "cmor_table_path", default=DEFAULT_CMOR_TABLE_PATH)
        force_validation = config.getboolean(project_config_section, "force_validation", default=False)
        cmor_table_subdirs = config.getboolean(project_config_section, "cmor_table_subdirs", default=False)

        if not force_validation:

            if self.replica:
                info("skipping PrePARE for replica (file %s)" % f)
                return

            try:
                file_cmor_version = fileobj.getAttribute('cmor_version', None)
            except:
                file_cmor_version = None
                debug('File %s missing cmor_version attribute; will proceed with PrePARE check' % f)

            passed_cmor = False
            if compareLibVersions(min_cmor_version, file_cmor_version):
                debug('File %s cmor-ized at version %s, passed!'%(f, file_cmor_version))
                passed_cmor = True

        try:
            table = fileobj.getAttribute('table_id', None)
        except:
            raise ESGPublishError("File %s missing required table_id global attribute" % f)

        try:
            variable_id = fileobj.getAttribute('variable_id', None)
        except:
            raise ESGPublishError("File %s missing required variable_id global attribute" % f)

        # data_specs_version drives CMOR table fetching
        # Behavior A (default): fetches "master" branch" (if not "data_specs_version" in esg.ini")
        # Behavior A: fetches branch specified by "data_specs_version=my_branch" into esg.ini
        # Behavior B: fetches branch specified by file global attributes using "data_specs_version=file" into esg.ini

        try:
            file_data_specs_version = fileobj.getAttribute('data_specs_version', None)
        except Exception as e:
            raise ESGPublishError("File %s missing required data_specs_version global attribute"%f)

        if not compareLibVersions(min_ds_version, file_data_specs_version):
            raise ESGPublishError("File %s data_specs_version is %s, which is less than the required minimum version of %s"%(f,file_data_specs_version,min_ds_version))
        # at this point the file has the correct data specs version.
        # if also was CMORized and has the correct version tag, we can exit

        if (not force_validation) and passed_cmor:
            return
            
        if data_specs_version == "file":
            data_specs_version = file_data_specs_version

        table_dir = getTableDir(cmor_table_path, data_specs_version, cmor_table_subdirs)
        debug("Validating {} using tables dir: {}".format(f, table_dir))

        try:
            process = validator.checkCMIP6(table_dir)
            if process is None:
                raise ESGPublishError("File %s failed the CV check - object create failure"%f)
            process.ControlVocab(f)
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
                        raise ESGPublishError(
                            "Misconfiguration: 'pid_credentials', section '%s' of esg.ini." % project_config_section)

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

    def get_citation_url(self, project_section, config, dataset_name, dataset_version, test_publication):
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
        if test_publication:
            return 'http://cera-www.dkrz.de/WDCC/testmeta/CMIP6/%s.v%s.json' % (dataset_name, dataset_version)
        else:
            return 'http://cera-www.dkrz.de/WDCC/meta/CMIP6/%s.v%s.json' % (dataset_name, dataset_version)
