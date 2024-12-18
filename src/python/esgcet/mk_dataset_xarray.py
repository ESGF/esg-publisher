import xarray, netCDF4
from esgcet.handler_base import ESGPubHandlerBase
import os.path
import numpy as np

class ESGPubXArrayHandler(ESGPubHandlerBase):

    @staticmethod
    def xarray_load(map_data):
        datafile = map_data[0][1]
        destpath = os.path.dirname(datafile)

        filespec = f"{destpath}/*.nc"
        res = xarray.open_mfdataset(filespec, use_cftime=True)
        return res

    def get_attrs_dict(self, scanobj):
        return scanobj.attrs

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
            return timeval.item().isoformat(timespec="seconds") + "Z"
        
    def _get_min_max_bounds(self, latlon):
        bigarr = latlon[0] + latlon[-1]
        return float(np.min(bigarr)), float(np.max(bigarr))
    
    def set_bounds(self, record, scanobj):

        geo_units = []
        # latitude
        if "lat" in scanobj.coords:
            lat = scanobj.coords["lat"]
            if len(lat) > 0:
                record["north_degrees"] = lat.values.max()
                record["south_degrees"] = lat.values.min()
            else:
                self.publog.warn("'lat' found but len 0")          
        elif "latitude" in scanobj.coords:
            lat = scanobj.coords["latitude"]
            if len(lat) > 0:
                if isinstance(lat[0].values, (list, np.ndarray)):
                    min, max = self._get_min_max_bounds(lat)
                    record["north_degrees"] = min
                    record["south_degrees"] = max

                else:    
                    record["north_degrees"] = lat[-1].values.item()
                    record["south_degrees"] = lat[0].values.item()
                geo_units.append(lat.units)
            else:
                self.publog.warn("Latitude found but len 0")
        else:
            self.publog.warn("Lat/Latitude not found")
        # longitude
        if "lon" in scanobj.coords:
            lon = scanobj.coords["lon"]
            if len(lon) > 0:
                record["east_degrees"] = lon.values.max()
                record["west_degrees"] = lon.values.min()
            else:
                self.publog.warn("'lon' found but len 0")          
        elif "longitude" in scanobj.coords:
            lon = scanobj.coords["longitude"]
            if len(lon) > 0:
                if isinstance(lon[0].values, (list, np.ndarray)):
                    min, max = self._get_min_max_bounds(lon)   
                    record["east_degrees"] = min
                    record["west_degrees"] = max
                else:
                    record["east_degrees"] = lon[-1].values.item()
                    record["west_degrees"] = lon[0].values.item()
                geo_units.append(lon.units)
            else:
                self.publog.warn("Latitude found but len 0")
                # time
        else:
            self.publog.warn("Lon/Longitude not found")
        if "time" in scanobj.coords:
            ti = scanobj.coords["time"]
            record["datetime_start"] = self._get_time_str(ti[0].values)
            record["datetime_end"] = self._get_time_str(ti[-1].values)
        # plev
        if "plev" in scanobj.coords:
            try:
                plev = scanobj.coords["plev"]
                record["height_top"] = plev[0].values.item() 
                record["height_bottom"] = plev[-1].values.item() 
                geo_units.append(plev.units)
            except:
                self.publog.warn("plev found but not an expected type")
        if len(geo_units) > 0:
            record["geo_units"] = geo_units
            
