import sys, json
from mapfile import *
import args

from datetime import datetime, timedelta

from settings import *



EXCLUDES = [""]

def eprint(*a):

    print(*a, file=sys.stderr)


def unpack_values(invals):

    for x in invals:
        if x['values']:
            yield x['values']


def get_dataset(mapdata, scandata):

    if DATA_NODE == "":
        raise BaseException("Missing data node!")
    if INDEX_NODE == "":
        raise BaseException("Missing index node!")

    master_id, version = mapdata.split('#')

    parts = master_id.split('.')
    projkey = parts[0]
    facets = DRS[projkey]
    d = {}
    for i, f in enumerate(facets):
        if f in scandata:
            ga_val = scandata[f]
            if not parts[i] == ga_val:
                eprint("WARNING: {} does not agree!".format(f))
        d[f] = parts[i]

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
        for gakey in GA_MAPPED[projkey]:
            if gakey in scandata:
                facetkey = GA_MAPPED[projkey][gakey]
                facetval = scandata[gakey]
                d[facetkey] = facetval
            else:
                eprint("WARNING: GA to be mapped {} is missing!".format(facetkey))
        for facetkey in CONST_ATTR[projkey]:
            d[facetkey] = CONST_ATTR[projkey][facetkey]

    pub = args.get_args()
    if pub.set_replica:
        replica = True
    else:
        replica = False
    d['data_node'] = pub.data_node
    d['index_node'] = pub.index_node
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
    d['project'] = projkey
    d['version'] = version

    fmat_list = ['%({})s'.format(x) for x in DRS[projkey]]

    d['dataset_id_template_'] = '.'.join(fmat_list)
    d['directory_format_template_'] = '%(root)s/{}/%(version)s'.format('/'.join(fmat_list))

    return d


def gen_urls(proj_root, rel_path):
    return [template.format(DATA_NODE, proj_root, rel_path) for template in URL_Templates]


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

    rel_path, proj_root = normalize_path(fullfn, dataset_rec["project"])

    if not proj_root in DATA_ROOTS:
        eprint('Error:  The file system root {} not found.  Please check your configuration.'.format(proj_root))
        exit(1)

    ret["url"] = gen_urls(DATA_ROOTS[proj_root], rel_path)
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


def update_metadata(record, scanobj):
    if "variables" in scanobj:
        if "variable_id" in record:

            vid = record["variable_id"]
            var_rec = scanobj["variables"][vid]
            record["variable_long_name"] = var_rec["long_name"]
            record["cf_standard_name"] = var_rec["standard_name"]
            record["variable_units"] = var_rec["units"]
            record["variable"] = vid
        else:
            eprint("TODO check project settings for variable extraction")
            record["variable"] = "Multiple"
    else:
        eprint("WARNING: no variables were extracted (is this CF compliant?)")

    geo_units = []
    if "axes" in scanobj:
        axes = scanobj["axes"]
        if "lat" in axes:
            lat = axes["lat"]
            geo_units.append(lat["units"])
            record["north_degrees"] = lat["values"][-1]
            record["south_degrees"] = lat["values"][0]
        if "lon" in axes:
            lon = axes["lon"]
            geo_units.append(lon["units"])
            record["east_degrees"] = lat["values"][-1]
            record["west_degrees"] = lat["values"][0]
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
                    eprint("WARNING: not sure where time values are...")
                    proc_time = False
                if proc_time:
                    days_since_dt = datetime.strptime(tu_date, "%Y-%m-%d")
                    dt_start = days_since_dt + timedelta(days=tu_start_inc)
                    dt_end = days_since_dt + timedelta(days=tu_end_inc)
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


def iterate_files(dataset_rec, mapdata, scandata):
    ret = []
    sz = 0

    for maprec in mapdata:
        fullpath = maprec['file']
        scanrec = scandata[fullpath]
        file_rec = get_file(dataset_rec, maprec, scanrec)
        sz += file_rec["size"]
        ret.append(file_rec)

    return ret, sz

def get_records(mapdata, scanfilename, xattrfn=None):

    mapobj = mapdata
    scanobj = json.load(open(scanfilename))

    rec = get_dataset(mapobj[0][0], scanobj['dataset'])
    update_metadata(rec, scanobj)
    rec["number_of_files"] = len(mapobj)  # place this better

    if xattrfn:
        xattrobj = json.load(open(xattrfn))
    else:
        xattrobj = {}

    if DEBUG:
        print("rec = ")
        print(rec)
        print()
    for key in xattrobj:
        rec[key] = xattrobj[key]

    project = rec['project']
    mapdict = parse_map_arr(mapobj)
    if DEBUG:
        print('mapdict = ')
        print(mapdict)
        print()
    scandict = get_scanfile_dict(scanobj['file'])
    if DEBUG:
        print('scandict = ')
        print(scandict)
        print()
    ret, sz = iterate_files(rec, mapdict, scandict)
    rec["size"] = sz
    ret.append(rec)
    return ret


def main(args):
    if (len(args) < 2):
        print("Missing required arguments!")
        exit(0)

    if len(args) > 2:
        ret = get_records(args[0], args[1], xattrfn=args[2])
    else:
        ret = get_records(args[0], args[1])
    return ret
