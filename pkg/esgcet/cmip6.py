import esgcet.mapfile as mp
import esgcet.mk_dataset as mkd
import esgcet.update as up
import esgcet.index_pub as ip
import esgcet.pid_cite_pub as pid
import esgcet.activity_check as act
import esgcet.args as args
import esgcet.esgmigrate as migrate
import os
import json
import sys
import tempfile
from cmip6_cv import PrePARE
from esgcet.settings import *
import configparser as cfg
from pathlib import Path
import esgcet.esgmigrate as em


class cmip6:

    scan_file = tempfile.NamedTemporaryFile()  # create a temporary file which is deleted afterward for autocurator
    scanfn = scan_file.name
    files = [scan_file, ]

    def check_files(self):
        pass

    def cleanup(self):
        self.scan_file.close()

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

    def mapfile(self, args):
        try:
            map_json_data = mp.run(args)
        except Exception as ex:
            print("Error with converting mapfile: " + str(ex), file=sys.stderr)
            self.cleanup()
            exit(1)
        return map_json_data

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

    def mk_dataset(self, args):
        args.append(self.scanfn)
        try:
            out_json_data = mkd.run(args)
        except Exception as ex:
            print("Error making dataset: " + str(ex), file=sys.stderr)
            self.cleanup()
            exit(1)
        return out_json_data

    def pid(self, args):
        try:
            new_json_data = pid.run(args)
            act.run(new_json_data)
        except Exception as ex:
            print("Error assigning pid or running activity check: " + str(ex))
            self.cleanup()
            exit(1)
        return new_json_data

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
