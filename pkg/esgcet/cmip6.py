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
from esgcet.generic_pub import BasePublisher
from esgcet.generic_netcdf import GenericPublisher


class cmip6(GenericPublisher):

    scan_file = tempfile.NamedTemporaryFile()  # create a temporary file which is deleted afterward for autocurator
    scanfn = scan_file.name
    files = [scan_file, ]

    def __init__(self, argdict):
        # maybe get args here
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
        self.proj = ardict["proj"]
        self.json_file = argdict["json_file"]
        self.pid_creds = argdict["pid_creds"]
        self.cmor_tables = argdict["cmor_tables"]
        pass
    
    def prepare_internal(self, json_map, cmor_tables):
        try:
            print("iterating through filenames for PrePARE (internal version)...")
            validator = PrePARE.PrePARE
            for info in json_map:
                filename = info[1]
                process = validator.checkCMIP6(cmor_tables)
                process.ControlVocab(filename)
        except Exception as ex:
            print("Error with PrePARE: " + str(ex), file=sys.stderr)
            self.cleanup()
            exit(1)

    def pid(self, args):
        try:
            new_json_data = pid.run(args)
            act.run(new_json_data)
        except Exception as ex:
            print("Error assigning pid or running activity check: " + str(ex))
            self.cleanup()
            exit(1)
        return new_json_data

    def workflow(self):

        # step one: convert mapfile
        if not self.silent:
            print("Converting mapfile...")
        map_json_data = self.mapfile([self.fullmap, self.proj])

        # step two: PrePARE
        self.prepare_internal(map_json_data, self.cmor_tables)

        # step three: autocurator
        if not self.silent:
            print("Done.\nRunning autocurator...")
        self.autocurator(map_json_data, self.autoc_command)

        # step four: make dataset
        if not self.silent:
            print("Done.\nMaking dataset...")
        out_json_data = self.mk_dataset(map_json_data)

        # step five: assign PID
        if not self.silent:
            print("Done. Assigning PID...")
        new_json_data = self.pid([out_json_data, self.data_node, self.pid_creds, self.silent, self.verbose])

        # step six: update record if exists
        if not self.silent:
            print("Done.\nUpdating...")
        self.update([new_json_data, self.index_node, self.cert, self.silent, self.verbose])

        # step seven: publish to database
        if not self.silent:
            print("Done.\nRunning index pub...")
        self.index_pub([new_json_data, self.index_node, self.cert, self.silent, self.verbose])

        if not self.silent:
            print("Done. Cleaning up.")
        self.cleanup()
