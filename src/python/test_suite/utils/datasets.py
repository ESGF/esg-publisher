# datasets.py - defines the test dataset ids, by reference to the mapfiles
# The list of files in them are read from the mapfiles.

import os

from . import config
import esg_config
from read_filesystem import ReadFilesystem


_conf = esg_config.Config()
_rf = ReadFilesystem(_conf)
_mf_dir = config.get('test_mapfile_dir')


def _get_ds(dsid, nfiles = None):

    mapfile_path = os.path.join(_mf_dir, dsid)

    ds = _rf.dset_from_mapfile(mapfile_path)

    if nfiles != None:
        # check expected number of files
        assert len(ds.files) == nfiles

    return ds


# Dataset 1, versions 1 & 2
d1v1 = _get_ds('cmip5.output1.ESGF-PWT-TEST.MPI-ESM-LR.esmFixClim1.mon.ocean.Omon.r1i1p1.v20111006', 2)
d1v2 = _get_ds('cmip5.output1.ESGF-PWT-TEST.MPI-ESM-LR.esmFixClim1.mon.ocean.Omon.r1i1p1.v20120625', 2)

# Dataset 2, versions 1 & 2
d2v1 = _get_ds('cmip5.output1.ESGF-PWT-TEST.MPI-ESM-P.abrupt4xCO2.fx.ocean.fx.r0i0p0.v20111028', 4)
d2v2 = _get_ds('cmip5.output1.ESGF-PWT-TEST.MPI-ESM-P.abrupt4xCO2.fx.ocean.fx.r0i0p0.v20120625', 5)

# Dataset 3 contains BAD Files
print "fixme: ds3 in datasets.py"
d3v1 = None

#all_datasets = (d1v1, d1v2, d2v1, d2v2, d3v1)
all_datasets = (d1v1, d1v2, d2v1, d2v2)


# define a function to get a list of the parallel test datasets, but do not call it on import 
# as a little slow (has to read all the mapfiles) 0 can be called if actually running the 
# parallel test.
def get_parallel_test_datasets():

    ds_pattern = 'cmip5.output1.ESGF-PWT-TEST.MPI-ESM-P.abrupt4xCO2.fx.ocean.fx.r0i99p%s.%s'

    if config.is_set('partest_use_multi_version'):
        versions = ['v20111028', 'v20120625']
    else:
        versions = ['v20111028']

    datasets = []
    for version in versions:
        for member in range(int(config.get('partest_ensemble_size'))):
            print member
            datasets.append(_get_ds(ds_pattern % (member, version)))
    return datasets

