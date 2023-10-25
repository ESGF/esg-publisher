import sys, json
from esgcet.mapfile import ESGPubMapConv
import configparser as cfg

from datetime import datetime, timedelta

from esgcet.settings import *
from pathlib import Path
from esgcet.mk_dataset import ESGPubMakeDataset
from esgcet.mkd_create_ip import ESGPubMKDCreateIP
import esgcet.logger as logger

log = logger.ESGPubLogger()


class ESGPubMKDCmip5(ESGPubMKDCreateIP):

    def init_project(self):

        self.DRS = DRS["cmip5"]
        self.project = "cmip5"

    def __init__(self, *args, **kwargs):
        super(ESGPubMKDCmip5, self).__init__(args, kwargs)

        self.variable_name = "variable"
        self.publog = log.return_logger('Make Dataset CMIP5', self.silent, self.verbose)

    def get_dataset(self, mapdata, scanobj):

        master_id, version = mapdata.split('#')

        parts = master_id.split('.')

        self.init_project()

        facets = self.DRS  # depends on Init_project to initialize

        if not facets:
            raise RuntimeError()
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

