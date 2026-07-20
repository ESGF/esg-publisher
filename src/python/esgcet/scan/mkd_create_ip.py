import sys, json
from esgcet.mapfile import ESGPubMapConv
import configparser as cfg

from datetime import datetime, timedelta

from esgcet.settings import *
from pathlib import Path
from esgcet.mk_dataset import ESGPubMakeDataset
import esgcet.logger as logger

log = logger.ESGPubLogger()


class ESGPubMKDCreateIP(ESGPubMakeDataset):

    def init_project(self, s, l):

        self.project = "CREATE-IP"
        if s in self.source_ids:
            self.DRS = DRS["create-ip-src"]
        elif l == 7:
            self.DRS = DRS["create-ip-model"]
        elif l == 8:
            self.DRS = DRS["create-ip-var"]
        else:
            self.DRS = DRS["create-ip-exp"]

    def __init__(self, *args, **kwargs):
        super(ESGPubMakeDataset,self).__init__(args, kwargs)
        self.models = ["CCSM-CAM", "CFSR", "CREATE-MRE2models", "CREATE-MRE3models", "CREATE-MREmodels", "GEOS-5",
                   "IFS-Cy31r2", "IFS-Cy41r2", "JRA-25", "JRA-55", "MITgcm", "MOM3", "MOM4", "MRICOMv3",
                   "NCEP-Global-Operational-Model", "NEMOv3", "NEMOv32-LIM2", "NEMOv34-LIM2", "ORAmodels", "ensda-v351"]
        self.source_ids = [ "20CRv2c", "C-GLORSv5", "CERA-20C", "CFSR", "CREATE-MRE", "ECDAv31", "ERA-Interim", "ERA40-CRUTS3-10", "ERA5", "ERAInterim-CRUTS3-10", "GECCO2", "GODAS", "JRA-25", "JRA-55," "JRA-55-mdl-iso", "MERRA", "MERRA-CRUTS3-10", "MERRA2", "MERRA2-ASM", "MOVE-G2i", "MRE2ensemble", "NCEP-NCAR-CRUTS3-10", "ORAP5", "ORAS4", "ORAensemble"]
        self.publog = log.return_logger('Make Dataset CREATE-IP', self.silent, self.verbose)

    def get_dataset(self, mapdata, scanobj):

        master_id, version = mapdata.split('#')

        parts = master_id.split('.')
        exp_src = parts[3]

        projkey = parts[0]
        scandata = scanobj['dataset']

        if self.project:
            projkey = self.project
        self.init_project(exp_src, len(parts))

        facets = self.DRS  # depends on Init_project to initialize

        if not facets:
            raise RuntimeError()
        for var in list(scanobj["variables"].keys()):
            if "bnds" not in var and "_" not in var and "lon" not in var and "lat" not in var:
                self.variable = var

        for i, f in enumerate(facets):
            if f in scandata:
                ga_val = scandata[f]
                if not parts[i] == ga_val:
                    if f == "source_id" and ga_val not in self.source_ids:
                        self.dataset["experiment"] = ga_val
                    elif f == "experiment" and ga_val in self.source_ids:
                        self.dataset["source_id"] = ga_val
                    self.publog.warning("{} does not agree!\n".format(f) + ga_val)
            self.dataset[f] = parts[i]
        self.dataset[self.variable_name] = self.variable

        self.global_attributes(projkey, scandata)
        self.global_attr_mapped(projkey, scandata)
        self.const_attr()
        self.assign_dset_values(projkey, master_id, version)

    def aggregate_datasets(self, datasets, limit=False):
        vids = []
        v_long_names = []
        cf_std_names = []
        v_units = []
        last_dset = None
        last_rec = None
        for data in datasets:
            if data[0]["type"] == "Dataset":
                idx = 0
            elif data[-1]["type"] == "Dataset":
                idx = -1
            else:
                self.publog.error("No dataset record found. Exiting")
                exit(-4)
            dataset = data[idx]
            if self.variable_name in dataset and dataset[self.variable_name] not in vids:
                vids.append(dataset[self.variable_name])
            if "variable_long_name" in dataset and dataset["variable_long_name"] not in v_long_names:
                v_long_names.append(dataset["variable_long_name"])
            if "cf_standard_name" in dataset and dataset["cf_standard_name"] not in cf_std_names:
                cf_std_names.append(dataset["cf_standard_name"])
            if "variable_units" in dataset and dataset["variable_units"] not in v_units:
                v_units.append(dataset["variable_units"])
            last_rec = data
            last_dset = dataset
        if limit:
            last_dset[self.variable_name] = "Multiple"
            last_dset["variable_long_name"] = "Multiple"
            last_dset["cf_standard_name"] = "Multiple"
            last_dset["variable_units"] = "Multiple"
        else:
            last_dset[self.variable_name] = vids
            last_dset["variable_long_name"] = v_long_names
            last_dset["cf_standard_name"] = cf_std_names
            last_dset["variable_units"] = v_units
        last_rec[idx] = last_dset
        self.publog.debug("Aggregate record:\n" + json.dumps(last_dset, indent=4))
        return last_rec
