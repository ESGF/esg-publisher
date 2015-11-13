import os
import re
import cdms2
import hashlib

from publication_objects import Dataset, File

def dset_from_mapfile(path, ds_version=None,
                      verify_sizes=True,
                      verify_checksums=False,
                      return_list=False):
    """
    Parse mapfile and netCDF files listed in it, and return a Dataset object.
    Expect to find one dataset and return it, but if return_list=True then 
    instead return list of Dataset objects.

    Unless verify_checksums is set to true, assume that checksums in the 
    mapfile can be believed (avoid slow checksumming as we are testing 
    publication, not mapfile integrity...)
    """
    if ds_version == None:
        ds_version = version_from_mapfile_name(path)

    dsets = {}
    fh = open(path)
    for line in fh:
        (dsid, file_path, size), kwitems = parse_mapfile_line(line)
        size = int(size)
        if dsid not in dsets:
            dsets[dsid] = Dataset(dsid, ds_version)
        cksum = kwitems['checksum']
        tracking_id = get_tracking_id(file_path)
        filename = os.path.basename(file_path)
        if verify_sizes:
            assert size == get_size(file_path)
        if verify_checksums:
            cksum_type = kwitems['checksum_type']
            assert cksum == get_cksum(file_path, cksum_type)
        dsets[dsid].add_file(File(filename, size, cksum, tracking_id))
    fh.close()
    dslist = dsets.values()
    if return_list:
        return dslist
    else:
        assert len(dslist) == 1
        return dslist[0]

def get_size(path):
    return os.stat(path).st_size

def get_cksum(path, cksum_type):
    func = getattr(hashlib, cksum_type.lower())  # hashlib.md5 or hashlib.sha256
    h = func()
    f = open(path)
    while True:
        data = f.read(10240)
        if not data:
            break
        h.update(data)
    f.close()
    return h.hexdigest()

def get_tracking_id(path):
    """
    read tracking ID from a netCDF file
    """
    f = cdms2.open(path)
    tracking_id = f.tracking_id
    f.close()
    return tracking_id


_version_re = re.compile(".*\.v([0-9]+)(.map)?$")

def version_from_mapfile_name(path):
    """
    Dataset version from mapfile path assuming it ends .v<version> or
    .v<version>.map
    """
    m = _version_re.match(path)
    if not m:
        raise ValueError("%s does not contain version number" % path)
    return int(m.group(1))
    
   

_mf_splitter = re.compile("\s+\|\s+").split

def parse_mapfile_line(line):
    bits = _mf_splitter(line.replace("\n", ""))
    positional = []
    keyword = {}
    for bit in bits:
        try:
            pos = bit.index("=")
        except ValueError:
            positional.append(bit)
        else:
            keyword[bit[:pos]] = bit[pos + 1 :]
    return positional, keyword


if __name__ == '__main__':

    path = "/badc/cmip5/metadata/mapfiles/by_name/cmip5/output1/CSIRO-QCCCE/CSIRO-Mk3-6-0/historical/cmip5.output1.CSIRO-QCCCE.CSIRO-Mk3-6-0.historical.mon.land.Lmon.r5i1p1.v1"

    print dset_from_mapfile(path)
    
