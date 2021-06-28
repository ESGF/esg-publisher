import sys, json
from esgcet.mapfile import ESGPubMapConv
import configparser as cfg

from datetime import datetime, timedelta

from esgcet.settings import *
from pathlib import Path
from esgcet.mk_dataset import ESGPubMakeDataset
from esgcet.mkd_create_ip import ESGPubMKDCreateIP
import esgcet.logger as logger

log = logger.Logger()


class ESGPubMKDCmip5(ESGPubMKDCreateIP):

    def init_project(self):

        self.DRS = DRS["cmip5"]
        self.project = "cmip5"

    def __init__(self, data_node, index_node, replica, globus, data_roots, dtn, silent=False, verbose=False, limit_exceeded=False, user_project=None):
        self.silent = silent
        self.verbose = verbose
        self.data_roots = data_roots
        self.globus = globus
        self.data_node = data_node
        self.index_node = index_node
        self.replica = replica
        self.dtn = dtn

        self.mapconv = ESGPubMapConv("")
        self.dataset = {}
        self.project = None
        self.user_project = user_project
        self.DRS = None
        self.CONST_ATTR = None
        self.variable_name = "variable"
        self.limit_exceeded = limit_exceeded
        self.publog = log.return_logger('Make Dataset CMIP5', self.silent, self.verbose)

    def get_dataset(self, mapdata, scanobj):

        master_id, version = mapdata.split('#')

        parts = master_id.split('.')

        self.init_project()

        facets = self.DRS  # depends on Init_project to initialize

        assert(facets)
        for var in list(scanobj["variables"].keys()):
            if "bnds" not in var and "_" not in var and "lon" not in var and "lat" not in var:
                self.variable = var
        for i, f in enumerate(facets):
            self.dataset[f] = parts[i]
        self.dataset[self.variable_name] = self.variable

#        self.global_attributes(projkey, scandata)
#        self.global_attr_mapped(projkey, scandata)
        self.const_attr()
        self.assign_dset_values(self.project, master_id, version)

