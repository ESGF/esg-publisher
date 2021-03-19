import esgcet.mapfile as mp
import esgcet.mkd_non_nc as mkd
import esgcet.update as up
import esgcet.index_pub as ip
import esgcet.pid_cite_pub as pid
import esgcet.activity_check as act
import esgcet.args as args
import os
import json
import sys
import tempfile
from cmip6_cv import PrePARE
from esgcet.settings import *
import configparser as cfg
from pathlib import Path
import esgcet.esgmigrate as em


class BasePublisher:

    def __init__(self, argdict):
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
        self.proj = ardict["proj"]
        self.json_file = argdict["json_file"]
        pass

    def cleanup(self):
        pass

    def mapfile(self, args):
        try:
            map_json_data = mp.run(args)
        except Exception as ex:
            print("Error with converting mapfile: " + str(ex), file=sys.stderr)
            self.cleanup()
            exit(1)
        return map_json_data

    def mk_dataset(self, map_json_data):
        try:
            out_json_data = mkd.run(map_json_data, self.scanfn, self.data_node, self.index_node, self.replica,
                                    self.data_roots, self.globus, self.dtn, self.silent, self.verbose, self.json_file)
        except Exception as ex:
            print("Error making dataset: " + str(ex), file=sys.stderr)
            self.cleanup()
            exit(1)
        return out_json_data

    def update(self, args):
        try:
            up.run(args)
        except Exception as ex:
            print("Error updating: " + str(ex), file=sys.stderr)
            self.cleanup()
            exit(1)

    def index_pub(self, args):
        try:
            ip.run(args)
        except Exception as ex:
            print("Error running index pub: " + str(ex), file=sys.stderr)
            self.cleanup()
            exit(1)

    def workflow(self):

        # step one: convert mapfile
        if not self.silent:
            print("Converting mapfile...")
        map_json_data = self.mapfile([self.fullmap, self.proj])
        if not self.silent:
            print("Done.")

        # step two: make dataset
        if not self.silent:
            print("Done.\nMaking dataset...")
        out_json_data = self.mk_dataset(map_json_data)

        if not self.silent:
            print("Done.\nUpdating...")
        self.update([out_json_data, self.index_node, self.cert, self.silent, self.verbose])

        if not silent:
            print("Done.\nRunning index pub...")
        self.index_pub([out_json_data, self.index_node, self.cert, self.silent, self.verbose])

        if not silent:
            print("Done.")

