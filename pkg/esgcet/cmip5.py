import sys, os
from esgcet.create_ip import CreateIP
from esgcet.mkd_cmip5 import ESGPubMKDCmip5
from esgcet.settings import VARIABLE_LIMIT

import tempfile


class cmip5(CreateIP):

    def __init__(self, argdict):
        self.argdict = argdict
        self.fullmap = argdict["fullmap"]
        self.silent = argdict["silent"]
        self.verbose = argdict["verbose"]
        self.cert = argdict["cert"]
        self.autoc_command = argdict["autoc_command"]
        self.index_node = argdict["index_node"]
        self.data_node = argdict["data_node"]
        self.data_roots = argdict["data_roots"]
        self.globus = argdict["globus"]
        self.dtn = argdict["dtn"]
        self.replica = argdict["replica"]
        self.proj = argdict["proj"]
        self.json_file = argdict["json_file"]
        self.proj_config = argdict["user_project_config"]
        self.verify = argdict["verify"]
        self.auth = argdict["auth"]

        self.scans = []
        self.datasets = []
        self.variables = []
        self.master_dataset = None
        self.variable_limit = 100
        self.autoc_args = ' --out_pretty --out_json {} --files "{}/*.nc"'

    def autocurator(self, map_json_data):
        datafile = map_json_data[0][1]

        destpath = os.path.dirname(datafile)
        outname = os.path.basename(datafile)
        idx = outname.rfind('.')  # was this needed for something?

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
            print(autstr.format(scan, destpath))
            stat = os.system(autstr.format(scan, destpath))
            if os.WEXITSTATUS(stat) != 0:
                print("Error running autocurator, exited with exit code: " + str(os.WEXITSTATUS(stat)), file=sys.stderr)
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
            except Exception as ex:
                print("Error making dataset: " + str(ex), file=sys.stderr)
                self.cleanup()
                exit(1)
            # only use first scan file if more than 75 variables
            if len(self.variables) > self.variable_limit:
                limit = True
                break

        self.master_dataset = mkd.aggregate_datasets(self.datasets, limit)
        return 0