#!/usr/bin/env python2.7

"""
Produces a set of test netCDF files for use in ESGF publication, based on some 
real input data.

For further info on what it does, see gen_test_file.__doc__

For further info on how to use it, see gen_all_test_data.__doc__
"""

import os
import re
import string
import netCDF4
import numpy
import random
import uuid

#import pdb

def gen_test_file(input_path,
                  output_path,
                  num_lons = 2,
                  num_lats = 2,
                  num_other_axis = 2,
                  first_lon_val = 60.,
                  first_lat_val = 30.,
                  first_other_axis_index = 0):
    """
    Generate a subsetted file with number of lons and lats specified,
    given the coords of the first lon and lat (uses nearest gridpoint).

    It will also remove any attributes containing an email address, and 
    add to the history to say what has been done.

    It will replace the tracking ID with a new one.

    And it will modify the data by adding large-amplitude noise.
    """
    dsin = netCDF4.Dataset(input_path)
    dsout = netCDF4.Dataset(output_path, "w", format=dsin.file_format)
    copy_attrs(dsin, dsout)

    att_name = 'tracking_id'
    if hasattr(dsin, att_name):
        setattr(dsout, att_name, str(uuid.uuid1()))

    overwritten_vars = []
    for varname in dsin.variables:
        if overwrite_this_variable(varname, dsin):
            overwritten_vars.append(varname)

    value = "For test purposes, subsetted in lon and lat"

    if overwritten_vars:
        value += (" and overwrote the following vars with random data: %s." % 
                  string.join(overwritten_vars, ", "))
    try:
        history = "%s %s" % (dsin.history, value)
    except AttributeError:
        history = value
    dsout.history = history
    dsout.comment = "DUMMY DATA. See history."

    subsetting = { "longitude": (get_nearest_index, first_lon_val, num_lons),
                   "latitude": (get_nearest_index, first_lat_val, num_lats),
                   "time": None,
                   "default": (None, first_other_axis_index, num_other_axis) }

    coords = find_coords(dsin)
    subsets = get_subsets(coords, subsetting)

    print "Subsetting:"
    for dimname, (first, num) in subsets.iteritems():
        print "  %s: first index %s, length %s" % (dimname, first, num)

    print "Variables:"
    copy_dims(dsin, dsout, subsets)
    for varname in dsin.variables:
        overwrite = (varname in overwritten_vars)
        copy_var(varname, dsin, dsout, subsets, overwrite)
        if overwrite:
            print "  write fake %s" % varname
        else:
            print "  copy %s" % varname
    dsout.close()
    dsin.close()



def copy_var(name, dsin, dsout, subsets, write_random):
    """
    copy variable between two datasets, taking into account subsetting 
    and optionally deliberate overwrite with random values
    """
    var_in = dsin.variables[name]
    var_out = dsout.createVariable(name, var_in.datatype, var_in.dimensions)
    copy_attrs(var_in, var_out)
    
    if write_random:
        sizes = []
        for dimname in var_in.dimensions:
            if dimname in subsets:
                offset, count = subsets[dimname]
                sizes.append(count)
            else:
                dim = dsin.dimensions[dimname]
                sizes.append(len(dim))
        var_out[:] = numpy.random.rand(*sizes)
    else:
        slices = []
        for dimname in var_in.dimensions:
            if dimname in subsets:
                offset, count = subsets[dimname]
                slices.append(slice(offset, offset + count))
            else:
                slices.append(slice(None))
        var_out[:] = var_in[slices]


def overwrite_this_variable(name, ds):
    """
    Test whether to write random data instead of the variable values.
    
    returns True if the first dimension is unlimited and the variable is not 
    a coordinate variable and does not end with '_bnds' or '_bounds'
    """
    var = ds.variables[name]
    dim_names = var.dimensions

    if not dim_names:
        # scalar
        return False

    if not ds.dimensions[dim_names[0]].isunlimited():
        return False

    if len(dim_names) == 1 and name == dim_names[0]:
        # coord var
        return False

    if name.endswith("_bnds") or name.endswith("_bounds"):
        return False

    return True


