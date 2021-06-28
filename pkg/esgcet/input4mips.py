from esgcet.mkd_input4mips import ESGPubMKDinput4MIPs
from esgcet.pid_cite_pub import ESGPubPidCite
from esgcet.cmip6 import cmip6
import esgcet.logger as logger

log = logger.Logger()
publog = log.return_logger('input4MIPs')

class input4mips(cmip6):

    def __init__(self, argdict):
        super().__init__(argdict)
        self.MKD_Construct = ESGPubMKDinput4MIPs

    def pid(self, out_json_data):

        pid = ESGPubPidCite(out_json_data, self.pid_creds, self.data_node, test=self.test, silent=self.silent, verbose=self.verbose)

        try:
            new_json_data = pid.do_pidcite()
        except Exception as ex:
            publog.exception("Failed to assign pid")
            self.cleanup()
            exit(1)
        return new_json_data


    def workflow(self):

        # step one: convert mapfile
        if not self.silent:
            publog.info("Converting mapfile...")
        map_json_data = self.mapfile()

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

        # step seven: publish to database
        if not self.silent:
            publog.info("Done.\nRunning index pub...")
        self.index_pub(new_json_data)

        if not self.silent:
            publog.info("Done. Cleaning up.")
        self.cleanup()
