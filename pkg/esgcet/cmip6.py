from esgcet.pid_cite_pub import ESGPubPidCite
from esgcet.activity_check import FieldCheck
import tempfile
import json
from cmip6_cv import PrePARE
from esgcet.generic_pub import BasePublisher
from esgcet.generic_netcdf import GenericPublisher
import sys, os
import esgcet.logger as logger

log = logger.Logger()


class cmip6(GenericPublisher):

    scan_file = tempfile.NamedTemporaryFile()  # create a temporary file which is deleted afterward for autocurator
    scanfn = scan_file.name
    files = [scan_file, ]

    def __init__(self, argdict):
        super().__init__(argdict)
        self.pid_creds = argdict["pid_creds"]
        if "cmor_tables" in argdict:
            self.cmor_tables = os.path.expanduser(argdict["cmor_tables"])
        else:
            self.cmor_tables = None
        self.test = argdict["test"]
        if self.replica:
            self.skip_prepare = not argdict["force_prepare"]
        else:
            self.skip_prepare = argdict["skip_prepare"]
        self.publog = log.return_logger('CMIP6', self.silent, self.verbose)

    def prepare_internal(self, json_map, cmor_tables):
        try:
            assert(len(cmor_tables) > 0, f"{cmor_tables} are specified from config")
            assert(os.path.isdir(cmor_tables), f"{cmor_tables} exists and is a directory")
            self.publog.info("Iterating through filenames for PrePARE (internal version)...")
            validator = PrePARE.PrePARE
            for info in json_map:
                filename = info[1]
                process = validator.checkCMIP6(cmor_tables)
                process.ControlVocab(filename)
        except Exception as ex:
            self.publog.exception("PrePARE failed")
            self.cleanup()
            exit(1)

    def pid(self, out_json_data):
      
        pid = ESGPubPidCite(out_json_data, self.pid_creds, self.data_node, test=self.test,
                            silent=self.silent, verbose=self.verbose,
                            project_family='CMIP6')
        if self.cmor_tables:
            check = FieldCheck(self.cmor_tables, silent=self.silent)
            try:
                check.run_check(out_json_data)
            except:
                self.publog.exception("Activity/Metadata agreement check failed!")
                self.cleanup()
                exit(1)
            
        try:
            new_json_data = pid.do_pidcite()
        except Exception as ex:
            self.publog.exception("Assigning pid failed")
            self.cleanup()
            exit(1)

        return new_json_data

    def workflow(self):

        # step one: convert mapfile
        self.publog.info("Converting mapfile...")
        map_json_data = self.mapfile()

        # step two: PrePARE
        if not self.skip_prepare:
            self.prepare_internal(map_json_data, self.cmor_tables)

        # step three: autocurator
        self.publog.info("Running autocurator...")
        self.autocurator(map_json_data)

        # step four: make dataset
        self.publog.info("Making dataset...")
        out_json_data = self.mk_dataset(map_json_data)


        # step five: assign PID
        self.publog.info("Assigning PID...")
        new_json_data = self.pid(out_json_data)

        # step six: update record if exists
        self.publog.info("Updating...")
        self.update(new_json_data)

        # step seven: publish to database
        self.publog.info("Running index pub...")
        rc = self.index_pub(new_json_data)

        self.publog.info("Done. Cleaning up.")
        self.cleanup()
        return rc
