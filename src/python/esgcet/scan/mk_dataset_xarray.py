import xarray, netCDF4
from esgcet.scan.handler_base import ESGPubHandlerBase
import os.path
import numpy as np
import re

class ESGPubXArrayHandler(ESGPubHandlerBase):

    @staticmethod
    def xarray_load(map_data):
        filenames = [row[1] for row in map_data]
        if len(filenames) > 1:

            # optimise: only need first and last file (in sorted order) to correctly evaluate
            # data time range, if filenames all follow a common pattern but with a numeric
            # date string - see if they all have the same normalised filename (after
            # replacing actual digits with <DIGIT>)
            #
            # This saves time and memory for long timeseries.
            #
            # The assets dictionary is populated directly from the mapfile data, and is
            # not affected by this.

            if len({re.sub(r"\d", "<DIGIT>", filename)
                    for filename in filenames}) == 1:
                # use min() and max() rather than [0] and [-1] because esgmapfile might not
                # have created the lines in sorted order
                filenames = [min(filenames), max(filenames)]

        time_coder = xarray.coders.CFDatetimeCoder(use_cftime=True)
        res = xarray.open_mfdataset(
            filenames,
            decode_times=time_coder,
            data_vars='all'
        )
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
        if hasattr(timeval, "item"):
            timeval = timeval.item()
        if type(timeval) is float or type(timeval) is int:
            x = str(timeval)
            idx = x.index('.')
            return x[:idx] + 'Z'
        else:
            return timeval.isoformat(timespec="seconds") + "Z"


    def _get_item(self, obj):
        if hasattr(obj, "compute"):
            obj = obj.compute()
        return obj.item()


    def _undo_time_broadcast(self, var):
        dims = var.dims
        if dims and dims[0] == "time":
            return var[0]
        else:
            return var


    def _get_longitude_range(self, longitudes,
                             global_threshold=350.):
        """
        Given a scatter of longitude points, returns the west and east extremes.

        This is done by sorting them and locating the biggest "gap" (arc of circle),
        but subject to a threshold that if the range spanned is close to 360,
        then treating it as global.
        """
        x = np.asarray(longitudes, dtype=float).ravel()
        x = x[np.isfinite(x)]

        if len(x) == 0:
            raise ValueError("No finite longitude values")

        # Identify the convention used by the input data.
        if np.all((x >= 0) & (x <= 360)):
            globe_start = 0.
        else:
            globe_start = -180.

        x = np.sort(x)

        # If necessary, normalise
        if x[0] < 0 or x[-1] > 360 or x[-1] - x[0] >= 360:
            x = x % 360
            x = np.sort(x)

        if len(x) == 1 or x[0] == x[-1]:
            return x[0], x[0]

        wrap_gap = (x[0] - x[-1]) % 360
        gaps = np.append(np.diff(x) % 360, wrap_gap)

        # largest empty arc
        i = np.argmax(gaps)
        largest_gap = gaps[i]
        span = 360 - largest_gap

        if span >= global_threshold:
            # virtually global per heuristic, so return global range
            #  (-180,180 or 0,360 as per the data)
            return globe_start, globe_start + 360

        start = x[(i + 1) % len(x)]
        end = x[i]
        lon_min = (start - globe_start) % 360 + globe_start
        lon_max = (end - globe_start) % 360 + globe_start
        if lon_max == globe_start:
            lon_max += 360
        return lon_min, lon_max


    def _min_and_max(self, a, b):
        if a < b:
            return a, b
        else:
            return b, a


    def _get_min_max_bounds(self, scanobj, var):

        if var.name not in scanobj.coords:
            raise ValueError("_get_min_max_bounds called on "
                             f"non-coordinate variable {var.name}")
        
        stdname = var.attrs.get("standard_name")

        # use the bounds variable instead if available, so that the range
        # that is returned will include the bounds and not just the central value
        bounds_var_name = var.attrs.get("bounds")
        if (bounds_var_name is not None
            and bounds_var_name in scanobj.variables):
            var = scanobj[bounds_var_name]
            self.publog.debug(f"{stdname} has bounds var")
            using_bounds = True
        else:
            self.publog.debug(f"{stdname} no bounds var")
            using_bounds = False

        # undo any broadcasting in time that xarray may have done
        # for non-time variable (seems to do this for vertices array
        # of original shape (ny, nx, 4) when opening multiple files)
        if stdname != "time":
            var = self._undo_time_broadcast(var)

        # Get the min, max range in the same way both for a 1d coordinate axis
        # and also for an irregular grid.  With a 1d axis, in fact we only
        # need to inspect a couple of elements, but the extra work here is not
        # very expensive, and the code is simpler.
        shape = var.shape

        if stdname == "longitude":
            # For longitude, always use the same algorithm, regardless of whether it is
            # 1d or 2d coord var.  (For 1d, we might need to unnecessarily inspect *all*
            # the longitudes, but it won't be expensive, and it simplifies some other
            # complexity.)
            minmax = self._get_longitude_range(var.values)

        else:
            # Otherwise, try not to compute all the values unless it is actually 2d.
            # This is particularly important for the time axis.
            if not using_bounds and len(shape) == 1:
                # 1d coord variable
                minmax = self._min_and_max(self._get_item(var[0]),
                                           self._get_item(var[-1]))
            elif using_bounds and len(shape) == 2 and shape[1] == 2:
                # bounds variable of expected shape for 1d coordinate variable
                minmax = self._min_and_max(self._get_item(var[0, 0]),
                                           self._get_item(var[-1, 1]))
            else:
                vals = var.values
                minmax = (vals.min(), vals.max())

        return minmax


    def _get_coord_var_by_stdname(self, scanobj, stdname):
        for coord in scanobj.coords:
            var = scanobj[coord]
            if var.attrs.get("standard_name") == stdname:
                return var
        return None


    def set_bounds(self, record, scanobj):

        geo_units = []

        for (stdname, bounds_names, conv) in [
                ("latitude", ("south_degrees", "north_degrees"), None),
                ("longitude", ("west_degrees", "east_degrees"), None),
                ("time", ("datetime_start", "datetime_end"), self._get_time_str),
                ("air_pressure", ("height_top", "height_bottom"), None),
        ]:

            var = self._get_coord_var_by_stdname(scanobj, stdname)
            if var is not None:
                if len(var.shape) > 0 and var.size > 0:
                    minmax = self._get_min_max_bounds(scanobj, var)
                    if conv is not None:
                        minmax = (conv(minmax[0]), conv(minmax[1]))
                    record[bounds_names[0]], record[bounds_names[1]] = minmax
                    if "units" in var.attrs:
                        geo_units.append(var.units)
                else:
                    self.publog.warn(f"{stdname} found but len 0")

        if len(geo_units) > 0:
            record["geo_units"] = geo_units
