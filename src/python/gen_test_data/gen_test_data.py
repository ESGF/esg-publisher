#!/usr/bin/env python2.7

import os
import re
import string
import netCDF4
import random


def gen_test_file(input_path,
                  output_path,
                  num_lons = 2,
                  num_lats = 2,
                  lon_sw = 60.,
                  lat_sw = 30.):
    """
    Generate a subsetted file with number of lons and lats specified,
    given the coords of the south-west corner (uses nearest gridpoint).

    It will also remove any attributes containing an email address, and 
    add a comment attribute.

    And it will modify the data by adding large-amplitude noise.
    """

def ensure_containing_dir(path):
    "Make sure the parent directory of path exists"
    parent = os.path.dirname(path)
    if parent:
        if not os.path.isdir(parent):
            ensure_containing_dir(parent)
            os.mkdir(parent)

def read_list(path):
    "read ascii file into a list of lines with trailing whitespace removed"
    fh = open(path)
    sub = re.compile("\s+$").sub
    items = [sub("", x)  for x in fh]
    fh.close()
    return items


def gen_all_test_data(input_root = '/badc/cmip5/data',
                      input_list = 'input_files',
                      output_root = 'out',
                      fake_institute_name = 'ESGF-PWT-TEST',
                      model_prefix = 'DUMMY_',
                      file_prefix = 'DUMMY_',
                      **kwargs_for_gen_test_file):
    
    """
    Generate a set of test files, putting them in the same DRS
    locations as the input paths.  The file specfied in input_list
    should contain a list of relative paths, and these should reflect
    the DRS. Specifically, the 3rd and 4th level directories in the
    relative path will be taken to be the institute and the experiment.
    """

    for path_rel in read_list(input_list):
        path_in = os.path.join(input_root, path_rel)
        if not os.path.exists(path_in):
            print "Input file %s does not exist - skipping"
            continue

        assert("//" not in path_rel)
        elements = path_rel.split("/")
        elements[2] = fake_institute_name
        elements[3] = model_prefix + elements[3]
        elements[-1] = file_prefix + elements[-1]

        path_out = os.path.join(output_root, *elements)
       
        try:
            ensure_containing_dir(path_out)
        except OSError:
            print "could not create containing directory for %s" % path_out
            continue

        print "Converting %s -> %s" % (path_in, path_out)
        gen_test_file(path_in, path_out, **kwargs_for_gen_test_file)


if __name__ == '__main__':
    gen_all_test_data()
