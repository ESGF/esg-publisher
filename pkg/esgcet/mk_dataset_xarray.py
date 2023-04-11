import xarray, netCDF4

from esgcet.mk_dataset import ESGPubMakeDataset

class ESGPubMakeXArrayDataset(ESGPubMakeDataset):

    def __init__(self, *args):
        super().__init__(*args)

    def get_attrs_dict(self, scanobj):
        return scanobj.attrs

    def get_scanfile_dict(self, scandata, mapdata):
        ret = {}
        for rec in mapdata:
            fn = rec['file']
            print(f"TEST: {fn}")
            ds = netCDF4.Dataset(fn)
            ret[fn] = {"tracking_id": ds.tracking_id}
        return ret
    
    def get_variables(self, scanobj):
        res = {}
        for x in scanobj.variables:
            res[x] = scanobj.variables[x].attrs
        return res
    
    def get_variable_list(self, variable):
        return [x for x in variable]

    def _get_time_str(self, timeval):
        if type(timeval.item()) is int:
            x = str(timeval)
            idx = x.index('.')
            return x[:idx] + 'Z'
        else:
            return timeval.item().isoformat() + "Z"

    def set_bounds(self, record, scanobj):

        geo_units = []
        # latitude
        if "latitude" in scanobj.coords:
            lat = scanobj.coords["latitude"]
            record["north_degrees"] = lat[-1].values.item()
            record["south_degrees"] = lat[0].values.item()
            geo_units.append(lat.units)
        # longitude
        if "longitude" in scanobj.coords:
            lon = scanobj.coords["longitude"]
            record["east_degrees"] = lon[-1].values.item()
            record["west_degrees"] = lon[0].values.item()
            geo_units.append(lon.units)
        # time
        if "time" in scanobj.coords:
            ti = scanobj.coords["time"]
            record["datetime_start"] = self._get_time_str(ti[0].values)
            record["datetime_end"] = self._get_time_str(ti[-1].values)
        # plev
        if "plev" in scanobj.coords:
            plev = scanobj.coords["plev"]
            record["height_top"] = plev[0].values.item() 
            record["height_bottom"] = plev[-1].values.item() 
            geo_units.append(plev.units)
        if len(geo_units) > 0:
            record["geo_units"] = geo_units
            