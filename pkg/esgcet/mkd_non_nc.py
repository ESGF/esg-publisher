import sys, json, os
from esgcet.mapfile import *
import configparser as cfg
from esgcet.mk_dataset import MakeDataset
from datetime import datetime, timedelta
from esgcet.settings import *
from pathlib import Path


class MKDNonNC(MakeDataset):

    def get_dataset(self, mapdata, data_node, index_node, replica):
        master_id, version = mapdata.split('#')

        parts = master_id.split('.')
        projkey = parts[0]

        facets = DRS[projkey]
        d = {}

        for i, f in enumerate(facets):
            d[f] = parts[i]

        #    SPLIT_FACET = {'E3SM': {'delim': '_', 'facet': 'grid_resolution', 0: 'atmos_', 2: 'ocean_'}}
        if projkey in SPLIT_FACET:
            splitinfo = SPLIT_FACET[projkey]
            splitkey = splitinfo['facet']
            orgval = d[splitkey]
            valsplt = orgval.split(splitinfo['delim'])
            for idxkey in splitinfo:
                if type(idxkey) is int:
                    keyprefix = splitinfo[idxkey]
                    d[keyprefix + splitkey] = valsplt[idxkey]
        # handle Global attributes if defined for the project
        if projkey in CONST_ATTR:
            for facetkey in CONST_ATTR[projkey]:
                d[facetkey] = CONST_ATTR[projkey][facetkey]

        d['data_node'] = data_node
        d['index_node'] = index_node
        DRSlen = len(DRS[projkey])
        d['master_id'] = master_id
        d['instance_id'] = master_id + '.v' + version
        d['id'] = d['instance_id'] + '|' + d['data_node']
        if 'title' in d:
            d['short_description'] = d['title']
        d['title'] = d['master_id']
        d['replica'] = replica
        d['latest'] = 'true'
        d['type'] = 'Dataset'
        if projkey == "E3SM":
            d['project'] = projkey.lower()
        else:
            d['project'] = projkey

        d['version'] = version

        fmat_list = ['%({})s'.format(x) for x in DRS[projkey]]

        d['dataset_id_template_'] = '.'.join(fmat_list)
        d['directory_format_template_'] = '%(root)s/{}/%(version)s'.format('/'.join(fmat_list))

        return d

    def iterate_files(self, dataset_rec, mapdata):
        ret = []
        sz = 0
        last_file = None

        for maprec in mapdata:
            fullpath = maprec['file']
            file_rec = self.get_file(dataset_rec, maprec, {})
            last_file = file_rec
            sz += file_rec["size"]
            ret.append(file_rec)

        access = [x.split("|")[2] for x in last_file["url"]]

        return ret, sz, access

    def get_records(self, mapdata, data_node, index_node, replica, xattrfn=None):
        if isinstance(mapdata, str):
            mapobj = json.load(open(mapdata))
        else:
            mapobj = mapdata

        rec = self.get_dataset(mapobj[0][0], data_node, index_node, replica)

        if not rec:
            return None

        rec["number_of_files"] = len(mapobj)  # place this better

        if xattrfn:
            xattrobj = json.load(open(xattrfn))
        else:
            xattrobj = {}

        if self.verbose:
            eprint("rec = ")
            eprint(rec)
            eprint()
        for key in xattrobj:
            rec[key] = xattrobj[key]

        assert ('project' in rec)
        project = rec['project']

        mapdict = parse_map_arr(mapobj)
        if self.verbose:
            print('mapdict = ')
            print(mapdict)
            print()

        ret, sz, access = self.iterate_files(rec, mapdict)

        rec["size"] = sz
        rec["access"] = access
        ret.append(rec)
        return ret
