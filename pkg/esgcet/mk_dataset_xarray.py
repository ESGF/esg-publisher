import xarray, netcdf4

from mk_dataset import ESGPubMakeDataset

class ESGPubMakeXArrayDataset(ESGPubMakeDataset):

    def __init__(self, *args):
        super().__init__(args)

    def get_attrs_dict(self, scanobj):
        return scanobj.attrs

    def get_scanfile_dict(self, fn_list):
        ret = {}

        for fn in fn_list:
            ds = netcdf4.Dataset(fn)

            ret[fn] = {"tracking_id": ds.tracking_id}
        return ret
    
    def set_bounds(self, record, scanobj):

        geo_units = []
        # latitude
        if "latitude" in scanobj.coords:
            lat = scanobj.coords["latitude"]
            record["north_degrees"] = lat[-1].values.item()
            record["south_degrees"] = lat[0].values.item()
        # longitude
        if "longitude" in scanobj.coords:
            lon = scanobj.coords["longitude"]
            record["east_degrees"] = lon[-1].values.item()
            record["west_degrees"] = lon[0].values.item()
        # time
        if "time" in scanobj.coords:
            ti = scanobj.coords["time"]
            record["datetime_start"] = ti[0].values.item().isoformat() 
            record["datetime_end"] = ti[-1].values.item().isoformat()
        # plev
        if "plev" in scanobj.coords:
            plev = scanobj.coords["plev"]
        if len(geo_units) > 0:
            record["geo_units"] = geo_units
        

