from esgcet.pid_cite_pub import ESGPubPidCite
from esgcet.activity_check import FieldCheck
import tempfile
import json
from cmip6_cv import PrePARE
from esgcet.generic_pub import BasePublisher
from esgcet.generic_netcdf import GenericPublisher
import sys
import logging

publog = logging.getLogger('CMIP6')
publog.setLevel('INFO')

class cmip6(GenericPublisher):

    scan_file = tempfile.NamedTemporaryFile()  # create a temporary file which is deleted afterward for autocurator
    scanfn = scan_file.name
    files = [scan_file, ]

    def __init__(self, argdict):
        super().__init__(argdict)
        self.pid_creds = argdict["pid_creds"]
        self.cmor_tables = argdict["cmor_tables"]
        self.test = argdict["test"]
        if self.replica:
            self.skip_prepare= argdict["skip-prepare"]

    def prepare_internal(self, json_map, cmor_tables):
        try:
            publog.info("Iterating through filenames for PrePARE (internal version)...")
            validator = PrePARE.PrePARE
            for info in json_map:
                filename = info[1]
                process = validator.checkCMIP6(cmor_tables)
                process.ControlVocab(filename)
        except Exception as ex:
            publog.exception("PrePARE failed")
            self.cleanup()
            exit(1)

    def pid(self, out_json_data):
      
        pid = ESGPubPidCite(out_json_data, self.pid_creds, self.data_node, test=self.test, silent=self.silent, verbose=self.verbose)
        check = FieldCheck(self.cmor_tables, silent=self.silent)

        try:
            check.run_check(out_json_data)
            new_json_data = pid.do_pidcite()
        except Exception as ex:
            publog.exception("Assigning pid or running activity check failed")
            self.cleanup()
            exit(1)
        return new_json_data

    def workflow(self):

        # step one: convert mapfile
        if not self.silent:
            publog.info("Converting mapfile...")
        map_json_data = self.mapfile()

        # step two: PrePARE
        self.prepare_internal(map_json_data, self.cmor_tables)

        # step three: autocurator
        if not self.silent:
            publog.info("Done.\nRunning autocurator...")
        self.autocurator(map_json_data)

        # step four: make dataset
        if not self.silent:
            publog.info("Done.\nMaking dataset...")
        out_json_data = self.mk_dataset(map_json_data)


        # step five: assign PID
        if not self.silent:
            publog.info("Done. Assigning PID...")
        new_json_data = self.pid(out_json_data)

        # step six: update record if exists
        if not self.silent:
            publog.info("Done.\nUpdating...")
        self.update(new_json_data)

        # step seven: publish to database
        if not self.silent:
            publog.info("Done.\nRunning index pub...")
        self.index_pub(new_json_data)

        if not self.silent:
            publog.info("Done. Cleaning up.")
        self.cleanup()
