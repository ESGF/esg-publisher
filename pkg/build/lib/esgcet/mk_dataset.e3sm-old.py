import sys, json, os
from esgcet.mapfile import *
import configparser as cfg

from datetime import datetime, timedelta

from esgcet.settings import *
from pathlib import Path

config = cfg.ConfigParser()
home = str(Path.home())
config_file = home + "/.esg/esg.ini"
config.read(config_file)

try:
    s = config['user']['silent']
    if 'true' in s or 'yes' in s:
        SILENT = True
    else:
        SILENT = False
except:
    SILENT = False
try:
    v = config['user']['verbose']
    if 'true' in v or 'yes' in v:
        VERBOSE = True
    else:
        VERBOSE = False
except:
    VERBOSE = False

EXCLUDES = [""]

def eprint(*a):

    print(*a, file=sys.stderr)


def unpack_values(invals):

    for x in invals:
        if x['values']:
            yield x['values']


def get_dataset(mapdata, scandata, data_node, index_node, replica):

    master_id, version = mapdata.split('#')

    parts = master_id.split('.')
    projkey = parts[0]

        
    facets = DRS[projkey]
    d = {}

    if not scandata:
        eprint('WARNING:  empty dataset are the files in the mapfile still valid?')
        return None


    for i, f in enumerate(facets):
        if f in scandata:
            ga_val = scandata[f]
            if not parts[i] == ga_val:
                if not SILENT:
                    eprint("WARNING: {} does not agree!".format(f))
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
    if projkey in GA:
        for facetkey in GA[projkey]:
            # did we find a GA in the data by the the key name
            if facetkey in scandata:
                facetval = scandata[facetkey]
                # is this a delimited attribute ?
                if facetkey in GA_DELIMITED[projkey]:
                    delimiter = GA_DELIMITED[projkey][facetkey]
                    d[facetkey] = facetval.split(delimiter)
                else:
                    d[facetkey] = facetval
        # would we ever combine mapped and delimited facets?
    if projkey in GA_MAPPED:
        for gakey in GA_MAPPED[projkey]:
            if gakey in scandata:
                facetkey = GA_MAPPED[projkey][gakey]
                facetval = scandata[gakey]
                d[facetkey] = facetval
            else:
                if not SILENT:
                    eprint("WARNING: GA to be mapped {} is missing!".format(facetkey))
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
        try:
            globus = config['user']['globus_uuid']
            if globus != 'none':
                return template.format(globus, root, rel)
            else:
                eprint("INFO: no Globus UUID defined. Using default: " + GLOBUS_UUID, file=sys.stderr)
                return template.format(GLOBUS_UUID, root, rel)
        except:
            eprint("INFO: no Globus UUID defined. Using default: " + GLOBUS_UUID, file=sys.stderr)
            return template.format(GLOBUS_UUID, root, rel)
    elif "gsiftp" in template:
        try:
            dtn = config['user']['data_transfer_node']
            if dtn != 'none':
                return template.format(dtn, root, rel)
            else:
                eprint("INFO: no data transfer node defined. Using default: " + DATA_TRANSFER_NODE, file=sys.stderr)
                return template.format(DATA_TRANSFER_NODE, root, rel)
        except:
            eprint("INFO: no data transfer node defined. Using default: " + DATA_TRANSFER_NODE, file=sys.stderr)
            return template.format(DATA_TRANSFER_NODE, root, rel)
    else:
        try:
            data_node = config['user']['data_node']
        except:
            eprint("Data node not defined. Define in esg.ini.", file=sys.stderr)
            exit(1)
        return template.format(data_node, root, rel)


def gen_urls(proj_root, rel_path):
    return  [format_template(template, proj_root, rel_path) for template in URL_Templates]


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

    try:
        data_roots = json.loads(config['user']['data_roots'])
        if data_roots == 'none':
            eprint("Data roots undefined. Define in esg.ini to create file metadata.", file=sys.stderr)
            exit(1)
    except:
        eprint("Data roots undefined. Define in esg.ini to create file metadata.", file=sys.stderr)
        exit(1)
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
            set_variable_metadata(record, scanobj['variables'], vid )
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
    flen =  len(fparts)

    variable_name = "_".join(fparts[0:flen-2])

    return set_variable_metadata(file_rec, scan_vars, variable_name)


def iterate_files(dataset_rec, mapdata, scandata):
    ret = []
    sz = 0
    last_file = None

    if 'file' in scandata:
        scanfile = get_scanfile_dict(scandata['file'])
        if not scanfile:
            eprint("Warning no file metadata found!")
    else:
        eprint("Warning no file metadata found!")
    if 'variables' in scandata:
        scan_vars = scandata['variables']
    #No else because we do a previous check in update matadata for dataset level variables.
    for maprec in mapdata:
        fullpath = maprec['file']
        scanrec = scanfile[fullpath]
        file_rec = get_file(dataset_rec, maprec, scanrec)
        if check_variable(dataset_rec) and scan_vars:
            update_file(file_rec, scan_vars)
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
    scanobj = json.load(open(scanfilename))
    
    rec = get_dataset(mapobj[0][0], scanobj['dataset'], data_node, index_node, replica)

    if not rec:
        return None

    update_metadata(rec, scanobj)
    rec["number_of_files"] = len(mapobj)  # place this better

    if xattrfn:
        xattrobj = json.load(open(xattrfn))
    else:
        xattrobj = {}

    if VERBOSE:
        eprint("rec = ")
        eprint(rec)
        eprint()
    for key in xattrobj:
        rec[key] = xattrobj[key]

    assert('project' in rec)
    project = rec['project']

    mapdict = parse_map_arr(mapobj)
    if VERBOSE:
        print('mapdict = ')
        print(mapdict)
        print()

    ret, sz, access = iterate_files(rec, mapdict, scanobj)

    rec["size"] = sz
    rec["access"] = access
    ret.append(rec)
    return ret


def run(args):
    if (len(args) < 2):
        print("usage: esgmkpubrec <JSON file with map data> <scan file>", file=sys.stderr)
        exit(0)
    p = False
    if args[-1] == 'no':
        data_node = args[2]
        index_node = args[3]
        replica = args[4]
    else:
        p = True
        try:
            data_node = config['user']['data_node']
        except:
            eprint("Data node not defined. Define in esg.ini.")
            exit(1)

        try:
            index_node = config['user']['index_node']
        except:
            eprint("Index node not defined. Define in esg.ini.")
            exit(1)

        try:
            r = config['user']['set_replica']
            if 'true' in r or 'yes' in r:
                replica = True
            elif 'false' in r or 'no' in r:
                replica = False
            else:
                print("Config file error: set_replica must be true, false, yes, or no.", file=sys.stderr)
        except:
            eprint("Replica not defined. Define in esg.ini")
            exit(1)

    if len(args) > 5 and args[-1] != 'no':
        ret = get_records(args[0], args[1], data_node, index_node, replica, xattrfn=args[5])
    else:
        ret = get_records(args[0], args[1], data_node, index_node, replica)
    if p or VERBOSE:
        print(json.dumps(ret,indent=1))
    return ret

def main():
    run(sys.argv[1:])

if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
