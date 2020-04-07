def establish_pid_connection(pid_prefix, test_publication, project_config_section, config, handler, publish=True):

    """Establish a connection to the PID service

    pid_prefix
        PID prefix to be used for given project

    test_publication
        Boolean to flag PIDs as test

     project_config_section
        The name of the project config section in esg.ini

    config
        Loaded config file(s)

    handler
        Project handler to be used for given project

    publish
        Flag to trigger publication and unpublication
    """
    try:
        import esgfpid
    except ImportError:
        raise "PID module not found. Please install the package 'esgfpid' (e.g. with 'pip install')."

    pid_messaging_service_exchange_name, pid_messaging_service_credentials = handler.get_pid_config(project_config_section, config)
    pid_data_node = urllib.parse.urlparse(config.get('DEFAULT', 'thredds_url')).netloc
    thredds_service_path = None
    if publish:
        thredds_file_specs = getThreddsServiceSpecs(config, 'DEFAULT', 'thredds_file_services')
        for serviceType, base, name, compoundName in thredds_file_specs:
            if serviceType == 'HTTPServer':
                thredds_service_path = base
                break

    pid_connector = esgfpid.Connector(handle_prefix=pid_prefix,
                                      messaging_service_exchange_name=pid_messaging_service_exchange_name,
                                      messaging_service_credentials=pid_messaging_service_credentials,
                                      data_node=pid_data_node,
                                      thredds_service_path=thredds_service_path,
                                      test_publication=test_publication)
    # Check connection
    check_pid_connection(pid_connector, send_message=True)

    return pid_connector


def check_pid_connection(pid_connector, send_message=False):
    """
    Check the connection to the PID rabbit MQ
    Raise an Error if connection fails
    """
    return
    pid_queue_return_msg = pid_connector.check_pid_queue_availability(send_message=send_message)
    if pid_queue_return_msg is not None:
        raise ESGPublishError("Unable to establish connection to PID Messaging Service. Please check your esg.ini for correct pid_credentials.")



            pid_prefix = handler.check_pid_avail(project_config_section, config, version=version)
            if pid_prefix:
                pid_connector = establish_pid_connection(pid_prefix, test_publication, project_config_section, config, handler, publish=True)
                if thredds:
                    pid_connector.start_messaging_thread()

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


def flow_code(datasetName,newVersion):

    dataset_pid = None
    if pid_connector:
        dataset_pid = pid_connector.make_handle_from_drsid_and_versionnumber(drs_id=datasetName, version_number=newVersion)
        info("Assigned PID to dataset %s.v%s: %s " % (datasetName, newVersion, dataset_pid))

    # if project uses citation, build citation url
    project_config_section = 'config:%s' %context.get('project')
    citation_url = handler.get_citation_url(project_config_section, config, datasetName, newVersion, test_publication)

    newDsetVersionObj = DatasetVersionFactory(dset, version=newVersion, creation_time=createTime, comment=comment, tech_notes=datasetTechNotes,
                                                  tech_notes_title=datasetTechNotesTitle, pid=dataset_pid, citation_url=citation_url)

    if pid_connector and not dsetVersionObj.pid:
        dsetVersionObj.pid = pid_connector.make_handle_from_drsid_and_versionnumber(drs_id=datasetName, version_number=versionNumber)
        info("Assigned PID to dataset %s.v%s: %s " % (datasetName, versionNumber, dsetVersionObj.pid))
        pid_wizard = None
        # Check connection
        check_pid_connection(pid_connector)
        pid_wizard = pid_connector.create_publication_assistant(drs_id=datasetName,
                                                                version_number=versionNumber,
                                                                is_replica=is_replica)
# Iterate this over all the files:
        pid_wizard.add_file(file_name=name,
                    file_handle=trackingID,
                    checksum=checksum,
                    file_size=size,
                    publish_path=publishPath,
                    checksum_type=checksumType,
                    file_version=fileVersion)

        if pid_wizard:
            pid_wizard.dataset_publication_finished()


