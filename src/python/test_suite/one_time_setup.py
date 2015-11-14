import utils.test_suite_config as conf
from utils.esg_config import default_config_path as esgini
from one_time_setup.simple_mapfile_gen import gen_all_mapfiles

mapfile_dir = conf.get_mapfile_dir()
data_root = conf.get_data_root()

gen_all_mapfiles(data_root, mapfile_dir)

print """
Mapfiles for test publication are set up.


You also need to:

(1) ensure that the following directory is listed in 
    in %s under thredds_dataset_roots:

      %s

    (For example, modify esg_testroot, or add esg_testroot2.)

(2) Obtain a certificate (required for publication to the
    index node) and store at ~/.globus/certificate_file
    - see instructions at [[FIXME: where]]

Then you will be ready to run the test suite.

""" % (esgini, data_root)
