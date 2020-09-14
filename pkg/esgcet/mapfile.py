import sys, json
from datetime import datetime
import configparser as cfg
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

ARGS = 1

def normalize_path(path, project):
    pparts = path.split('/')
    idx = pparts.index(project)
    if idx < 0:
        raise(BaseException("Incorrect Project in File Path!"))
    proj_root = '/'.join(pparts[0:idx])
    return('/'.join(pparts[idx:]), proj_root)

'''  Input: 
'''
def parse_map(map_data, project=None, normalize=False):

    ret = []    
    for line in map_data:

        parts = line.rstrip().split(' | ')
        if normalize:
            parts[1] = normalize_path(parts[1], project)

        ret.append(parts)

    return ret


''' Input: Takes a 2-D array representation of the parsed map. 
Returns: file records.  assumes that the files all belong to the same dataset
'''
def parse_map_arr(map_data):
    ret = []
    for lst in map_data:
        rec = {}
        rec['file'] = lst[1]
        rec['size'] = int(lst[2])
        for x in lst[3:]:
            parts = x.split('=')
            if parts[0] == 'mod_time':
                rec["timestamp"] = datetime.utcfromtimestamp(float(parts[1])).isoformat() + "Z"
            else:
                rec[parts[0]] = parts[1]
        ret.append(rec)
    return ret



def map_entry(map_json, project, fs_root):
    norm_path = normalize_path(map_json['file'], project)
    abs_path = "{}/{}".format(fs_root, norm_path)
    outarr = []

    outarr.append(map_json['id'])
    outarr.append(abs_path)
    outarr.append(map_json['size'])
    for x in map_json:
        if not x in ['id', 'file', 'size']:
            outarr.append("{}={}".format(x,map_json[x]))
    return ' | '.join(outarr)

def run(args):

    if (len(args) < ARGS):
        print("usage: esgmapconv <mapfile>", file=sys.stderr)
        exit(0)

    with open(args[0]) as map_data:
        ret = parse_map(map_data)
    p = True
    if len(args) > ARGS:
        if args[1] == 'no':
            p = False
    if VERBOSE or p:
        print(json.dumps(ret))
    return ret

def main():
    run(sys.argv[1:])

if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
