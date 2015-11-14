import os
import ConfigParser

print "FIXME - hard-coded path in test_suite_config.py"

testdata_root = "/root/dev/esg-publisher/src/python/test_suite/test_data/"


def get_mapfile_dir():    
    return os.path.join(testdata_root, "mapfiles")

def get_data_root():    
    return os.path.join(testdata_root, "data")
