import sys, json, os
from esgcet.mapfile import ESGPubMapConv
import configparser as cfg
from esgcet.mk_dataset import ESGPubMakeDataset
from datetime import datetime, timedelta
from esgcet.settings import *
from pathlib import Path
import esgcet.logger as logger

log = logger.ESGPubLogger()


class ESGPubMKDNonNC(ESGPubMakeDataset):

    def __init__(self, data_node, index_node, replica, globus, data_roots,  silent=False, verbose=False, limit_exceeded=False, user_project=None):
        
        super().__init__(data_node, index_node, replica, globus, data_roots,  None, silent, verbose, limit_exceeded,
                         user_project)
        self.publog = log.return_logger('Make Non-NetCDF Dataset', silent, verbose)

    def get_dataset(self, mapdata):
        master_id, version = mapdata.split('#')

        parts = master_id.split('.')
        projkey = parts[0]
        if self.project:
            projkey = self.project
        self.init_project(projkey)

        facets = self.DRS

        for i, f in enumerate(facets):
            self.dataset[f] = parts[i]

        #    SPLIT_FACET = {'E3SM': {'delim': '_', 'facet': 'grid_resolution', 0: 'atmos_', 2: 'ocean_'}}
        if projkey in SPLIT_FACET:
            splitinfo = SPLIT_FACET[projkey]
            splitkey = splitinfo['facet']
            orgval = self.dataset[splitkey]
            valsplt = orgval.split(splitinfo['delim'])
            for idxkey in splitinfo:
                if type(idxkey) is int:
                    keyprefix = splitinfo[idxkey]
                    self.dataset[keyprefix + splitkey] = valsplt[idxkey]

        self.const_attr()
        self.assign_dset_values(master_id, version)
        if not 'project' in self.dataset:
            self.dataset['project'] = projkey
        
    def iterate_files(self, mapdata):
        ret = []
        sz = 0
        last_file = None

        for maprec in mapdata:
            fullpath = maprec['file']
            file_rec = self.get_file(maprec, {})
            last_file = file_rec
            sz += file_rec["size"]
            ret.append(file_rec)

        access = [x.split("|")[2] for x in last_file["url"]]

        return ret, sz, access

    def get_records(self, mapdata, xattrfn=None, user_project=None):
        self.user_project = user_project

        if isinstance(mapdata, str):
            mapobj = json.load(open(mapdata))
        else:
            mapobj = mapdata

        self.get_dataset(mapobj[0][0])

        self.dataset["number_of_files"] = len(mapobj)  # place this better
        project = self.dataset['project']

        self.proc_xattr(xattrfn)
        self.publog.debug("Record:\n" + json.dumps(self.dataset, indent=4))
        print()

        self.mapconv.set_map_arr(mapobj)
        mapdict = self.mapconv.parse_map_arr()
        self.publog.debug('Mapfile dictionary:\n' + json.dumps(mapdict, indent=4))
        print()

        ret, sz, access = self.iterate_files(mapdict)

        self.dataset["size"] = sz
        self.dataset["access"] = access
        ret.append(self.dataset)
        return ret
