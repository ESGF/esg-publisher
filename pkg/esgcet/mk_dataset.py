import sys, json
from esgcet.mapfile import ESGPubMapConv
import configparser as cfg

from datetime import datetime, timedelta

from esgcet.settings import *
from pathlib import Path
import esgcet.logger as logger

log = logger.Logger()


class ESGPubMakeDataset:

    def init_project(self, proj):
        project = proj

        if project in DRS:
            self.DRS = DRS[project]
            if project in CONST_ATTR:
                self.CONST_ATTR = CONST_ATTR[project]
        elif self.user_project and "clone_project" in self.user_project:
            cloneproj = self.user_project["clone_project"]
            if cloneproj not in DRS:
                raise(RuntimeError(f"Project {cloneproj} Data Record Syntax (DRS) not defined. Define in esg.ini"))
            self.DRS = DRS[cloneproj]
            if cloneproj in CONST_ATTR:
                self.CONST_ATTR = CONST_ATTR[cloneproj]
            else:
                self.CONST_ATTR = {}
            if 'CONST_ATTR' in self.user_project[project]:
                self.CONST_ATTR.update(self.user_project[project]['CONST_ATTR'])
        elif self.user_project and project in self.user_project:
            if 'DRS' in self.user_project[project]:
                self.DRS = self.user_project[project]['DRS']
            if 'CONST_ATTR' in self.user_project[project]:
                self.CONST_ATTR = self.user_project[project]['CONST_ATTR']
        else:
            raise (BaseException(f"Error: Project {project} Data Record Syntax (DRS) not defined. Define in esg.ini"))

    def __init__(self, data_node, index_node, replica, globus, data_roots, dtn, silent=False, verbose=False, limit_exceeded=False, user_project=None):
        self.silent = silent
        self.verbose = verbose
        self.data_roots = data_roots
        self.globus = globus
        self.data_node = data_node
        self.index_node = index_node
        self.replica = replica
        self.dtn = dtn
        self.limit_exceeded = limit_exceeded

        self.mapconv = ESGPubMapConv("")
        self.dataset = {}
        self.project = None
        self.user_project = user_project
        self.DRS = None
        self.CONST_ATTR = None
        self.variable_name = "variable_id"
        self.publog = log.return_logger('Make Dataset', self.silent, self.verbose)
        self.xattr = None
        self.tracking_id_set = set()

    def set_project(self, project_in):
        self.project = project_in

    def unpack_values(self, invals):
        for x in invals:
            if x['values']:
                yield x['values']

    def prune_list(self, ll):
        for x in ll:
            if not x is None:
                yield (x)

    def load_xattr(self, xattrfn):
        if self.xattr:
            return
        if (xattrfn):
            self.xattr = json.load(open(xattrfn))
        else:
            self.xattr = {}

    def proc_xattr(self, xattrfn):
        self.load_xattr(xattrfn)
        if len(self.xattr) > 0:
            tmp_xattr = self.xattr_handler()
            for key in tmp_xattr:
                self.dataset[key] = tmp_xattr[key]

    def xattr_handler(self):
        return self.xattr

    def get_dataset(self, mapdata, scanobj):

        master_id, version = mapdata.split('#')

        parts = master_id.split('.')

        projkey = parts[0]
        self.first_val = projkey
        scandata = scanobj['dataset']


        if self.project:
            projkey = self.project
        self.init_project(projkey.lower())

        facets = self.DRS  # depends on Init_project to initialize

        assert(facets)
        if projkey == "cordex":
            self.variable_name = "variable"

        for i, f in enumerate(facets):
            if f in scandata:
                ga_val = scandata[f]
                if not parts[i] == ga_val:
                    self.publog.warning("{} does not agree!".format(f))
            self.dataset[f] = parts[i]

        priorkey = projkey
        if self.user_project and "clone_project" in self.user_project:
            projkey = self.user_project["clone_project"]
        self.global_attributes(projkey, scandata)
        self.global_attr_mapped(projkey, scandata)
        self.assign_dset_values(master_id, version)
        self.const_attr()
        if not 'project' in self.dataset:
            self.dataset['project'] = priorkey


    def global_attributes(self, proj, scandata):
        # handle Global attributes if defined for the project
        projkey = proj.lower()

        if projkey in GA:
            for facetkey in GA[projkey]:
                # did we find a GA in the data by the the key name
                if facetkey in scandata:
                    facetval = scandata[facetkey]
                    # is this a delimited attribute ?
                    if facetkey in GA_DELIMITED[projkey]:
                        delimiter = GA_DELIMITED[projkey][facetkey]
                        self.dataset[facetkey] = facetval.split(delimiter)
                    else:
                        self.dataset[facetkey] = facetval

    def global_attr_mapped(self, proj, scandata):
        projkey = proj.lower()

        if projkey in GA_MAPPED:
            for gakey in GA_MAPPED[projkey]:
                if gakey in scandata:
                    facetkey = GA_MAPPED[projkey][gakey]
                    facetval = scandata[gakey]
                    self.dataset[facetkey] = facetval
                else:
                    self.publog.warning("GA to be mapped {} is missing!".format(facetkey))

    def const_attr(self):
        if self.CONST_ATTR:
            for facetkey in self.CONST_ATTR:
                self.dataset[facetkey] = self.CONST_ATTR[facetkey]

    def assign_dset_values(self, master_id, version):

        self.dataset['data_node'] = self.data_node
        self.dataset['index_node'] = self.index_node
        self.dataset['master_id'] = master_id
        self.dataset['instance_id'] = master_id + '.v' + version
        self.dataset['id'] = self.dataset['instance_id'] + '|' + self.dataset['data_node']
        if 'title' in self.dataset:
            self.dataset['short_description'] = self.dataset['title']
        self.dataset['title'] = self.dataset['master_id']
        self.dataset['replica'] = self.replica
        self.dataset['latest'] = 'true'
        self.dataset['type'] = 'Dataset'
        self.dataset['version'] = version

        fmat_list = ['%({})s'.format(x) for x in self.DRS]

        self.dataset['dataset_id_template_'] = '.'.join(fmat_list)
        self.dataset['directory_format_template_'] = '%(root)s/{}/%(version)s'.format('/'.join(fmat_list))

    def format_template(self, template, root, rel):
        if "Globus" in template:
            if self.globus != 'none':
                return template.format(self.globus, root, rel)
            else:
                return None
        elif "gsiftp" in template:
            if self.dtn != 'none':
                if ':' in self.dtn:
                    template = template.replace(':2811','')
                return template.format(self.dtn, root, rel)
            else:
                return None
        else:
            return template.format(self.data_node, root, rel)

    def gen_urls(self, proj_root, rel_path):
        res = self.prune_list([self.format_template(template, proj_root, rel_path) for template in URL_Templates])
        return list(res)

    def get_file(self, mapdata, fn_trid):
        ret = self.dataset.copy()
        dataset_id = self.dataset["id"]
        ret['type'] = "File"
        fullfn = mapdata['file']

        fparts = fullfn.split('/')
        title = fparts[-1]
        ret['id'] = "{}.{}|{}".format(ret['instance_id'], title, self.data_node)
        ret['master_id'] = f"{ret['master_id']}.{title}"

        ret['instance_id'] = "{}.{}".format(ret['instance_id'], title)
        ret['title'] = title
        ret["dataset_id"] = dataset_id
        if "tracking_id" in fn_trid:
            if fn_trid["tracking_id"] in self.tracking_id_set:
                self.publog.error(f"Duplicate tracking_id {fn_trid['tracking_id']} encountered!")
                exit(1)
            self.tracking_id_set.add(fn_trid["tracking_id"])
            ret["tracking_id"] = fn_trid["tracking_id"]

        for kn in mapdata:
            if kn not in ("id", "file"):
                ret[kn] = mapdata[kn]

        rel_path, proj_root = self.normalize_path(fullfn, self.data_roots)

        if not proj_root in self.data_roots:

            # Need to handle the case where the root might contain the
            # project ID, ensure that the original root and the id are
            # found.`
            root_found = False
            for root in self.data_roots:
                if self.first_val in root and proj_root in root:
                    proj_root = root
                    rel_path = rel_path.replace(f"{self.first_val}/","")
                    root_found = True
                    break
            if not root_found:
                self.publog.error('The file system root {} not found.  Please check your configuration.'.format(proj_root))
                exit(1)

        ret["url"] = self.gen_urls(self.data_roots[proj_root], rel_path)
        ret["publish_path"] = f"{self.data_roots[proj_root]}/{rel_path}"
        if "number_of_files" in ret:
            ret.pop("number_of_files")
        else:
            self.publog.warning("No files present")
        if "datetime_start" in ret:
            ret.pop("datetime_start")
            ret.pop("datetime_end")

        return ret

    def get_scanfile_dict(self, scandata):
        ret = {}
        for key in scandata:
            rec = scandata[key]
            ret[rec['name']] = rec
        return ret

    def update_metadata(self, record, scanobj):
        if "variables" in scanobj:
            if self.variable_name in record:

                vid = record[self.variable_name]
                try:
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

                except Exception as ex:
                    self.publog.exception("Variable could not be extracted, exception encountered")
                    record[self.variable_name] = "none"
            else:
                self.publog.warning("TODO check project settings for variable extraction")
                record[self.variable_name] = "Multiple"
                if self.variable_name == "variable_id":
                    record["variable"] = "Multiple"
        else:
            self.publog.warning("No variables were extracted (is this CF compliant?)")

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
        else:
            self.publog.warning("No axes extracted from data files")

    def iterate_files(self, mapdata, scandata):
        ret = []
        sz = 0
        last_file = None

        for maprec in mapdata:
            fullpath = maprec['file']
            if fullpath not in scandata.keys():
                if not self.limit_exceeded and self.project != "CREATE-IP" and self.project != "cmip5":
                    self.publog.error("Autocurator data not found for file: " + fullpath)
                    exit(1)
                continue
            scanrec = scandata[fullpath]
            file_rec = self.get_file(maprec, scanrec)
            last_file = file_rec
            sz += file_rec["size"]
            ret.append(file_rec)

        lst = []
        for x in last_file["url"]:
            if x:
                lst.append(x)
        last_file["url"] = lst
        access = [x.split("|")[2] for x in last_file["url"]]

        return ret, sz, access

    def get_records(self, mapdata, scanfilename, xattrfn=None, user_project=None):

        self.user_project = user_project
        self.load_xattr(xattrfn)

        if isinstance(mapdata, str):
            mapobj = json.load(open(mapdata))
        else:
            mapobj = mapdata
        scanobj = json.load(open(scanfilename))

        self.get_dataset(mapobj[0][0], scanobj)
        self.update_metadata(self.dataset, scanobj)
        self.dataset["number_of_files"] = len(mapobj)  # place this better
        project = self.dataset['project']

        self.proc_xattr(xattrfn)

        self.publog.debug("Record:\n" + json.dumps(self.dataset, indent=4))
        print()

        self.mapconv.set_map_arr(mapobj)
        mapdict = self.mapconv.parse_map_arr()

        self.publog.debug('Mapfile dictionary:\n' + json.dumps(mapdict, indent=4))
        print()
        scandict = self.get_scanfile_dict(scanobj['file'])
        self.publog.debug('Autocurator Scanfile dictionary:\n' + json.dumps(scandict, indent=4))
        print()
        ret, sz, access = self.iterate_files(mapdict, scandict)
        self.dataset["size"] = sz
        self.dataset["access"] = access
        ret.append(self.dataset)
        return ret

    @staticmethod
    def normalize_path(path, data_roots):

        proj_root = None

        # Check each data root to see if it matches the provided path
        for data_root, _ in data_roots.items():
            path_match = "{}/".format(data_root.rstrip("/"))
            if path.startswith(path_match):

                rel_path = path[len(path_match):]
                proj_root = data_root.rstrip("/")

        if not proj_root:
            raise(BaseException("File Path does not match any data roots!"))

        return rel_path, proj_root
