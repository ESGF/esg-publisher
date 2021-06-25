from esgcet.mk_dataset import ESGPubMakeDataset
import json, os, sys
import tempfile
from esgcet.generic_pub import BasePublisher
import traceback
import esgcet.logger as log

publog = log.return_logger('Generic NetCDF Publisher')

class GenericPublisher(BasePublisher):

    scan_file = tempfile.NamedTemporaryFile()  # create a temporary file which is deleted afterward for autocurator
    scanfn = scan_file.name

    def __init__(self, argdict):
        super().__init__(argdict)
        self.autoc_command = argdict["autoc_command"]
        self.MKD_Construct = ESGPubMakeDataset

    def check_files(self):
        pass

    def cleanup(self):
        self.scan_file.close()

    def autocurator(self, map_json_data):
        datafile = map_json_data[0][1]

        destpath = os.path.dirname(datafile)
        outname = os.path.basename(datafile)
        idx = outname.rfind('.')

        autstr = self.autoc_command + ' --out_pretty --out_json {} --files "{}/*.nc"'
        stat = os.system(autstr.format(self.scanfn, destpath))
        if os.WEXITSTATUS(stat) != 0:
            publog.error("Autocurator exited with exit code: " + str(os.WEXITSTATUS(stat)))
            self.cleanup()
            exit(os.WEXITSTATUS(stat))

    def mk_dataset(self, map_json_data):
        mkd = self.MKD_Construct(self.data_node, self.index_node, self.replica, self.globus, self.data_roots, self.dtn,
                                self.silent, self.verbose)
        try:
            out_json_data = mkd.get_records(map_json_data, self.scanfn, self.json_file, user_project=self.proj_config)
        except Exception as ex:
            publog.exception("Failed to make dataset")
            self.cleanup()
            exit(1)
        return out_json_data

    def workflow(self):

        # step one: convert mapfile
        if not self.silent:
            publog.info("Converting mapfile...")
        map_json_data = self.mapfile()

        # step two: autocurator
        if not self.silent:
            publog.info("Done.\nRunning autocurator...")
        self.autocurator(map_json_data)

        # step three: make dataset
        if not self.silent:
            publog.info("Done.\nMaking dataset...")
        out_json_data = self.mk_dataset(map_json_data)

        # step four: update record if exists
        if not self.silent:
            publog.info("Done.\nUpdating...")
        self.update(out_json_data)

        # step five: publish to database
        if not self.silent:
            publog.info("Done.\nRunning index pub...")
        self.index_pub(out_json_data)

        if not self.silent:
            publog.info("Done. Cleaning up.")
        self.cleanup()
