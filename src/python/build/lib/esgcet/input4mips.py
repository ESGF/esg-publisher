from esgcet.mkd_input4mips import ESGPubMKDinput4MIPs
from esgcet.pid_cite_pub import ESGPubPidCite
from esgcet.cmip6 import cmip6
import esgcet.logger as logger

log = logger.ESGPubLogger()

class input4mips(cmip6):

    def __init__(self, argdict):
        super().__init__(argdict)
        self.MKD_Construct = ESGPubMKDinput4MIPs
        self.publog = log.return_logger('input4MIPs', self.silent, self.verbose)

    def pid(self, out_json_data):

        pid = ESGPubPidCite(out_json_data, self.pid_creds, self.data_node, test=self.test, silent=self.silent, verbose=self.verbose, disable_cite=self._disable_citation)
        try:
            new_json_data = pid.do_pidcite()
        except Exception as ex:
            self.publog.exception("Failed to assign pid")
            self.cleanup()
            exit(1)
        return new_json_data


    def workflow(self):

        # step one: convert mapfile
        self.publog.info("Converting mapfile...")
        map_json_data = self.mapfile()

        # step three: extract data
        self.publog.info(f"Running Extraction... {str(self.extract_method)}")
        self.extract_method(map_json_data)

        # step four: make dataset
        self.publog.info("Making dataset...")
        out_json_data = self.mk_dataset(map_json_data)

        # step five: assign PID
        self.publog.info("Assigning PID...")
        new_json_data = self.pid(out_json_data)

        # step seven: publish to database
        self.publog.info("Running index pub...")
        rc = self.index_pub(new_json_data)

        self.publog.info("Done. Cleaning up.")
        self.cleanup()
        return rc
