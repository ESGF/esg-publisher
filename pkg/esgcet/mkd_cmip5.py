import sys, json
from esgcet.mapfile import ESGPubMapConv
import configparser as cfg

from datetime import datetime, timedelta

from esgcet.settings import *
from pathlib import Path
from esgcet.mk_dataset import ESGPubMakeDataset

class ESGPubMKDCmip5(ESGPubMakeDataset):

    def init_project(self):

        self.DRS = DRS["cmip5"]
        self.project = "CMIP5"

    def __init__(self, data_node, index_node, replica, globus, data_roots, dtn, silent=False, verbose=False, user_project=None):
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
        self.variable_name = "variable_id"

        self.source_ids = ["CCSM-CAM", "CFSR", "CREATE-MRE2models", "CREATE-MRE3models", "CREATE-MREmodels", "GEOS-5",
                   "IFS-Cy31r2", "IFS-Cy41r2", "JRA-25", "JRA-55", "MITgcm", "MOM3", "MOM4", "MRICOMv3",
                   "NCEP-Global-Operational-Model", "NEMOv3", "NEMOv32-LIM2", "NEMOv34-LIM2", "ORAmodels", "ensda-v351"]

    def get_dataset(self, mapdata, scanobj):

        master_id, version = mapdata.split('#')

        parts = master_id.split('.')

        self.init_project()

        facets = self.DRS  # depends on Init_project to initialize

        assert(facets)
        self.variable_name = list(scanobj["variables"].keys())[0]

        for i, f in enumerate(facets):
            self.dataset[f] = parts[i]

#        self.global_attributes(projkey, scandata)
#        self.global_attr_mapped(projkey, scandata)
        self.const_attr()
        self.assign_dset_values(self.project, master_id, version)

