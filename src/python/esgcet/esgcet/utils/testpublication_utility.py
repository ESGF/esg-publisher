import os
import time
import socket
import urllib2
import logging
import getpass

from subprocess import Popen, PIPE
from pyesgf.search import SearchConnection
from esgcet.exceptions import *
from esgcet.messaging import debug, info, warning, error, critical, exception
from esgcet.publish import checksum
from esgcet.model import DatasetVersion

import requests

def check_permission(path, dir=True):
    """
    Check if current user has write access to a directory

    :param str path: The file or directory to check
    :param bool dir: Flag if path is a file or a directory
    :returns: True iff the directory is writeable by current user, otherwise returns False
    :rtype: *boolean*

    """
    if dir:
        if os.path.isdir(path) and os.access(path, os.W_OK):
            return True
    else:
        if os.path.isfile(path):
            if os.access(path, os.W_OK):
                return True
        else:
            if os.access(os.path.dirname(path), os.W_OK):
                return True
    return False


def get_test_file(test_file_location, target_checksum):
    """
    Fetch test file if not already present.

    :param str test_file_location: The directory where the testfile will be downloaded to
    :param str target_checksum: The checksum to be compared with
    :returns: True iff the download was successful, otherwise returns False
    :rtype: *boolean*

    """
    url = 'http://distrib-coffee.ipsl.jussieu.fr/pub/esgf/dist/externals/sftlf.nc'
    if not os.path.isfile(test_file_location) or checksum(test_file_location, 'sha256sum') != target_checksum:
        print 'Not found.',
        cmd = ['wget', '-O', test_file_location, url]
        success = execute_cmd(cmd)
        if not checksum(test_file_location, 'sha256sum') == target_checksum or not success:
            return False
    return True


def execute_cmd(cmd):
    """
    Run a command with subprocess.Popen and check for errors in stderr.

    :param list cmd: The command to run
    :returns: The stderr error message, if any
    :returns: True iff the download was successful, otherwise returns False
    :rtype: *boolean* and *str*

    """
    print 'Running "%s"...' % ' '.join(cmd),
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    if ('Traceback' in stderr) or (cmd[1] == 'esgprep' and 'Scan completed' not in stderr):
        err_msg = 'ERROR:\n%s' % stderr
        return False, err_msg
    return True, None


def check_mapfile(mapfile_path, dataset_name):
    """
    Check if any line in mapfile matches the expected test values.

    :param str mapfile_path: The mapfile path
    :param str dataset_name: The dataset name
    :returns: True iff at least one line in the mapfile matches the expected values, otherwise returns False
    :rtype: *boolean*

    """
    with open(mapfile_path, 'r') as f:
        for line in f:
            if line.strip().startswith('%s | /esg/data/test/sftlf.nc | 143540 |' % dataset_name):
                return True
    return False


def check_postgres(session, dataset_name_version):
    """
    Check whether a dataset is published to the Postgres Database or not.

    :param session session: A database session
    :param str dataset_name_version: The dataset name including the version
    :returns: True iff the dataset was found in the database
    :rtype: *boolean*

    """
    dset = session.query(DatasetVersion).filter_by(name=dataset_name_version, version=1).first()
    if dset:
        return True
    return False


def check_thredds(thredds_url):
    """
    Check whether a dataset is published to the THREDDS catalogs.

    :param str thredds_url: The final url of a dataset's THREDDS catalog
    :returns: True iff the THREDDS catalog was found on the server, otherwise returns False
    :rtype: *boolean*

    """
    try:
        fh = urllib2.urlopen(thredds_url)
        response = fh.read()
        return True
    except urllib2.HTTPError, e:
        return False


def check_index(index_node, dataset_name, publish):
    """
    Check whether a dataset is published to the Solr Index or not.

    :param str index_node: The index node to check
    :param str dataset_name: The dataset name
    :param bool publish: True if check for existence, False otherwise
    :returns: True iff the dataset was successfully published or unpublished from Solr, otherwise returns False
    :rtype: *boolean*

    """
    if publish:
        hit_count_num = 1
    else:
        hit_count_num = 0

    conn = SearchConnection('http://%s/esg-search' % index_node, distrib=False)
    limit = 50
    i = 0
    while i < limit:
        i += 1
        ctx = conn.new_context(master_id=dataset_name, data_node=socket.gethostname())
        if ctx.hit_count == hit_count_num:
            return True
        elif i < limit:
            print '.',
            time.sleep(10)
    return False

def test_download():
    resp = requests.get('http://localhost/thredds/fileServer/esg_dataroot/test/sftlf.nc')
    if resp.status_code == 200:
        return True
    return False