import sys, json
from mapfile import *

from datetime import datetime, timedelta

DEBUG = False

DRS = { 'CMIP6' : [ 'mip_era' , 'activity_drs','institution_id','source_id','experiment_id','member_id','table_id','variable_id','grid_label'] }
GA = { 'CMIP6' : ['frequency',
                     'realm',
                     'product',
                     'nominal_resolution',
                     'source_type',
                     'grid',
                     'creation_date',
                     'variant_label',
                     'sub_experiment_id',
                     'further_info_url',
                     'activity_id',
                     'data_specs_version', 'title']}

DATA_NODE = "greyworm1-rh7.llnl.gov"
INDEX_NODE = "esgf-fedtest.llnl.gov"
ROOT = {'esgf_data': '/esg/data'}

EXCLUDES = [""]

def get_dataset(mapdata, scandata):

    master_id, version = mapdata.split('#')

    parts = master_id.split('.')
    key = parts[0]
    facets = DRS[key]
    d = {}
    for i, f in enumerate(facets):
        if f in scandata:
            ga_val = scandata[f]
            if not parts[i] == ga_val:
                print("WARNING: {} does not agree!".format(f))
        d[f] = parts[i]

    for val in GA[key]:
        if val in scandata:
            d[val] = scandata[val]


    d['data_node'] = DATA_NODE
    d['index_node'] = INDEX_NODE
    DRSlen = len(DRS[key])
    d['master_id'] = master_id
    d['instance_id'] = master_id + '.' + version
    d['id'] = d['instance_id'] + '|' + d['data_node']
    if not 'title' in d:
        d['title'] = d['instance_id']
    d['replica'] = 'false' # set replica
    d['latest'] = 'true'
    d['type'] = 'Dataset'
    d['project'] = key
    d['version'] = version

    return d

URL_Templates = ["https://{}/thredds/fileServer/{}/{}|application/netcdf|HTTPServer"]

def gen_urls(proj_root, rel_path):
    return  [template.format(DATA_NODE, proj_root, rel_path) for template in URL_Templates]



def get_file(dataset_rec, mapdata, fn_trid, proj_root):
    ret = dataset_rec.copy()
    dataset_id = dataset_rec["id"]
    ret['type'] = "File"
    fullfn = mapdata['file']

    fparts = fullfn.split('/')
    title = fparts[-1]
    ret['id'] = "{}.{}".format(ret['instance_id'],title)
    ret['title'] = title
    ret["dataset_id"] = dataset_id
    ret["tracking_id"] = fn_trid["tracking_id"]

    for kn in mapdata:
        if kn not in ("id", "file"):
            ret[kn] = mapdata[kn]
    rel_path = normalize_path(fullfn, proj_root)
    ret["url"] = gen_urls(proj_root, rel_path)

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
        else:
            print("TODO check project settings for variable extraction")
    else:
        print("WARNING: no variables were extracted (is this CF compliant?)")

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
            tu_parts = time_units.split()
            if tu_parts[0] == "days" and tu_parts[1] == "since":
                proc_time = True
                tu_date = tu_parts[2] # can we ignore time component?
                if "subaxes" in time_obj:
                    subaxes = time_obj["subaxes"]
                    sub_values = sorted([x['values'] for x in subaxes.values()])


                    tu_start_inc = int(sub_values[0][0])
                    tu_end_inc = int(sub_values[-1][-1])
                elif "values" in time_obj:
                    tu_start_inc = time_obj["values"][0]
                    tu_end_inc = time_obj["values"][-1]
                else:
                    print("WARNING: not sure where time values are...")
                    proc_time = False
                if proc_time:
                    days_since_dt = datetime.strptime(tu_date, "%Y-%m-%d")
                    dt_start = days_since_dt + timedelta(days=tu_start_inc) 
                    dt_end = days_since_dt  + timedelta(days=tu_end_inc) 
                    record["datetime_start"] = "{}Z".format(dt_start.isoformat())
                    record["datetime_end"] = "{}Z".format(dt_end.isoformat())

        if "plev" in axes:
            plev = axes["plev"]
            if "units" in plev and "values" in plev:
                record["height_units"] = plev["units"]
                record["height_top"] = plev["values"][0]
                record["height_bottom"] = plev["values"][-1]
    else:
        print("WARNING: No axes extracted from data files")

def iterate_files(dataset_rec, mapdata, scandata, proj_root):

    ret = []

    for maprec in mapdata:

        fullpath = maprec['file']
        scanrec = scandata[fullpath]
        ret.append(get_file(dataset_rec, maprec, scanrec, proj_root))
    return ret

def get_records(mapfilename, scanfilename, xattrfn=None):

    mapobj = json.load(open(mapfilename))
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
    ret, sz = iterate_files(rec, mapdict, scandict, project)
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
    print(json.dumps(ret, indent=1))

if __name__ == '__main__':
    main(sys.argv[1:])
