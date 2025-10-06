import sys, json
from esgcet.settings import PID_PREFIX, PID_EXCHANGE, HTTP_SERVICE, CITATION_URLS, PID_URL
import traceback
import esgcet.logger as logger


log = logger.ESGPubLogger()

silent = False
verbose = False
pid_creds = {}
import traceback

class ESGPubPidCite(object):
    """ for PID services wraps calls to obtain a PID, add to records and generate citiation metadata """

    def __init__(self, ds_recs, pid_creds, data_node, test=False, silent=False, verbose=False, pid_prefix=PID_PREFIX,
                 project_family=None, disable_cite=False):
        """ Constructor
            ds_rec - a dataset record (dictionary/json)
            pid_creds - credentials typically loaded from config file, contains PID server, password, etc.
            silent, verbose - suppress info msgs, extend print
            test - register PID in test mode, essential for testing """
        self.ds_records = ds_recs
        self.pid_creds = pid_creds
        if type(self.pid_creds) == dict:
            self.pid_creds = [ self.pid_creds, ]
        self.silent = silent
        self.verbose = verbose
        self.test_publication = test
        self.pid_prefix = pid_prefix
        self.project_family = project_family
        self.data_node = data_node
        self.publog = log.return_logger('PID Citation', silent, verbose)
        self._disable_cite = disable_cite

    def establish_pid_connection(self):
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
            self.publog.exception("PID module not found. Please install the package 'esgfpid' (e.g. with 'pip install').")
            exit(1)

        pid_messaging_service_exchange_name = PID_EXCHANGE
        pid_messaging_service_credentials = self.pid_creds
        pid_data_node = self.data_node

        # http_service_path = None

        # if publish:
        http_service_path = HTTP_SERVICE

        print(f" self.pid_connector = esgfpid.Connector(handle_prefix={self.pid_prefix}, \
                                          messaging_service_exchange_name={pid_messaging_service_exchange_name}, \
                                          messaging_service_credentials={pid_messaging_service_credentials}, \
                                          data_node={pid_data_node}, \
                                          thredds_service_path={http_service_path}, \
                                          test_publication={self.test_publication}")
        self.pid_connector = esgfpid.Connector(handle_prefix=self.pid_prefix,
                                          messaging_service_exchange_name=pid_messaging_service_exchange_name,
                                          messaging_service_credentials=pid_messaging_service_credentials,
                                          data_node=pid_data_node,
                                          thredds_service_path=http_service_path,
                                          test_publication=self.test_publication)
        # Check connection



    def check_pid_connection(self,  send_message=False):
        """
        Check the connection to the PID rabbit MQ
        Raise an Error if connection fails
        """
        pid_queue_return_msg = self.pid_connector.check_pid_queue_availability(send_message=send_message)
        if pid_queue_return_msg is not None:
            self.publog.error("Unable to establish connection to PID Messaging Service. Please check your esg.ini for correct pid_credentials.")



    def pid_flow_code(self):

        dsrec = {}
        try:
            dsrec = self.ds_records[-1]
        except:
            self.publog.exception("Failed to obtain dataset record: {}".format(str(self.ds_records)))
            exit(-1)
        if not 'data_node' in dsrec:
            self.publog.error("Record missing data node value")
            exit(-1)
        self.data_node = dsrec['data_node']
        dset = dsrec['master_id']
        version_number = dsrec['version']
        is_replica = dsrec["replica"]

        self.establish_pid_connection()
        self.pid_connector.start_messaging_thread()

        self.dataset_pid = None
        if self.pid_connector:
            self.dataset_pid = self.pid_connector.make_handle_from_drsid_and_versionnumber(drs_id=dset, version_number=version_number)
            self.publog.info("Assigned PID to dataset %s.v%s: %s " % (dset, version_number, self.dataset_pid))
        else:
            self.publog.warning('No connection')
        # if project uses citation, build citation url


        try:
            self.check_pid_connection(send_message=True)

            pid_wizard = None
                # Check connection
            pid_wizard = self.pid_connector.create_publication_assistant(drs_id=dset,
                                                                        version_number=version_number,
                                                                        is_replica=is_replica)
        # Iterate this over all the files:
            if len(self.ds_records) > 1:
                for file_rec in self.ds_records[0:-1]:

                    pid_wizard.add_file(file_name=file_rec['title'],
                                        file_handle=file_rec['tracking_id'],
                                        checksum=file_rec['checksum'],
                                        file_size=file_rec['size'],
                                        publish_path=file_rec['publish_path'],
                                        checksum_type=file_rec['checksum_type'],
                                        file_version=file_rec['version'] )
            else:
                file_rec = dsrec
                pid_wizard.add_file(file_name=file_rec['title'],
                                   file_handle=file_rec['tracking_id'],
                                   checksum=file_rec['checksum'],
                                   file_size=file_rec['size'],
                                   publish_path=file_rec['publish_path'],
                                   checksum_type=file_rec['checksum_type'],
                                   file_version=file_rec['version'])
            if pid_wizard:
                pid_wizard.dataset_publication_finished()
                return True
            else:
                self.publog.warning("Empty pid_wizard!")

        except Exception as e:
            traceback.print_exc()
            self.publog.exception("PID module exception encountered!")

        self.pid_connector.force_finish_messaging_thread()
        return False

    def pid_unpublish(self, drs_id, version):

        self.establish_pid_connection()
        self.pid_connector.start_messaging_thread()

        try:
            self.pid_connector.unpublish_one_version(drs_id=drs_id, version_number=version)
            self.pid_connector.finish_messaging_thread()
            return True
        except Exception as e:
            traceback.print_exc()
            self.pid_connector.force_finish_messaging_thread()
            self.publog.exception("PID module exception encountered!")

        self.pid_connector.force_finish_messaging_thread()
        return False


    def update_dataset(self, index):

        dset_rec = self.ds_records[index]
        # project is taken from the record metadata unless project_family is a truthy value
        # (defaults to None, but might be e.g. 'CMIP6')
        project = (self.project_family or dset_rec['project']).lower()
        # At present we only support the stock templates from CMIP6
        if not project in CITATION_URLS:
            return
        if self.test_publication:
            keystr = 'test'
        else:
            keystr = 'prod'

        
        dset_rec['pid'] = self.dataset_pid
        if not (dset_rec['type'] == 'File'):
            dset_rec['xlink'] = [PID_URL.format(self.dataset_pid)]

        if not self._disable_cite:

            citation_url = CITATION_URLS[project][keystr].format(dset_rec['master_id'], dset_rec['version'])

            dset_rec['citation_url'] = citation_url
            if not (dset_rec['type'] == 'File'):
                dset_rec['xlink'].append('{}|Citation|citation'.format(citation_url))

        self.ds_records[index] = dset_rec

    def do_pidcite(self):
        
        ret = self.pid_flow_code()

        if not ret:
            exit(-1)

        try:
            for i in range(len(self.ds_records)):
                self.update_dataset(i)

        except Exception as e:
            traceback.print_exc()
            self.publog.exception("Some exception encountered!")
            self.pid_connector.force_finish_messaging_thread()
            exit(-1)

        self.pid_connector.finish_messaging_thread()

        return self.ds_records

    def rewrite_json(self, fname):
        with open(fname, 'w') as f:
            f.write(json.dumps(self.ds_records, indent=1))


    def do_pidciterewrite(self, fname):
        res = self.do_pidcite()
        if type(res) is list:
            self.rewrite_json(fname)
        else:
            self.publog.warning("Something went wrong, PID/cite information were not added")




#    "xlink":["http://cera-www.dkrz.de/WDCC/meta/CMIP6/CMIP6.RFMIP.MOHC.HadGEM3-GC31-LL.rad-irf.r1i1p3f3.Efx.rld.gn.v20191030.json|Citation|citation",
 #         "http://hdl.handle.net/hdl:21.14100/2720a03c-479a-3cdf-99e2-1265d90d51ae|PID|pid"],,



