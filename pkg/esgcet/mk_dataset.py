import sys, json
from esgcet.mapfile import ESGPubMapConv
import configparser as cfg

from datetime import datetime, timedelta

from esgcet.settings import *
from pathlib import Path


class ESGPubMakeDataset:

    def init_project(self, project):

        if project in DRS:
            self.DRS = DRS['project']
            if 'project' in CONST_ATTR:
                self.CONST_ATTR = CONST_ATTR['project']
        elif project in user_project:
            self.DRS = user_project['project']['DRS']
            if len(user_project['project']['CONST_ATTR']) > 0:
                self.CONST_ATTR = user_project['project']['CONST_ATTR']
        else:
            raise (BaseException("Error: Project {project} Data Record Syntax (DRS) not defined. Define in esg.ini"))

    def __init__(self, data_node, index_node, replica, globus, data_roots, dtn, silent=False, verbose=False, user_project=None):
        self.silent = silent
        self.verbose = verbose
        self.data_roots = data_roots
        self.globus = globus
        self.data_node = data_node
        self.index_node = index_node
        self.replica = replica
        self.dtn = dtn

        self.mapconv = ESGPubMapConv("")
        self.dataset = {}
        self.project = None
        self.user_project = user_project
        self.DRS = None
        self.CONST_ATTR = None
        self.variable_name = "variable_id"

    def set_project(self, project_in):
        self.project = project_in

    def eprint(self, *a):

        print(*a, file=sys.stderr)

    def unpack_values(self, invals):

        for x in invals:
            if x['values']:
                yield x['values']

    def get_dataset(self, mapdata, scandata):

        master_id, version = mapdata.split('#')

        parts = master_id.split('.')

        projkey = parts[0]

        if self.project:
            projkey = self.project
        self.init_project(projkey)

        facets = self.DRS  # depends on Init_project to initialize

        assert(facets)
        if projkey == "cordex":
            self.variable_name = "variable"

        for i, f in enumerate(facets):
            if f in scandata:
                ga_val = scandata[f]
                if not parts[i] == ga_val:
                    if not self.silent:
                        self.eprint("WARNING: {} does not agree!".format(f))
            self.dataset[f] = parts[i]

        self.global_attributes(projkey, scandata)
        self.global_attr_mapped(projkey, scandata)
        self.const_attr()
        self.assign_dset_values(projkey, master_id, version)

    def global_attributes(self, projkey, scandata):
        # handle Global attributes if defined for the project
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

    def global_attr_mapped(self, projkey, scandata):
        if projkey in GA_MAPPED:
            for gakey in GA_MAPPED[projkey]:
                if gakey in scandata:
                    facetkey = GA_MAPPED[projkey][gakey]
                    facetval = scandata[gakey]
                    self.dataset[facetkey] = facetval
                else:
                    if not self.silent:
                        self.eprint("WARNING: GA to be mapped {} is missing!".format(facetkey))

    def const_attr(self):
        if self.CONST_ATTR:
            for facetkey in self.CONST_ATTR:
                self.dataset[facetkey] = self.CONST_ATTR[facetkey]

    def assign_dset_values(self, projkey, master_id, version):

        self.dataset['data_node'] = self.data_node
        self.dataset['index_node'] = self.index_node
        DRSlen = len(DRS[projkey])
        self.dataset['master_id'] = master_id
        self.dataset['instance_id'] = master_id + '.v' + version
        self.dataset['id'] = self.dataset['instance_id'] + '|' + self.dataset['data_node']
        if 'title' in self.dataset:
            self.dataset['short_description'] = self.dataset['title']
        self.dataset['title'] = self.dataset['master_id']
        self.dataset['replica'] = self.replica
        self.dataset['latest'] = 'true'
        self.dataset['type'] = 'Dataset'
        self.dataset['project'] = projkey
        self.dataset['version'] = version

        fmat_list = ['%({})s'.format(x) for x in DRS[projkey]]

        self.dataset['dataset_id_template_'] = '.'.join(fmat_list)
        self.dataset['directory_format_template_'] = '%(root)s/{}/%(version)s'.format('/'.join(fmat_list))

    def format_template(self, template, root, rel):
        if "Globus" in template:
            if self.globus != 'none':
                return template.format(self.globus, root, rel)
            else:
                if not self.silent:
                    print("INFO: no Globus UUID defined. Using default: " + GLOBUS_UUID, file=sys.stderr)
                return template.format(GLOBUS_UUID, root, rel)
        elif "gsiftp" in template:
            if self.dtn != 'none':
                return template.format(self.dtn, root, rel)
            else:
                if not self.silent:
                    print("INFO: no data transfer node defined. Using default: " + DATA_TRANSFER_NODE, file=sys.stderr)
                return template.format(DATA_TRANSFER_NODE, root, rel)
        else:
            return template.format(self.data_node, root, rel)

    def gen_urls(self, proj_root, rel_path):
        return [self.format_template(template, proj_root, rel_path) for template in URL_Templates]

    def get_file(self, mapdata, fn_trid):
        ret = self.dataset.copy()
        print(self.dataset.keys())
        dataset_id = self.dataset["id"]
        ret['type'] = "File"
        fullfn = mapdata['file']

        fparts = fullfn.split('/')
        title = fparts[-1]
        ret['id'] = "{}.{}".format(ret['instance_id'], title)
        ret['title'] = title
        ret["dataset_id"] = dataset_id
        if "tracking_id" in fn_trid:
            ret["tracking_id"] = fn_trid["tracking_id"]

        for kn in mapdata:
            if kn not in ("id", "file"):
                ret[kn] = mapdata[kn]

        rel_path, proj_root = self.mapconv.normalize_path(fullfn, self.dataset["project"])

        if not proj_root in self.data_roots:
            self.eprint(
                'Error:  The file system root {} not found.  Please check your configuration.'.format(proj_root))
            exit(1)

        ret["url"] = self.gen_urls(self.data_roots[proj_root], rel_path)
        if "number_of_files" in ret:
            ret.pop("number_of_files")
        else:
            self.eprint("WARNING: no files present")
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

    def iterate_files(self, mapdata, scandata):
        ret = []
        sz = 0
        last_file = None

        for maprec in mapdata:
            fullpath = maprec['file']
            scanrec = scandata[fullpath]
            file_rec = self.get_file(maprec, scanrec)
            last_file = file_rec
            sz += file_rec["size"]
            ret.append(file_rec)

        access = [x.split("|")[2] for x in last_file["url"]]

        return ret, sz, access

    def get_records(self, mapdata, scanfilename, xattrfn=None, user_project=None):

        self.user_project = user_project

        if isinstance(mapdata, str):
            mapobj = json.load(open(mapdata))
        else:
            mapobj = mapdata
        scanobj = json.load(open(scanfilename))

        self.get_dataset(mapobj[0][0], scanobj['dataset'])
        self.update_metadata(self.dataset, scanobj)
        self.dataset["number_of_files"] = len(mapobj)  # place this better

        if xattrfn:
            xattrobj = json.load(open(xattrfn))
        else:
            xattrobj = {}

        if self.verbose:
            print("rec = ")
            print(self.dataset)
            print()
        for key in xattrobj:
            self.dataset[key] = xattrobj[key]

        project = self.dataset['project']
        self.mapconv.set_map_arr(mapobj)
        mapdict = self.mapconv.parse_map_arr()

        if self.verbose:
            print('mapdict = ')
            print(mapdict)
            print()
        scandict = self.get_scanfile_dict(scanobj['file'])
        if self.verbose:
            print('scandict = ')
            print(scandict)
            print()
        ret, sz, access = self.iterate_files(mapdict, scandict)
        self.dataset["size"] = sz
        self.dataset["access"] = access
        ret.append(self.dataset)
        return ret
