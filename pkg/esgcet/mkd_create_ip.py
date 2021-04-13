import sys, json
from esgcet.mapfile import ESGPubMapConv
import configparser as cfg

from datetime import datetime, timedelta

from esgcet.settings import *
from pathlib import Path
from esgcet.mk_dataset import ESGPubMakeDataset

class ESGPubMKDCreateIP(ESGPubMakeDataset):

    def init_project(self, s):

        if s in self.source_ids:
            self.DRS = DRS["CREATE-IP-src"]
        else:
            self.DRS = DRS["CREATE-IP-exp"]

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
        exp_src = parts[3]

        projkey = parts[0]
        scandata = scanobj['dataset']

        if self.project:
            projkey = self.project
        self.init_project(exp_src)

        facets = self.DRS  # depends on Init_project to initialize

        assert(facets)
        self.variable_name = list(scanobj["variables"].keys())[0]

        for i, f in enumerate(facets):
            if f in scandata:
                ga_val = scandata[f]
                if not parts[i] == ga_val:
                    if f == "source_id" and ga_val not in self.source_ids:
                        self.dataset["experiment"] = ga_val
                    elif f == "experiment" and ga_val in self.source_ids:
                        self.dataset["source_id"] = ga_val
                    elif not self.silent:
                        self.eprint("WARNING: {} does not agree!".format(f))
                        self.eprint(ga_val)
            self.dataset[f] = parts[i]

        self.global_attributes(projkey, scandata)
        self.global_attr_mapped(projkey, scandata)
        self.const_attr()
        self.assign_dset_values(projkey, master_id, version)

