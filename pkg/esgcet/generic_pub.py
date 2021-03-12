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


class BasePublisher:

    def __init__(self):
        pass

    def mapfile(self, args):
        try:
            map_json_data = mp.run(args)
        except Exception as ex:
            print("Error with converting mapfile: " + str(ex), file=sys.stderr)
            exit(1)
        return map_json_data

    def mk_dataset(self, args):
        try:
            out_json_data = mkd.run(args)
        except Exception as ex:
            print("Error making dataset: " + str(ex), file=sys.stderr)
            exit(1)
        return out_json_data

    def update(self, args):
        try:
            up.run(args)
        except Exception as ex:
            print("Error updating: " + str(ex), file=sys.stderr)
            exit(1)

    def index_pub(self, args):
        try:
            ip.run(args)
        except Exception as ex:
            print("Error running index pub: " + str(ex), file=sys.stderr)
            exit(1)

    def workflow(self, a):
        silent = a["silent"]

        # step one: convert mapfile
        if not silent:
            print("Converting mapfile...")
        map_json_data = self.mapfile([a["fullmap"], a["proj"]])
        if not silent:
            print("Done.")

        # step two: make dataset
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

        if not silent:
            print("Done.\nUpdating...")
        self.update([out_json_data, a["index_node"], a["cert"], a["silent"], a["verbose"]])

        if not silent:
            print("Done.\nRunning index pub...")
        self.index_pub([out_json_data, a["index_node"], a["cert"], a["silent"], a["verbose"]])

        if not silent:
            print("Done.")

