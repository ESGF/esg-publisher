# datasets.py - defines the test dataset ids and their files

class DatasetForTests(object):

    def __init__(self, id, files):
        self.id = id
        self.files = files


# Dataset 1, versions 1 & 2
### THIS IS A BAD EXAMPLE - we need a small dataset with only one or two variables in it.
### And maybe we need a CORDEX example
d1v1 = DatasetForTests("cmip5.output1.MOHC.HadGEM2-ES.abrupt4xCO2.day.atmos.cfDay.r1i1p1.v20120114", (
        "rsds_cfDay_HadGEM2-ES_abrupt4xCO2_r1i1p1_18791201-18791230.nc",
        "rsds_cfDay_HadGEM2-ES_abrupt4xCO2_r1i1p1_19991201-19991230.nc",
    ))

d1v2 = DatasetForTests("foo.baa", (
        "baa_foo_2015.nc",
    ))

# Dataset 2, versions 1 & 2
d2v1 = DatasetForTests("foo.baa", (
        "baa_foo_2015.nc",
    ))

d2v2 = DatasetForTests("foo.baa", (
        "baa_foo_2015.nc",
    ))

# Dataset 3 contains BAD Files
d3v1 = DatasetForTests("foo.bad", (
        "bad_file_2015.nc",
    ))

all_datasets = (d1v1, d1v2, d2v1, d2v2, d3v1)
