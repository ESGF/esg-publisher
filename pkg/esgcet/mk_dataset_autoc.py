from mk_dataset import ESGPubMakeDataset

class ESGPubMakeAutocDataset(ESGPubMakeDataset):

    def __init__(self, *args):
        super().__init__(args)

    def get_scanfile_dict(self, scandata):
        ret = {}
        for key in scandata:
            rec = scandata[key]
            ret[rec['name']] = rec
        return ret

    def get_attrs_dict(self, scanobj):
        return scanobj['dataset']

    def set_variables(self, record, scanobj, vid):
        if vid in scanobj["variables"]:
                var_rec = scanobj["variables"][vid]
                if "long_name" in var_rec.keys():
                    record["variable_long_name"] = var_rec["long_name"]
                elif "info" in var_rec:
                    record["variable_long_name"] = var_rec["info"]
                if "standard_name" in var_rec:
                    record["cf_standard_name"] = var_rec["standard_name"]
                record["variable_units"] = var_rec["units"]
                record[self.variable_name] = vid
                if self.variable_name == "variable_id":
                    record["variable"] = vid
        else:
            var_list = list(scanobj["variables"].keys())
            if len(var_list) < VARIABLE_LIMIT:
                init_lst = [self.variable_name, "variable_long_name"]
                if "variable_id" in init_lst:
                    init_lst.append("variable")
                for kid in init_lst:
                    record[kid] = []
                units_list = []
                cf_list = []
                for vk in var_list:
                    if not vk in VARIABLE_EXCLUDES:
                        var_rec = scanobj["variables"][vk]
                        if "long_name" in var_rec.keys():
                            record["variable_long_name"].append(var_rec["long_name"])
                        elif "info" in var_rec:
                            record["variable_long_name"].append(var_rec["info"])
                        if "standard_name" in var_rec and len(var_rec["standard_name"]) > 0:
                            cf_list.append(var_rec["standard_name"])          
                        if var_rec["units"] != "1" and len(var_rec["units"]) > 0:
                            units_list.append(var_rec["units"])
                        record["variable"].append(vk)

                if self.variable_name == "variable_id":
                    record[self.variable_name] = "Multiple"
                record["variable_units"] = list(set(units_list))
                record["cf_standard_name"] = list(set(cf_list))
        
            if self.variable_name == "variable_id":
                record["variable"] = "Multiple"


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

