import os
from esgcet.generic_netcdf import GenericPublisher
from esgcet.mkd_create_ip import ESGPubMKDCreateIP
from esgcet.update import ESGPubUpdate
from esgcet.index_pub import ESGPubIndex
import tempfile
from esgcet.settings import VARIABLE_LIMIT
from copy import deepcopy
import esgcet.logger as logger

log = logger.ESGPubLogger()


class CreateIP(GenericPublisher):

    def __init__(self, argdict):
        super().__init__(argdict)

        self.scans = []
        self.datasets = []
        self.variables = []
        self.master_dataset = None
        self.variable_limit = 75
        self.autoc_args = ' --out_pretty --out_json {} --files "{}/{}_*.nc"'
        self.publog = log.return_logger('CREATE-IP', self.silent, self.verbose)

    def cleanup(self):
        for scan in self.scans:
            scan.close()

    def autocurator(self, map_json_data):
        datafile = map_json_data[0][1]
        destpath = os.path.dirname(datafile)

        autstr = self.autoc_command + self.autoc_args
        files = os.listdir(destpath)
        for f in files:
            var = f.split('_')[0]
            if var not in self.variables:
                self.variables.append(var)
        for var in self.variables:
            self.scans.append(
                tempfile.NamedTemporaryFile())  # create a temporary file which is deleted afterward for autocurator
            scan = self.scans[-1].name
            self.publog.info("Autocurator command: " + autstr.format(scan, destpath, var))
            stat = os.system(autstr.format(scan, destpath, var))
            if os.WEXITSTATUS(stat) != 0:
                self.publog.error("Autocurator exited with exit code: " + str(os.WEXITSTATUS(stat)))
                self.cleanup()
                exit(os.WEXITSTATUS(stat))

    def mk_dataset(self, map_json_data):
        limit_exceeded = len(self.variables) > VARIABLE_LIMIT
        limit = False
        mkd = ESGPubMKDCreateIP(self.data_node, self.index_node, self.replica, self.globus, self.data_roots,
                                self.dtn, self.silent, self.verbose, limit_exceeded)
        for scan in self.scans:
            try: 
                out_json_data = mkd.get_records(map_json_data, scan.name, self.json_file)
                self.datasets.append(deepcopy(out_json_data)) # herein lies the issue, copy hasn't fixed it
            except Exception as ex:
                self.publog.exception(f"Failed to make dataset: {ex}")
                self.cleanup()
                exit(1)
            # only use first scan file if more than 75 variables
            if len(self.variables) > self.variable_limit:
                limit = True
                break

        self.master_dataset = mkd.aggregate_datasets(self.datasets, limit)
        return 0

    def update(self, placeholder):
        up = ESGPubUpdate(self.index_node, self.cert, silent=self.silent, verbose=self.verbose, verify=self.verify, auth=self.auth)
        try:
            up.run(self.master_dataset)
        except Exception as ex:
            self.publog.exception(f"Failed to update record: {ex}")
            self.cleanup()
            exit(1)

    def index_pub(self, placeholder):
        ip = ESGPubIndex(self.index_node, self.cert, silent=self.silent, verbose=self.verbose, verify=self.verify, auth=self.auth)
        try:
            ip.do_publish(self.master_dataset)
        except Exception as ex:
            self.publog.exception(f"Failed to publish to index node: {ex}")
            self.cleanup()
            exit(1)
