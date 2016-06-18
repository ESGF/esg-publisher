#!/usr/bin/env python

from utils import config
from utils.esg_config import default_config_path as esgini
from one_time_setup.simple_mapfile_gen import gen_all_mapfiles
from one_time_setup.make_dummy_ensemble import MakeDummyEnsemble

mapfile_dir = config.get('test_mapfile_dir')
data_root = config.get('test_data_dir')
host_certs_dir = config.get('host_certs_dir')

print "making ensemble for parallel test"
ensmaker = MakeDummyEnsemble(int(config.get('partest_ensemble_size')),
                             config.get('partest_ensemble_dir'),
                             config.get('partest_template_member'),
                             config.get('partest_member_pattern'))
ensmaker.make_ensemble()

print "making mapfiles"
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


(2) For both index and/or data node, if they use a self-signed 
    certificate for the https front end, then copy or link the 
    relevant host certificate into full_hostname.pem in the host-certs
    directory of the test suite: 
     %s

    Assuming that the test suite is run locally on the data node, 
    the one for the data node might be a symlink.  For example:

      cd %s
      ln -s /etc/certs/hostcert.pem `hostname -f`.pem
      scp index_node_hostname:/etc/certs/hostcert.pem index_node_hostname.pem

    This is not necessary if commercially signed certificates are used.


(3) Obtain a user certificate (required for publication to the
    index node) and store at ~/.globus/certificate_file.

    You can do this with:

        myproxy-logon \
             -b -l your_username -o ~/.globus/certificate-file \
             -s your_myproxy_host_name
    
        but myproxy-logon might not work as root, so to do it as root, 
        become another user with "su", run the command, and then 
        (as root again) copy the file into ~root/.globus/
    
    (This step may have to be repeated when the user certificate expires.)


(4) Ensure that the security on the index node is configured such that 
    this user (for whom the certificate has been obtained) has permission 
    to publish to the test dataset.

Then you will be ready to run the test suite.

""" % (esgini, data_root, host_certs_dir, host_certs_dir)
