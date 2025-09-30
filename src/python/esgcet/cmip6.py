from esgcet.pid_cite_pub import ESGPubPidCite
from esgcet.activity_check import FieldCheck
import tempfile
from esgcet.generic_netcdf import GenericPublisher
import os
import esgcet.logger as logger

log = logger.ESGPubLogger()


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
        self.publog = log.return_logger('CMIP6', self.silent, self.verbose)
        self._disable_citation = argdict["disable_citation"]


    def pid(self, out_json_data):
      
        pid = ESGPubPidCite(out_json_data, self.pid_creds, self.data_node, test=self.test,
                            silent=self.silent, verbose=self.verbose,
                            project_family='CMIP6', disable_cite=self._disable_citation)
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

        # step two: extract
        self.publog.info(f"Running Extraction... {str(self.extract_method)}")
        self.extract_method(map_json_data)

        # step three: make dataset
        self.publog.info("Making dataset...")
        out_json_data = self.mk_dataset(map_json_data)

        # step four: assign PID
        self.publog.info("Assigning PID...")
        new_json_data = self.pid(out_json_data)
        
        #step five: update record if exists
        self.publog.info("Updating...")
        self.update(new_json_data)

        # step six: publish to database
        self.publog.info("Running index pub...")
        rc = self.index_pub(new_json_data)

        self.publog.info("Done. Cleaning up.")
        self.cleanup()
        return rc
