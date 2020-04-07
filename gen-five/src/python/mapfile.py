
def normalize_path(path, project):
    pparts = path.split('/')
    idx = pparts.index(project)
    if idx < 0:
        raise(BaseException("Incorrect Project in File Path!"))
    return('/'.join(pparts[idx:]))


def parse_map(map_data, project):

    ret = []    
    for line in map_data:

        parts = line.split('|')
        parts[1] = normalize_path(parts[1])
        ret.append(parts)

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