def get_subsets(coords, subsetting):
    """
    Given coordinate and dictionary looking up from standard name to 
    required first axis value and number of axis values,
    returns dictionary of dim_name -> (offset, count)
    
    (num_vals is not used for calculations, and is just copied into count)
    """
    subsets = {}
    for coord in coords:
        name, dim, var = coord
        try:
            indices = subsetting[var.standard_name]
        except (KeyError, AttributeError):
            indices = subsetting["default"]
        if not indices:
            continue
        func, first_val, num_vals = indices
        if func:
            first_val = func(var, first_val)
        subsets[name] = (first_val, num_vals)
    return subsets


def get_nearest_index(var, value):
    """
    get nearest index to specified value, of variable known to be
    1-dimensional
    """
    return (numpy.abs(var[:] - value)).argmin()
    


def find_coords(ds):
    """
    Find all the coordinate variables
    Returns a list of (name, dim, var) tuples
    """
    coords = []
    for name, dim in ds.dimensions.iteritems():
        if name in ds.variables:
            var = ds.variables[name]
            if var.dimensions == (name,):
                coords.append((name, dim, var))
    return coords
    

def copy_dims(dsin, dsout, subsets):
    """
    Copy dimensions, taking account of any subsetting.
    """
    for name, dim in dsin.dimensions.iteritems():
        if dim.isunlimited():
            dsout.createDimension(name, None)
        else:
            if name in subsets:
                length = subsets[name][1]
            else:
                length = len(dim)
            dsout.createDimension(name, length)
    

def copy_attrs(obj_in, obj_out):
    """
    Copy all attributes between two netCDF objects - which could be 
    Dataset (for global attributes) or Variable, but masking anything that 
    looks like an email address.
    """
    for attr in obj_in.ncattrs():
        obj_out.setncattr(attr, remove_email(obj_in.getncattr(attr)))


email_re = re.compile("[^@\s]+@[^@\s]+\.[^@\s]+")

def remove_email(value):
    if not isinstance(value, str) and not isinstance(value, unicode):
        return value
    return email_re.sub("[email address removed]", value)


def ensure_containing_dir(path):
    "Make sure the parent directory of path exists"
    parent = os.path.dirname(path)
    if parent:
        if not os.path.isdir(parent):
            ensure_containing_dir(parent)
            os.mkdir(parent)


def read_list(path):
    """
    read ascii file into a list of lines 
    with trailing whitespace and any commented out filenames removed
    """
    fh = open(path)
    sub = re.compile("\s+$").sub
    items = [sub("", x)  for x in fh]
    fh.close()
    return [x for x in items if not x.startswith("#")]


def gen_all_test_data(input_root = '/badc/cmip5/data',
                      input_list = 'input_files',
                      output_root = 'out',
                      fake_institute_name = 'ESGF-PWT-TEST',
                      model_prefix = 'DUMMY_',
                      file_prefix = 'DUMMY_',
                      **kwargs_for_gen_test_file):
    
    """
    Generate a set of test files, using the same DRS hierarchy as for
    the input paths, except that the institute is overwritten, and the
    model name has a prefix added, as does the filename.  The file
    specfied in input_list should contain a list of relative paths,
    and these should reflect the DRS. Specifically, the 3rd and 4th
    level directories in the relative path will be taken to be the
    institute and the experiment.
    """

    for path_rel in read_list(input_list):
        path_in = os.path.join(input_root, path_rel)
        if not os.path.exists(path_in):
            print "Input file %s does not exist - skipping" % path_in
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

        print "Converting %s" % path_in
        gen_test_file(path_in, path_out, **kwargs_for_gen_test_file)
        print "Wrote %s" % path_out
        print

if __name__ == '__main__':
    gen_all_test_data()
    #gen_all_test_data(input_root = 'swiftbrowser.dkrz.de/out/',
    #                  input_list = 'kb_files')
                      
