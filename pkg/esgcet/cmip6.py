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

    def __init__(self):
        # maybe get args here
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

    def workflow(self, a):
        silent = a["silent"]

        # step one: convert mapfile
        if not silent:
            print("Converting mapfile...")
        map_json_data = self.mapfile([a["fullmap"], a["proj"]])

        # step two: PrePARE
        self.prepare_internal(map_json_data, a["cmor_tables"])

        # step three: autocurator
        if not silent:
            print("Done.\nRunning autocurator...")
        self.autocurator(map_json_data, a["autoc_command"])

        # step four: make dataset
        if not silent:
            print("Done.\nMaking dataset...")
        if a["json_file"]:
            out_json_data = self.mk_dataset(
                [map_json_data, a["data_node"], a["index_node"], a["replica"], a["data_roots"], a["globus"], a["dtn"],
                 a["silent"], a["verbose"], a["json_file"]])
        else:
            out_json_data = self.mk_dataset(
                [map_json_data, a["data_node"], a["index_node"], a["replica"], a["data_roots"], a["globus"], a["dtn"],
                 a["silent"], a["verbose"]])

        # step five: assign PID
        if not silent:
            print("Done. Assigning PID...")
        new_json_data = self.pid([out_json_data, a["data_node"], a["pid_creds"], silent, a["verbose"]])

        # step six: update record if exists
        if not silent:
            print("Done.\nUpdating...")
        self.update([new_json_data, a["index_node"], a["cert"], a["silent"], a["verbose"]])

        # step seven: publish to database
        if not silent:
            print("Done.\nRunning index pub...")
        self.index_pub([new_json_data, a["index_node"], a["cert"], a["silent"], a["verbose"]])

        if not silent:
            print("Done. Cleaning up.")
        self.cleanup()
