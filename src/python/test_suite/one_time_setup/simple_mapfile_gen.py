import os
import sys
import re
import string

from utils.cksum import get_cksum

"""
Do simple generation of mapfiles without all the vocab checking
"""

drs_length = {
    # number of DRS elements in each project, not including the version
    'cmip5': 9
    }


def gen_all_mapfiles(data_root, mapfile_dir, cksum_type = "SHA256"):
    try:
        os.mkdir(mapfile_dir)
    except OSError:
        print "Remove %s and start again" % mapfile_dir
        sys.exit(1)

    version_match = re.compile("v[0-9]+$").match

    for rel_path in list_nc_files(data_root):
        full_path = os.path.join(data_root, rel_path)

        bits = rel_path.split("/")
        project = bits[0]
        nbit = drs_length[project]
        dsid_no_version = string.join(bits[:nbit], ".")
        if not version_match(bits[nbit]):
            print "Skipping %s - cannot find version number in correct path element" % full_path
            continue
        dsid_with_version = string.join(bits[: nbit + 1], ".")
        mf_path = os.path.join(mapfile_dir, dsid_with_version)
        
        checksum = get_cksum(full_path, cksum_type)
        mod_time = get_mtime(full_path)
        size = get_size(full_path)
        
        mf_bits = (dsid_no_version,
                   full_path,
                   "%s" % size,
                   "mod_time=%f" % mod_time,
                   "checksum=%s" % checksum,
                   "checksum_type=%s" % cksum_type)

        line = string.join(mf_bits, " | ")

        add_line(mf_path, line + "\n")

    print "Made mapfiles:"
    for f in os.listdir(mapfile_dir):
        print f
        

def list_nc_files(data_root):
    """
    iterator returning relative paths of netcdf file wrt data_root
    """
    while data_root[-1] == "/":
        data_root = data_root[:-1]
    pos = len(data_root) + 1
    for root, folders, files in os.walk(data_root):        
        for rel_path in files:
            if rel_path.endswith(".nc"):
                yield os.path.join(root[pos:], rel_path)


def add_line(path, line):
    f = open(path, "a")
    f.write(line)
    f.close()


def get_size(path):
    return os.stat(path).st_size


def get_mtime(path):
    return os.stat(path).st_mtime

