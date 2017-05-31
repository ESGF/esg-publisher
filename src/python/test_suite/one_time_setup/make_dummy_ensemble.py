#!/usr/bin/env python

import sys
import os
import uuid
import shutil

class MakeDummyEnsemble(object):

    """
    Class to create a dummy ensemble. Given the directory containing subdirectories 
    for each member, the name of a template member, and a pattern for the name of 
    the members to be created, it will create the subdirectories, copying all the 
    data files from the template member but replacing the member name as part of the 
    filename, and also running 'ncatted' to replace the tracking_id global attribute 
    with a newly generated UUID.
    """

    def __init__(self, size, ensemble_dir, template_member_name, new_member_pattern, start=0):
        self.size = size
        self.start = start
        self.ensemble_dir = ensemble_dir
        self.template_member_name = template_member_name
        self.member_pattern = new_member_pattern
        self.template_member_dir = self.get_member_dir(template_member_name)

    def make_ensemble(self):        
        "make the whole ensemble"
        self.get_nc_rel_paths()
        for i in range(self.start, self.start + self.size):
            print "\r%d/%d" % (i, self.size),
            sys.stdout.flush()
            self.make_member(i)
        print

    def make_member(self, i):        
        "make the i'th member of the ensemble"
        member_name = self.get_member_name(i)
        member_dir = self.get_member_dir(member_name)
        if os.path.exists(member_dir):
            shutil.rmtree(member_dir)
        for nc_rel_path in self.nc_rel_paths:
            in_path = os.path.join(self.template_member_dir, nc_rel_path)
            out_path = os.path.join(member_dir, nc_rel_path.replace(self.template_member_name, member_name))
            self.ensure_parent_dir(out_path)
            os.system("ncatted -a tracking_id,global,m,c,%s %s %s" %
                      (uuid.uuid1(), in_path, out_path))

    def get_nc_rel_paths(self):
        "Scans template dir for .nc files, writing file list to self.nc_rel_paths"
        self.nc_rel_paths = []
        pos = len(self.template_member_dir)
        for root, dirs, files in os.walk(self.template_member_dir, topdown=False):
            assert root.startswith(self.template_member_dir)
            relroot = root[pos + 1:]
            for file in files:
                if file.endswith(".nc"):
                    self.nc_rel_paths.append(os.path.join(relroot, file))

    def get_member_name(self, i):
        return self.member_pattern.replace("MEMBER", str(i))

    def get_member_dir(self, member_name):
        return os.path.join(self.ensemble_dir, member_name)

    def ensure_parent_dir(self, path):
        dname = os.path.dirname(path)
        if not os.path.isdir(dname):
            os.makedirs(dname)
    

if __name__ == '__main__':
    ensmaker = MakeDummyEnsemble(100, 
                                 '../test_data/data/cmip5/output1/ESGF-PWT-TEST/MPI-ESM-P/abrupt4xCO2/fx/ocean/fx/',
                                 'r0i0p0',
                                 'r0i99pMEMBER')
    ensmaker.make_ensemble()
    
