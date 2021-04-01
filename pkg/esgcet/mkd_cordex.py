import sys, json, os
from esgcet.mapfile import ESGPubMapConv
import configparser as cfg
from esgcet.mk_dataset import ESGPubMakeDataset
from datetime import datetime, timedelta
from esgcet.settings import *
from pathlib import Path


class ESGPubMKDCordex(ESGPubMakeDataset):

    def update_metadata(self, record, scanobj):
        if "variables" in scanobj:
            if "variable" in record:

                vid = record["variable"]
                var_rec = scanobj["variables"][vid]
                if "long_name" in var_rec.keys():
                    record["variable_long_name"] = var_rec["long_name"]
                elif "info" in var_rec:
                    record["variable_long_name"] = var_rec["info"]
                if "standard_name" in var_rec:
                    record["cf_standard_name"] = var_rec["standard_name"]
                record["variable_units"] = var_rec["units"]
                record["variable"] = vid
            else:
                self.eprint("TODO check project settings for variable extraction")
                record["variable"] = "Multiple"
        else:
            self.eprint("WARNING: no variables were extracted (is this CF compliant?)")

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
                        self.eprint("WARNING: Time values not located...")
                        proc_time = False
                    if proc_time:
                        # TODO: handle this better?
                        try:
                            days_since_dt = datetime.strptime(tu_date.split("T")[0], "%Y-%m-%d")
                        except:
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
        else:
            self.eprint("WARNING: No axes extracted from data files")
