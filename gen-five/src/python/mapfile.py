import sys, json

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

def main(args):

    if (len(args) < ARGS):
        print("Missing required arguments!")
        exit(0)

    with open(args[0]) as map_data:
        ret = parse_map(map_data)
    print(json.dumps(ret, indent=1))


if __name__ == '__main__':
    main(sys.argv[1:])
