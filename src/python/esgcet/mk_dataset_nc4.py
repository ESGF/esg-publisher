import netCDF4
from esgcet.handler_base import ESGPubHandlerBase
import os.path
import numpy as np

class ESGPubNC4Handler(ESGPubHandlerBase):

    @staticmethod
    def nc4_load(map_data):
        datafile = map_data[0][1]
        destpath = os.path.dirname(datafile)
        flst = os.listdir(destpath)

        if len(flst) == 0:
            raise RuntimeError("Directory empty!")
        fn = f"{destpath}/{flst[0]}"
        ds = netCDF4.Dataset(fn)

        return ds

    def get_attrs_dict(self, scanobj):
        return scanobj.__dict__

    def get_scanfile_dict(self, scandata, mapdata):
        ret = {}
        for rec in mapdata:
            fn = rec['file']
            ds = netCDF4.Dataset(fn)
            try:
                ret[fn] = {"tracking_id": ds.tracking_id}
            except:
                self.publog.warn("Tracking ID not found")
                ret[fn] = {}
        return ret
    
    def get_variables(self, scanobj):
        res = {}
        return res
    
    def get_variable_list(self, variable):
        return []

    
    def set_bounds(self, record, scanobj):

        pass

