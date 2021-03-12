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
from generic_pub import BasePublisher


class GenericPublisher(BasePublisher):

    scan_file = tempfile.NamedTemporaryFile()  # create a temporary file which is deleted afterward for autocurator
    scanfn = scan_file.name

    def __init__(self):
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

    def workflow(self, a):

        silent = a["silent"]

        # step one: convert mapfile
        if not silent:
            print("Converting mapfile...")
        map_json_data = self.mapfile([a["fullmap"], a["proj"]])

        # step two: autocurator
        if not silent:
            print("Done.\nRunning autocurator...")
        self.autocurator(map_json_data, a["autoc_command"])

        # step three: make dataset
        if not silent:
            print("Done.\nMaking dataset...")
        if a["third_arg_mkd"]:
            out_json_data = self.mk_dataset(
                [map_json_data, a["data_node"], a["index_node"], a["replica"], a["data_roots"], a["globus"], a["dtn"],
                 a["silent"], a["verbose"], a["json_file"]])
        else:
            out_json_data = self.mk_dataset(
                [map_json_data, a["data_node"], a["index_node"], a["replica"], a["data_roots"], a["globus"], a["dtn"],
                 a["silent"], a["verbose"]])

        # step four: update record if exists
        if not silent:
            print("Done.\nUpdating...")
        self.update([out_json_data, a["index_node"], a["cert"], a["silent"], a["verbose"]])

        # step five: publish to database
        if not silent:
            print("Done.\nRunning index pub...")
        self.index_pub([out_json_data, a["index_node"], a["cert"], a["silent"], a["verbose"]])

        if not silent:
            print("Done. Cleaning up.")
        self.cleanup()
