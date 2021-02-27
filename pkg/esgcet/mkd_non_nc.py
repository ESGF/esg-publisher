import sys, json, os
from esgcet.mapfile import *
import configparser as cfg

from datetime import datetime, timedelta

from esgcet.settings import *
from pathlib import Path

silent = False
verbose = False
data_roots = {}
globus = "none"
data_node = ""
dtn = "none"
EXCLUDES = [""]

def eprint(*a):
    print(*a, file=sys.stderr)


def unpack_values(invals):
    for x in invals:
        if x['values'] and (not x['values'][0] == x['values'][-1]):
            yield x['values']


def get_dataset(mapdata, data_node, index_node, replica):
    master_id, version = mapdata.split('#')

    parts = master_id.split('.')
    projkey = parts[0]

    facets = DRS[projkey]
    d = {}

    for i, f in enumerate(facets):
        d[f] = parts[i]

    #    SPLIT_FACET = {'E3SM': {'delim': '_', 'facet': 'grid_resolution', 0: 'atmos_', 2: 'ocean_'}}
    if projkey in SPLIT_FACET:
        splitinfo = SPLIT_FACET[projkey]
        splitkey = splitinfo['facet']
        orgval = d[splitkey]
        valsplt = orgval.split(splitinfo['delim'])
        for idxkey in splitinfo:
            if type(idxkey) is int:
                keyprefix = splitinfo[idxkey]
                d[keyprefix + splitkey] = valsplt[idxkey]
    # handle Global attributes if defined for the project
    if projkey in CONST_ATTR:
        for facetkey in CONST_ATTR[projkey]:
            d[facetkey] = CONST_ATTR[projkey][facetkey]

    d['data_node'] = data_node
    d['index_node'] = index_node
    DRSlen = len(DRS[projkey])
    d['master_id'] = master_id
    d['instance_id'] = master_id + '.v' + version
    d['id'] = d['instance_id'] + '|' + d['data_node']
    if 'title' in d:
        d['short_description'] = d['title']
    d['title'] = d['master_id']
    d['replica'] = replica
    d['latest'] = 'true'
    d['type'] = 'Dataset'
    if projkey == "E3SM":
        d['project'] = projkey.lower()
    else:
        d['project'] = projkey

    d['version'] = version

    fmat_list = ['%({})s'.format(x) for x in DRS[projkey]]

    d['dataset_id_template_'] = '.'.join(fmat_list)
    d['directory_format_template_'] = '%(root)s/{}/%(version)s'.format('/'.join(fmat_list))

    return d


def format_template(template, root, rel):
    if "Globus" in template:
        if globus != 'none':
            return template.format(globus, root, rel)
        else:
            if not silent:
                print("INFO: no Globus UUID defined. Using default: " + GLOBUS_UUID, file=sys.stderr)
            return template.format(GLOBUS_UUID, root, rel)
    elif "gsiftp" in template:
        if dtn != 'none':
            return template.format(dtn, root, rel)
        else:
            if not silent:
                print("INFO: no data transfer node defined. Using default: " + DATA_TRANSFER_NODE, file=sys.stderr)
            return template.format(DATA_TRANSFER_NODE, root, rel)
    else:
        return template.format(data_node, root, rel)


def gen_urls(proj_root, rel_path):
    return [format_template(template, proj_root, rel_path) for template in URL_Templates]


def get_file(dataset_rec, mapdata, fn_trid):
    ret = dataset_rec.copy()
    dataset_id = dataset_rec["id"]
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
    proj_key = dataset_rec["project"]
    rel_path, proj_root = normalize_path(fullfn, proj_key.upper())

    if not proj_root in data_roots:
        eprint('Error:  The file system root {} not found.  Please check your configuration.'.format(proj_root))
        exit(1)

    ret["url"] = gen_urls(data_roots[proj_root], rel_path)
    if "number_of_files" in ret:
        ret.pop("number_of_files")
    else:
        eprint("WARNING: no files present")
    if "datetime_start" in ret:
        ret.pop("datetime_start")
        ret.pop("datetime_end")

    return ret
    # need to match up the


def get_scanfile_dict(scandata):
    ret = {}
    for key in scandata:
        rec = scandata[key]
        ret[rec['name']] = rec
    return ret


