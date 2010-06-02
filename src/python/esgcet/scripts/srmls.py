#!/usr/bin/env python

import sys, subprocess
import getopt
from esgcet.config import loadConfig
from esgcet.exceptions import *

usage = """Usage:
    srmls.py [options] directory

    Run the srm-ls command. The following configuration options are used:
      srmls = location of srm-ls
      srm_server = SRM server URL
      srm_archive = archive containing tbe directory

Arguments:
    directory: A directory to list.

Options:

    --config-section section
        Configuration file section containing lister options. Defaults to 'srmls'.

    --echo
        Echo the srm-ls command.

    --recursive yes|no
        List the contents of the directory recursively (default: yes)
        
"""

def SRMIterator(f, prefix):
    line = f.readline()
    path = ""
    len_prefix = len(prefix)
    while line:
        if line[0:15]=="SRM-CLIENT*SURL":
            path = line[16+len_prefix:-1]
        elif line[0:16]=="SRM-CLIENT*BYTES":
            bytes = line[17:-1]
            yield (path, bytes)
        elif line[0:22]=="SRM-CLIENT*FILE_STATUS" and line[23:34]!="SRM_SUCCESS":
            message = line[23:]
            raise ESGPublishError("Error listing %s: %s"%(path, message))
        line = f.readline()
    return

def main(argv):

    try:
        args, lastargs = getopt.getopt(argv, "", ['config-section=', 'echo', 'recursive='])
    except getopt.error:
        print sys.exc_value
        print usage
        sys.exit(0)

    configSection = "srmls"
    echo = False
    recurse = True
    for flag, arg in args:
        if flag=='--config-section':
            configSection = arg
        elif flag=='--echo':
            echo = True
        elif flag=='--recursive':
            recurse = (arg.lower()=="yes")

    if len(lastargs)==0:
        print "No directory specified."
        print usage
        sys.exit(0)

    if recurse:
        recurseOption = "-recursive"
    else:
        recurseOption = ""

    config = loadConfig(None)
    command = config.get(configSection, 'srmls')
    offline_proxy = config.get(configSection, 'srm_server')
    archive = config.get(configSection, 'srm_archive')
    srm_prefix = "%s?SFN=%s"%(offline_proxy, archive)
    echo_args = "-storageinfo %s -s '%s?SFN=%s%s'"%(recurseOption, offline_proxy, archive, lastargs[0])
    command_args = "-storageinfo %s -s %s?SFN=%s%s"%(recurseOption, offline_proxy, archive, lastargs[0])

    if echo:
        print '%s %s'%(command, echo_args)
        sys.exit(0)

    try:
        f = subprocess.Popen([command, command_args], stdout=subprocess.PIPE).stdout
    except:
        raise ESGPublishError("Error running command '%s %s': check configuration option 'srmls'"%(command, command_args))
        
    for path, size in SRMIterator(f, srm_prefix):
        print path, size
    f.close()

if __name__=='__main__':
    main(sys.argv[1:])
