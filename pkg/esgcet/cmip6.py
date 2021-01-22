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
            exit(1)

    def mapfile(self, args):
        try:
            map_json_data = mp.run(args)
        except Exception as ex:
            print("Error with converting mapfile: " + str(ex), file=sys.stderr)
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
            exit(os.WEXITSTATUS(stat))

    def mk_dataset(self, args):
        args.append(self.scanfn)
        try:
            out_json_data = mkd.run(args)
        except Exception as ex:
            print("Error making dataset: " + str(ex), file=sys.stderr)
            return None
        return out_json_data

    def pid(self, args):
        try:
            new_json_data = pid.run(args)
            act.run(new_json_data)
        except Exception as ex:
            print("Error assigning pid or running activity check: " + str(ex))
            return None
        return new_json_data

    def update(self, args):
        try:
            up.run(args)
        except Exception as ex:
            print("Error updating: " + str(ex), file=sys.stderr)
            return None
        return "all good"

    def index_pub(self, args):
        try:
            ip.run(args)
        except Exception as ex:
            print("Error running index pub: " + str(ex), file=sys.stderr)
            return None
        return "all good"

    def get_args(self, args):

        # setup and variables
        fullmap = args[0]
        third_arg_mkd = args[1]
        silent = args[2]
        verbose = args[3]
        cert = args[4]
        autoc_cmd = args[5]
        index_node = args[6]
        data_node = args[7]
        data_roots = args[8]
        globus = args[9]
        dtn = args[10]
        replica = args[11]
        if third_arg_mkd:
            json_file = args[12]
            cmor_tables = args[13]
        else:
            cmor_tables = args[12]