def set_variable_metadata(record, scan_vars, vid):
    try:
        var_rec = scan_vars[vid]
        if "long_name" in var_rec.keys():
            record["variable_long_name"] = var_rec["long_name"]
        elif "info" in var_rec:
            record["variable_long_name"] = var_rec["info"]
        if "standard_name" in var_rec:
            record["cf_standard_name"] = var_rec["standard_name"]
        record["variable_units"] = var_rec["units"]
        record["variable"] = vid
    except Exception as e:
        eprint("Exception encountered {}".format(str(e)))


def update_metadata(record, scanobj):
    if "variables" in scanobj:
        if "variable_id" in record:

            vid = record["variable_id"]
            set_variable_metadata(record, scanobj['variables'], vid)
        else:
            eprint("TODO check project settings for variable extraction")
            record["variable"] = MULTIPLE
    else:
        eprint("WARNING: no variables were extracted (is this CF compliant?)")

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
                    sub_values = sorted([x for x in unpack_values(subaxes.values())])

                    tu_start_inc = int(sub_values[0][0])
                    tu_end_inc = int(sub_values[-1][-1])
                elif "values" in time_obj:
                    tu_start_inc = time_obj["values"][0]
                    tu_end_inc = time_obj["values"][-1]
                else:
                    eprint("WARNING: Time values not located...")
                    proc_time = False
                if proc_time:
                    try:
                        days_since_dt = datetime.strptime(tu_date, "%Y-%m-%d")
                    except:
                        tu_date = '0' + tu_date
                        days_since_dt = datetime.strptime(tu_date, "%Y-%m-%d")
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
        eprint("WARNING: No axes extracted from data files")


def check_variable(dataset_rec):
    if dataset_rec['project'] in VARIABLE_IN_FN and dataset_rec['variable'] == MULTIPLE:
        field_check = VARIABLE_IN_FN[dataset_rec['project']]
        key = [x for x in field_check.keys()][0]
        value = field_check[key]

        return (dataset_rec[key] == value)
    return False


# extracts the variable name from the file name
def update_file(file_rec, scan_vars):
    fparts = file_rec['title'].split('_')
    flen = len(fparts)

    variable_name = "_".join(fparts[0:flen - 2])

    return set_variable_metadata(file_rec, scan_vars, variable_name)


def iterate_files(dataset_rec, mapdata, scandata):
    ret = []
    sz = 0
    last_file = None

    assert (len(scandata) == 0)

    if 'file' in scandata:
        scanfile = get_scanfile_dict(scandata['file'])
        if not scanfile:
            eprint("Warning no file metadata found!")
    else:
        eprint("Warning no file metadata found!")
    if 'variables' in scandata:
        scan_vars = scandata['variables']
    # No else because we do a previous check in update matadata for dataset level variables.
    for maprec in mapdata:
        fullpath = maprec['file']
        file_rec = get_file(dataset_rec, maprec, {})
        last_file = file_rec
        sz += file_rec["size"]
        ret.append(file_rec)

    access = [x.split("|")[2] for x in last_file["url"]]

    return ret, sz, access


def get_records(mapdata, scanfilename, data_node, index_node, replica, xattrfn=None):
    if isinstance(mapdata, str):
        mapobj = json.load(open(mapdata))
    else:
        mapobj = mapdata

    rec = get_dataset(mapobj[0][0], data_node, index_node, replica)

    if not rec:
        return None

    rec["number_of_files"] = len(mapobj)  # place this better

    if xattrfn:
        xattrobj = json.load(open(xattrfn))
    else:
        xattrobj = {}

    if verbose:
        eprint("rec = ")
        eprint(rec)
        eprint()
    for key in xattrobj:
        rec[key] = xattrobj[key]

    assert ('project' in rec)
    project = rec['project']

    mapdict = parse_map_arr(mapobj)
    if verbose:
        print('mapdict = ')
        print(mapdict)
        print()

    ret, sz, access = iterate_files(rec, mapdict, {})

    rec["size"] = sz
    rec["access"] = access
    ret.append(rec)
    return ret


def run(args):
    global silent
    global verbose
    global data_roots
    global dtn
    global data_node
    global globus
    silent = args[7]
    verbose = args[8]
    data_roots = args[4]
    globus = args[5]
    dtn = args[6]
    data_node = args[1]
    index_node = args[2]
    replica = args[3]

    if len(args) == 11:
        ret = get_records(args[0], "", data_node, index_node, replica, xattrfn=args[9])
    else:
        ret = get_records(args[0], "", data_node, index_node, replica)
    return ret


def main():
    run(sys.argv[1:])


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
