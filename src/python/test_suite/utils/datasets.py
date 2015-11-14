# datasets.py - defines the test dataset ids, by reference to the mapfiles
# The list of files in them are read from the mapfiles.

import os

import test_suite_config
import esg_config
from read_filesystem import ReadFilesystem


_conf = esg_config.Config()
_rf = ReadFilesystem(_conf)
_mf_dir = test_suite_config.get_mapfile_dir()


def _get_ds(dsid, nfiles = None):

    mapfile_path = os.path.join(_mf_dir, dsid)

    ds = _rf.dset_from_mapfile(mapfile_path)

    if nfiles != None:
        # check expected number of files
        assert len(ds.files) == nfiles

    return ds


# Dataset 1, versions 1 & 2
d1v1 = _get_ds('cmip5.output1.ESGF-PWT-TEST.DUMMY_MPI-ESM-LR.esmFixClim1.mon.ocean.Omon.r1i1p1.v20111006', 2)
d1v2 = _get_ds('cmip5.output1.ESGF-PWT-TEST.DUMMY_MPI-ESM-LR.esmFixClim1.mon.ocean.Omon.r1i1p1.v20120625', 2)

# Dataset 2, versions 1 & 2
d2v1 = _get_ds('cmip5.output1.ESGF-PWT-TEST.DUMMY_MPI-ESM-P.abrupt4xCO2.fx.ocean.fx.r0i0p0.v20111028', 4)
d2v2 = _get_ds('cmip5.output1.ESGF-PWT-TEST.DUMMY_MPI-ESM-P.abrupt4xCO2.fx.ocean.fx.r0i0p0.v20120625', 5)

# Dataset 3 contains BAD Files
print "fixme: ds3 in datasets.py"
d3v1 = None


#all_datasets = (d1v1, d1v2, d2v1, d2v2, d3v1)
all_datasets = (d1v1, d1v2, d2v1, d2v2)
