import esgcet.mapfile as mp
import esgcet.mkd_non_nc as mkd
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


class GenericPublisher:

    scan_file = tempfile.NamedTemporaryFile()  # create a temporary file which is deleted afterward for autocurator
    scanfn = scan_file.name

    def cleanup(self):
        self.scan_file.close()
        exit(1)

    def __init__(self):
        pass

    def mapfile(self, args):
        try:
            map_json_data = mp.run(args)
        except Exception as ex:
            print("Error with converting mapfile: " + str(ex), file=sys.stderr)
            exit(1)
        return map_json_data

    def autocurator(self, map_json_data):
        datafile = map_json_data[0][1]
        destpath = os.path.dirname(datafile)
        scanpath = self.scanfn

        autstr = 'autocurator --out_pretty --out_json {} --files "{}/*.nc"'
        os.system(autstr.format(scanpath, destpath))

    def mk_dataset(self, args):
        try:
            out_json_data = mkd.run(args)
        except Exception as ex:
            print("Error making dataset: " + str(ex), file=sys.stderr)
            return None
        return out_json_data

    def update(self, args):
        try:
            up.run(args)
        except Exception as ex:
            print("Error updating: " + str(ex), file=sys.stderr)
            return None
        return 0

    def index_pub(self, args):
        try:
            ip.run(args)
        except Exception as ex:
            print("Error running index pub: " + str(ex), file=sys.stderr)
            return None
        return 0

    def workflow(self, a):

        # step one: convert mapfile
        if not silent:
            print("Converting mapfile...")
        map_json_data = mapfile([a["fullmap"], a["proj"]])
        if not silent:
            print("Done.")

        # step three: run autocurator
        if not silent:
            print("Running autocurator...")
        autocurator(map_json_data, a["autoc_command"])

        # step four: make dataset
        if not silent:
            print("Done.\nMaking dataset...")
        if third_arg_mkd:
            out_json_data = mk_dataset(
                [map_json_data, a["data_node"], a["index_node"], a["replica"], a["data_roots"], a["globus"], a["dtn"], a["silent"], a["verbose"],
                 a["json_file"]])
        else:
            out_json_data = mk_dataset(
                [map_json_data, a["data_node"], a["index_node"], a["replica"], a["data_roots"], a["globus"], a["dtn"], a["silent"], a["verbose"]])

        if out_json_data is None:
            cleanup()

        if not silent:
            print("Done.\nUpdating...")
        rc = update([out_json_data, a["index_node"], a["cert"], a["silent"], a["verbose"]])
        if rc is None:
            cleanup()

        if not silent:
            print("Done.\nRunning index pub...")
        rc = index_pub([out_json_data, a["index_node"], a["cert"], a["silent"], a["verbose"]])
        if rc is None:
            cleanup()

        if not silent:
            print("Done. Cleaning up.")
        cleanup()

