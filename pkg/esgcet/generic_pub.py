from esgcet.mapfile import ESGPubMapConv
from esgcet.mkd_non_nc import ESGPubMKDNonNC
from esgcet.update import ESGPubUpdate
from esgcet.index_pub import ESGPubIndex
import sys
import esgcet.logger as logger

log = logger.Logger()


class BasePublisher(object):

    def __init__(self, argdict):
        self.argdict = argdict
        self.fullmap = argdict["fullmap"]
        self.silent = argdict["silent"]
        self.verbose = argdict["verbose"]
        self.cert = argdict["cert"]
        self.index_node = argdict["index_node"]
        self.data_node = argdict["data_node"]
        self.data_roots = argdict["data_roots"]
        self.globus = argdict["globus"]
        self.dtn = argdict["dtn"]
        self.replica = argdict["replica"]
        self.proj = argdict["proj"]
        self.json_file = argdict["json_file"]
        self.auth = argdict["auth"]
        self.proj_config = argdict["user_project_config"]
        self.verify = argdict["verify"]
        self.mountpoints = argdict["mountpoints"]
        self.project = argdict["proj"]
        self.publog = log.return_logger('Generic Non-NetCDF Publisher', self.silent, self.verbose)

    def cleanup(self):
        pass

    def mapfile(self):

        mapconv = ESGPubMapConv(self.fullmap, project=self.project)
        map_json_data = None
        try:
            map_json_data = mapconv.mapfilerun(self.mountpoints)

        except Exception as ex:
            self.publog.exception("Failed to convert mapfile")
            self.cleanup()
            exit(1)
        return map_json_data

    def mk_dataset(self, map_json_data):
        mkd = ESGPubMKDNonNC(self.data_node, self.index_node, self.replica, self.globus, self.data_roots, self.dtn,
                                self.silent, self.verbose)
        mkd.set_project(self.project)
        try:
            out_json_data = mkd.get_records(map_json_data, self.json_file, user_project=self.proj_config)
        except Exception as ex:
            self.publog.exception("Failed to make dataset")
            self.cleanup()
            exit(1)
        return out_json_data

    def update(self, json_data):
        up = ESGPubUpdate(self.index_node, self.cert, silent=self.silent, verbose=self.verbose, verify=self.verify, auth=self.auth)
        try:
            up.run(json_data)
        except Exception as ex:
            self.publog.exception("Failed to update record")
            self.cleanup()
            exit(1)

    def index_pub(self,dataset_records):
        arch_cfg = None
        if self.argdict["enable_archive"]:
            arch_cfg = { "length" : int(self.argdict["archive_path_length"]) , 
                          "archive_path" : self.argdict["archive_path"]}

        ip = ESGPubIndex(self.index_node, self.cert, silent=self.silent, verbose=self.verbose, verify=self.verify, auth=self.auth, arch_cfg=arch_cfg)
        rc = True
        try:
            rc = ip.do_publish(dataset_records)
        except Exception as ex:
            self.publog.exception("Failed to publish to index node")
            self.cleanup()
            exit(1)
        return rc

    def workflow(self):

        # step one: convert mapfile
        self.publog.info("Converting mapfile...")
        map_json_data = self.mapfile()

        # step two: make dataset
        self.publog.info("Making dataset...")
        out_json_data = self.mk_dataset(map_json_data)

        self.publog.info("Updating...")
        self.update(out_json_data)

        self.publog.info("Running index pub...")
        
        rc = self.index_pub(out_json_data)

        self.publog.info("Done.")

        return rc
