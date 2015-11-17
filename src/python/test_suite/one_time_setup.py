#!/usr/bin/env python

from utils import config
from utils.esg_config import default_config_path as esgini
from one_time_setup.simple_mapfile_gen import gen_all_mapfiles

mapfile_dir = config.get('test_mapfile_dir')
data_root = config.get('test_data_dir')

gen_all_mapfiles(data_root, mapfile_dir)

print """
Mapfiles for test publication are set up.


You also need to:

(1) in %s:

  (a) ensure that the following directory is listed in 
      under thredds_dataset_roots:

         %s

      (For example, modify esg_testroot, or add esg_testroot2.)

  (b) Ensure that the fake institute 'ESGF-PWT-TEST' is added under 
      [project:cmip5] institute_options, as the publications are 
      done under ESGF-PWT-TEST.

  and then run 'esginitialize -c'


(2) Obtain a certificate (required for publication to the
    index node) and store at ~/.globus/certificate_file
    - see instructions at [[FIXME: where]]

Then you will be ready to run the test suite.

""" % (esgini, data_root)
