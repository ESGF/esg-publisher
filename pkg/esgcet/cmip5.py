import os
from esgcet.create_ip import CreateIP
from esgcet.mkd_cmip5 import ESGPubMKDCmip5
from esgcet.settings import VARIABLE_LIMIT
import tempfile
import esgcet.logger as logger

log = logger.ESGPubLogger()


class cmip5(CreateIP):

    def __init__(self, argdict):
        super().__init__(argdict)
        self.variable_limit = 100
        self.autoc_args = ' --out_pretty --out_json {} --files "{}/*.nc"'
        self.publog = log.return_logger('CMIP5', self.silent, self.verbose)

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
            self.publog.info("Autocurator command: " + autstr.format(scan, destpath))
            stat = os.system(autstr.format(scan, destpath))
            if os.WEXITSTATUS(stat) != 0:
                self.publog.error("Autocurator exited with exit code: " + str(os.WEXITSTATUS(stat)))
                self.cleanup()
                exit(os.WEXITSTATUS(stat))

    def mk_dataset(self, map_json_data):
        limit_exceeded = len(self.variables) > VARIABLE_LIMIT
        limit = False
        mkd = ESGPubMKDCmip5(self.data_node, self.index_node, self.replica, self.globus, self.data_roots,
                                self.dtn, self.silent, self.verbose, limit_exceeded)
        for scan in self.scans:
            try:
                out_json_data = mkd.get_records(map_json_data, scan.name, self.json_file)
                self.datasets.append(out_json_data)
            except:
                self.publog.exception("Occured while making dataset.")
                self.cleanup()
                exit(1)
            # only use first scan file if more than 75 variables
            if len(self.variables) > self.variable_limit:
                limit = True
                break

        self.master_dataset = mkd.aggregate_datasets(self.datasets, limit)
        return 0
