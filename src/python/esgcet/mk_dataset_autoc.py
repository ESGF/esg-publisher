from esgcet.handler_base import ESGPubHandlerBase
from datetime import datetime, timedelta
import json

class ESGPubAutocHandler(ESGPubHandlerBase):

    def get_scanfile_dict(self, scandata, mapdata):
#        self.publog.debug(json.dumps(scandata, indent=1))
        self.publog.debug(type(scandata['file']))
        ret = {}
        for key in scandata['file']:
            rec = scandata['file'][key]
            ret[rec['name']] = rec
        return ret

    def unpack_values(self, invals):
        """
        convert a dictionary of items under the key "values" to a list of the values

        invals (dict): input dictionary
        return list
        """
        for x in invals:
            if x['values']:
                yield x['values']

    def get_attrs_dict(self, scanobj):
        return scanobj['dataset']

    def get_variables(self, scanobj):
        return scanobj["variables"]
    
    def get_variable_list(self, variables):
        return list(variables.keys())

    def set_bounds(self, record, scanobj):
        geo_units = []
         
        if "axes" in scanobj:
            axes = scanobj["axes"]
            if "lat" in axes:
                lat = axes["lat"]
                geo_units.append(lat["units"])
                if 'values' not in lat.keys():
                    record["north_degrees"] = lat['subaxes']['0']["values"][-1]
                    record["south_degrees"] = lat['subaxes']['0']["values"][0]
                else:
                    record["north_degrees"] = lat["values"][-1]
                    record["south_degrees"] = lat["values"][0]
            if "lon" in axes:
                lon = axes["lon"]
                geo_units.append(lon["units"])
                if 'values' not in lon.keys():
                    record["east_degrees"] = lon['subaxes']['0']["values"][-1]
                    record["west_degrees"] = lon['subaxes']['0']["values"][0]
                else:
                    record["east_degrees"] = lon["values"][-1]
                    record["west_degrees"] = lon["values"][0]
            if "time" in axes:
                time_obj = axes["time"]
                time_units = time_obj["units"]
                tu_parts = []
                if type(time_units) is str:
                    tu_parts = time_units.split()
                if len(tu_parts) > 2 and tu_parts[0] == "days" and tu_parts[1] == "since":
                    proc_time = True
                    tu_date = tu_parts[2]  # can we ignore time component?
                    if "subaxes" in time_obj:
                        subaxes = time_obj["subaxes"]
                        sub_values = sorted([x for x in self.unpack_values(subaxes.values())])

                        tu_start_inc = int(sub_values[0][0])
                        tu_end_inc = int(sub_values[-1][-1])
                    elif "values" in time_obj:
                        tu_start_inc = time_obj["values"][0]
                        tu_end_inc = time_obj["values"][-1]
                    else:
                        self.publog.warning("Time values not located...")
                        proc_time = False
                    if proc_time:
                        try:
                            days_since_dt = datetime.strptime(tu_date.split("T")[0], "%Y-%m-%d")
                        except:
                            tu_date = '0' + tu_date
                            while len(tu_date.split('-')[0]) < 4:
                                tu_date = '0' + tu_date
                            days_since_dt = datetime.strptime(tu_date.split("T")[0], "%Y-%m-%d")
                        dt_start = days_since_dt + timedelta(days=tu_start_inc)
                        dt_end = days_since_dt + timedelta(days=tu_end_inc)
                        if dt_start.microsecond >= 500000:
                            dt_start = dt_start + timedelta(seconds=1)
                        dt_start = dt_start.replace(microsecond=0)
                        record["datetime_start"] = "{}Z".format(dt_start.isoformat())
                        record["datetime_end"] = "{}Z".format(dt_end.isoformat())

            if "plev" in axes:
                plev = axes["plev"]
                if "units" in plev and "values" in plev:
                    record["height_units"] = plev["units"]
                    record["height_top"] = plev["values"][0]
                    record["height_bottom"] = plev["values"][-1]
            if len(geo_units) > 0:
                record["geo_units"] = geo_units
        else:
            self.publog.warning("No axes extracted from data files")

