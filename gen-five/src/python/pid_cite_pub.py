import sys, json
from settings import PID_CREDS, DATA_NODE, PID_PREFIX, PID_EXCHANGE, URL_Templates, HTTP_SERVICE, CITATION_URLS, PID_URL, TEST_PUB
import traceback

def establish_pid_connection(pid_prefix, test_publication,  publish=True):

    """Establish a connection to the PID service
    pid_prefix
        PID prefix to be used for given project
    test_publication
        Boolean to flag PIDs as test
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

    # http_service_path = None

    # if publish:
    http_service_path = HTTP_SERVICE


    pid_connector = esgfpid.Connector(handle_prefix=pid_prefix,
                                      messaging_service_exchange_name=pid_messaging_service_exchange_name,
                                      messaging_service_credentials=pid_messaging_service_credentials,
                                      data_node=pid_data_node,
                                      thredds_service_path=http_service_path,
                                      test_publication=test_publication)
    # Check connection

    return pid_connector


def check_pid_connection(pid_prefix, pid_connector, send_message=False):
    """
    Check the connection to the PID rabbit MQ
    Raise an Error if connection fails
    """
    pid_queue_return_msg = pid_connector.check_pid_queue_availability(send_message=send_message)
    if pid_queue_return_msg is not None:
        raise Exception("Unable to establish connection to PID Messaging Service. Please check your esg.ini for correct pid_credentials.")

    pid_connector = establish_pid_connection(pid_prefix, TEST_PUB,  publish=True)



def get_url(arr):

    return arr[0].split('|')[0]

def pid_flow_code(dataset_recs):


    try:
        dsrec = dataset_recs[-1]
    except:
        print(dataset_recs)
        exit(-1)
    dset = dsrec['master_id']
    version_number = dsrec['version']
    is_replica = dsrec["replica"]

    pid_connector = establish_pid_connection(PID_PREFIX, TEST_PUB, publish=False)
    pid_connector.start_messaging_thread()

    dataset_pid = None
    if pid_connector:
        dataset_pid = pid_connector.make_handle_from_drsid_and_versionnumber(drs_id=dset, version_number=version_number)
        print("Assigned PID to dataset %s.v%s: %s " % (dset, version_number, dataset_pid))
    else:
        print('warning no connection')
    # if project uses citation, build citation url


    try:
        check_pid_connection(PID_PREFIX, pid_connector, send_message=True)

        pid_wizard = None
            # Check connection
        pid_wizard = pid_connector.create_publication_assistant(drs_id=dset,
                                                                    version_number=version_number,
                                                                    is_replica=is_replica)
    # Iterate this over all the files:
        if len(dataset_recs) > 1:
            for file_rec in dataset_recs[0:-1]:

                pid_wizard.add_file(file_name=file_rec['title'],
                                    file_handle=file_rec['tracking_id'],
                                    checksum=file_rec['checksum'],
                                    file_size=file_rec['size'],
                                    publish_path=get_url(file_rec['url']),
                                    checksum_type=file_rec['checksum_type'],
                                    file_version=file_rec['version'] )
        else:
            file_rec = dsrec
            pid_wizard.add_file(file_name=file_rec['title'],
                               file_handle=file_rec['tracking_id'],
                               checksum=file_rec['checksum'],
                               file_size=file_rec['size'],
                               publish_path=get_url(file_rec['url']),
                               checksum_type=file_rec['checksum_type'],
                               file_version=file_rec['version'])
        if pid_wizard:
            pid_wizard.dataset_publication_finished()
            return pid_connector, dataset_pid
        else:
            print("WARNING, empty pid_wizard!")

    except Exception as e:
        print("WARNING: PID module exception encountered! {}".format(str(e)))
        traceback.print_exc()

    pid_connector.force_finish_messaging_thread()
    return None, None

def update_dataset(dset_rec, pid, test_publication):


    project = dset_rec['project']
    if test_publication:
        keystr = 'test'
    else:
        keystr = 'prod'
    citation_url = CITATION_URLS[project][keystr].format(dset_rec['master_id'], dset_rec['version'])

    dset_rec['citation_url'] = citation_url
    dset_rec['xlink'] = ['{}|citation|Citation'.format(citation_url)]
    dset_rec['pid'] = pid
    dset_rec['xlink'].append(PID_URL.format(pid))
    return dset_rec


def rewrite_json(fname, recs):

    with open(fname, 'w') as f:
        f.write(json.dumps(recs, indent=1))

def main(args):

    res = args
    pid_connector, pid = pid_flow_code(res)

    if pid_connector is None:
        exit(-1)

    try:
        for i in range(len(res)):
            res[i] = update_dataset(res[i], pid, TEST_PUB)

    except Exception as e:
        print("WARNING: Some exception encountered! {}".format(str(e)))
        pid_connector.force_finish_messaging_thread()
        exit(-1)

#    print("before finish"). DEBUG
    pid_connector.finish_messaging_thread()
    return res
#    print("after finish") DEBUG

if __name__ == '__main__':
    main(sys.argv[1:])


#    "xlink":["http://cera-www.dkrz.de/WDCC/meta/CMIP6/CMIP6.RFMIP.MOHC.HadGEM3-GC31-LL.rad-irf.r1i1p3f3.Efx.rld.gn.v20191030.json|Citation|citation",
 #         "http://hdl.handle.net/hdl:21.14100/2720a03c-479a-3cdf-99e2-1265d90d51ae|PID|pid"],,



