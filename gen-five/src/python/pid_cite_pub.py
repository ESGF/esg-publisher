import sys, json
from settings import PID_CREDS, DATA_NODE, PID_PREFIX, PID_EXCHANGE, URL_TEMPLATES, HTTP_SERVICE, CITATION_URLS



def establish_pid_connection(pid_prefix, test_publication,  publish=True):

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

    pid_messaging_service_exchange_name = PID_EXCHANGE
    pid_messaging_service_credentials = PID_CREDS
    pid_data_node = DATA_NODE

    http_service_path = None

    if publish:
        http_service_path = HTTP_SERVICE 



    pid_connector = esgfpid.Connector(handle_prefix=pid_prefix,
                                      messaging_service_exchange_name=pid_messaging_service_exchange_name,
                                      messaging_service_credentials=pid_messaging_service_credentials,
                                      data_node=pid_data_node,
                                      http_service_path=http_service_path,
                                      test_publication=test_publication)
    # Check connection
    check_pid_connection(pid_connector, send_message=True)

    return pid_connector


def check_pid_connection(pid_connector, send_message=False):
    """
    Check the connection to the PID rabbit MQ
    Raise an Error if connection fails
    """
    pid_queue_return_msg = pid_connector.check_pid_queue_availability(send_message=send_message)
    if pid_queue_return_msg is not None:
        raise ESGPublishError("Unable to establish connection to PID Messaging Service. Please check your esg.ini for correct pid_credentials.")

    pid_connector = establish_pid_connection(pid_prefix, test_publication, project_config_section, config, handler, publish=True)
    pid_connector.start_messaging_thread()




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


def pid_flow_code(pid_connector, dataset_recs, is_replica):


    dsrec = dataset_recs[-1]
    dset = dsrec['master_id']
    version_number = dsrec['version']

    dataset_pid = None
    if pid_connector:
        dataset_pid = pid_connector.make_handle_from_drsid_and_versionnumber(drs_id=datasetName, version_number=newVersion)
        info("Assigned PID to dataset %s.v%s: %s " % (datasetName, newVersion, dataset_pid))
    else:
        print('warning no connection')
    # if project uses citation, build citation url



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




def get_dataset_pid()


    dset_rec = res[-1]
    if dset_rec

    pid_connector = establish_pid_connection(pid_prefix, test_publication, project_config_section, config, handler, publish=False)


def update_dataset(dset_rec, pid, test_publication):


    project = dset_rec['project']
    if test_publication:
        keystr = 'test'
    else:
        keystr = 'prod'
    citation_url = CITATION_URLS['project'][keystr]

    dset_rec['citation_url'] = citation_url
    dset_rec['xlink'] = '{}|citation|Citation'.format(citation_url)


def main(args):

    res = json.load(open(args[0]))



#    "xlink":["http://cera-www.dkrz.de/WDCC/meta/CMIP6/CMIP6.RFMIP.MOHC.HadGEM3-GC31-LL.rad-irf.r1i1p3f3.Efx.rld.gn.v20191030.json|Citation|citation",
 #         "http://hdl.handle.net/hdl:21.14100/2720a03c-479a-3cdf-99e2-1265d90d51ae|PID|pid"],



