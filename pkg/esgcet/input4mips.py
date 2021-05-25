from esgcet.pid_cite_pub import ESGPubPidCite
from esgcet.activity_check import FieldCheck
import tempfile
import json
from cmip6_cv import PrePARE
from esgcet.generic_pub import BasePublisher
from esgcet.generic_netcdf import GenericPublisher
import sys
from esgcet.mkd_input4mips import ESGPubMKDinput4MIPs

class input4mips(cmip6):

    scan_file = tempfile.NamedTemporaryFile()  # create a temporary file which is deleted afterward for autocurator
    scanfn = scan_file.name
    files = [scan_file, ]

    def __init__(self, argdict):
        # maybe get args here
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
        self.pid_creds = argdict["pid_creds"]
        self.cmor_tables = argdict["cmor_tables"]
        self.test = argdict["test"]
        self.proj_config = argdict["user_project_config"]
        self.verify = argdict["verify"]
        self.auth = argdict["auth"]
        if self.replica:
            self.skip_prepare= argdict["skip-prepare"]


    def mk_dataset(self, map_json_data):
        mkd = ESGPubMKDinput4MIPs(self.data_node, self.index_node, self.replica, self.globus, self.data_roots, self.dtn,
                                self.silent, self.verbose)
        try:
            out_json_data = mkd.get_records(map_json_data, self.scanfn, self.json_file, user_project=self.proj_config)
        except Exception as ex:
            print("Error making dataset: " + str(ex), file=sys.stderr)
            self.cleanup()
            exit(1)
        return out_json_data

    def workflow(self):

        # step one: convert mapfile
        if not self.silent:
            print("Converting mapfile...")
        map_json_data = self.mapfile()

        # step three: autocurator
        if not self.silent:
            print("Done.\nRunning autocurator...")
        self.autocurator(map_json_data)

        # step four: make dataset
        if not self.silent:
            print("Done.\nMaking dataset...")
        out_json_data = self.mk_dataset(map_json_data)


        # step five: assign PID
        if not self.silent:
            print("Done. Assigning PID...")
        new_json_data = self.pid(out_json_data)


        # step seven: publish to database
        if not self.silent:
            print("Done.\nRunning index pub...")
        self.index_pub(new_json_data)

        if not self.silent:
            print("Done. Cleaning up.")
        self.cleanup()
