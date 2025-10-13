from esgcet.mapfile import ESGPubMapConv
from esgcet.mkd_non_nc import ESGPubMKDNonNC
from esgcet.update_solr import ESGUpdateSolr
from esgcet.update_globus import ESGUpdateGlobus

from esgcet.index_pub import ESGPubIndex
import sys
import esgcet.logger as logger

log = logger.ESGPubLogger()


class BasePublisher(object):

    def __init__(self, argdict):
        self.argdict = argdict
        self.fullmap = argdict["fullmap"]
        self.silent = argdict["silent"]
        self.verbose = argdict["verbose"]
        self.cert = argdict.get("cert","")
        self.index_node = argdict["index_node"]
        self.data_node = argdict["data_node"]
        self.data_roots = argdict["data_roots"]
        self.globus = argdict["globus"]
        self.replica = argdict["replica"]
        self.proj = argdict["proj"]
        self.json_file = argdict["json_file"]
        self.auth = argdict.get("auth",False)
        self.proj_config = argdict["user_project_config"]
        self.verify = argdict["verify"]
        self.mountpoints = argdict["mountpoints"]
        self.project = argdict["proj"]
        self.dry_run = argdict.get("dry_run", False)
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
        mkd = ESGPubMKDNonNC(self.data_node, self.index_node, self.replica, self.globus, self.data_roots, 
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
    
        if self.argdict.get("globus_index", False):
            up = ESGUpdateGlobus(self.argdict.get("index_UUID"), json_data[0]["data_node"], silent=self.silent, verbose=self.verbose, dry_run=self.dry_run)
        else:
            up = ESGUpdateSolr(self.index_node, silent=self.silent, verbose=self.verbose, verify=self.verify)
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
        print(f"VERBOSE: {self.verbose}")
        # TODO: support solr and Globus using the globus_index argument

        globuspub = self.argdict.get("globus_index", False)
        
        if globuspub:
            index_node = ""
        else:
            index_node = dataset_records[0]["index_node"]
        ip = ESGPubIndex(index_node=index_node, UUID=self.argdict["index_UUID"],  silent=self.silent, verbose=self.verbose, verify=self.verify, auth=self.auth, arch_cfg=arch_cfg, dry_run=self.dry_run)
            
        rc = True
        try:
            if globuspub:
                rc = ip.do_globus(dataset_records)
            else:
                rc = ip.do_publish(dataset_records)
        except Exception as ex:
            self.publog.exception("Failed to publish to index.")
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
