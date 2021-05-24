import sys, os
import json
from esgcet.generic_pub import BasePublisher
from esgcet.generic_netcdf import GenericPublisher
from esgcet.mkd_create_ip import ESGPubMKDCreateIP
from esgcet.update import ESGPubUpdate
from esgcet.index_pub import ESGPubIndex
import tempfile
from esgcet.settings import VARIABLE_LIMIT


class CreateIP(GenericPublisher):

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

    def cleanup(self):
        for scan in self.scans:
            scan.close()

    def autocurator(self, map_json_data):
        datafile = map_json_data[0][1]

        destpath = os.path.dirname(datafile)
        outname = os.path.basename(datafile)
        idx = outname.rfind('.')  # was this needed for something?

        autstr = self.autoc_command + ' --out_pretty --out_json {} --files "{}/{}_*.nc"'
        files = os.listdir(destpath)
        for f in files:
            var = f.split('_')[0]
            if var not in self.variables:
                self.variables.append(var)
        for var in self.variables:
            self.scans.append(
                tempfile.NamedTemporaryFile())  # create a temporary file which is deleted afterward for autocurator
            scan = self.scans[-1].name
            print(autstr.format(scan, destpath, var))
            stat = os.system(autstr.format(scan, destpath, var))
            if os.WEXITSTATUS(stat) != 0:
                print("Error running autocurator, exited with exit code: " + str(os.WEXITSTATUS(stat)), file=sys.stderr)
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
                self.datasets.append(out_json_data)
            except Exception as ex:
                print("Error making dataset: " + str(ex), file=sys.stderr)
                self.cleanup()
                exit(1)
            # only use first scan file if more than 75 variables
            if len(self.variables) > VARIABLE_LIMIT:
                limit = True
                break

        print(json.dumps(self.datasets, indent=4))

        self.master_dataset = mkd.aggregate_datasets(self.datasets, limit)
        return 0

    def update(self, placeholder):
        up = ESGPubUpdate(self.index_node, self.cert, silent=self.silent, verbose=self.verbose, verify=self.verify, auth=self.auth)
        try:
            up.run(self.master_dataset)
        except Exception as ex:
            print("Error updating: " + str(ex), file=sys.stderr)
            self.cleanup()
            exit(1)

    def index_pub(self, placeholder):
        ip = ESGPubIndex(self.index_node, self.cert, silent=self.silent, verbose=self.verbose, verify=self.verify, auth=self.auth)
        try:
            ip.do_publish(self.master_dataset)
        except Exception as ex:
            print("Error running index pub: " + str(ex), file=sys.stderr)
            self.cleanup()
            exit(1)
