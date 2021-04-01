import tempfile
import json, sys
from cmip6_cv import PrePARE
from esgcet.generic_pub import BasePublisher
from esgcet.generic_netcdf import GenericPublisher
from esgcet.mkd_cordex import ESGPubMKDCordex

class cordex(GenericPublisher):

    scan_file = tempfile.NamedTemporaryFile()  # create a temporary file which is deleted afterward for autocurator
    scanfn = scan_file.name

    def mk_dataset(self, map_json_data):
        mkd = ESGPubMKDCordex(self.data_node, self.index_node, self.replica, self.globus, self.data_roots,
                                self.dtn, self.silent, self.verbose)
        try:
            out_json_data = mkd.run(map_json_data, self.scanfn, self.json_file)
        except Exception as ex:
            print("Error making dataset: " + str(ex), file=sys.stderr)
            self.cleanup()
            exit(1)
        return out_json_data
