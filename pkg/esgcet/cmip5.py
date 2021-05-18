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

    def mk_dataset(self, map_json_data):
        limit_exceeded = len(self.variables) > VARIABLE_LIMIT
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
            if len(self.variables) > VARIABLE_LIMIT:
                break

        self.master_dataset = mkd.aggregate_datasets(self.datasets)
        return 0
