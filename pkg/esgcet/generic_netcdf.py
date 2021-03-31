from esgcet.mk_dataset import ESGPubMakeDataset
import json, os, sys
import tempfile
from esgcet.generic_pub import BasePublisher


class GenericPublisher(BasePublisher):

    scan_file = tempfile.NamedTemporaryFile()  # create a temporary file which is deleted afterward for autocurator
    scanfn = scan_file.name

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
        pass

    def check_files(self):
        pass

    def cleanup(self):
        self.scan_file.close()

    def autocurator(self, map_json_data, autoc_cmd):
        datafile = map_json_data[0][1]

        destpath = os.path.dirname(datafile)
        outname = os.path.basename(datafile)
        idx = outname.rfind('.')

        autstr = autoc_cmd + ' --out_pretty --out_json {} --files "{}/*.nc"'
        stat = os.system(autstr.format(self.scanfn, destpath))
        if os.WEXITSTATUS(stat) != 0:
            print("Error running autocurator, exited with exit code: " + str(os.WEXITSTATUS(stat)), file=sys.stderr)
            self.cleanup()
            exit(os.WEXITSTATUS(stat))

    def mk_dataset(self, map_json_data):
        mkd = ESGPubMakeDataset(self.data_node, self.index_node, self.replica, self.globus, self.data_roots, self.dtn,
                                self.silent, self.verbose)
        try:
            out_json_data = mkd.run(map_json_data, self.scanfn, self.json_file)
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

        # step two: autocurator
        if not self.silent:
            print("Done.\nRunning autocurator...")
        self.autocurator(map_json_data, self.autoc_command)

        # step three: make dataset
        if not self.silent:
            print("Done.\nMaking dataset...")
        out_json_data = self.mk_dataset(map_json_data)

        # step four: update record if exists
        if not self.silent:
            print("Done.\nUpdating...")
        self.update(out_json_data)

        # step five: publish to database
        if not self.silent:
            print("Done.\nRunning index pub...")
        self.index_pub(out_json_data)

        if not self.silent:
            print("Done. Cleaning up.")
        self.cleanup()
