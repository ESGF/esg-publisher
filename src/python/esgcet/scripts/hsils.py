#!/usr/bin/env python

import sys, subprocess
import getopt
from esgcet.config import loadConfig
from esgcet.exceptions import *

usage = """Usage:
    hsils.py [options] directory

    Run the hsi ls command. The following configuration options are used:
      hsi = location of hsi executable

Arguments:
    directory: A directory to list.

Options:

    --config-section section
        Configuration file section containing lister options. Defaults to 'hsi'.

    --echo
        Echo the hsils command.

    --help
        Print a help message.

    --recursive yes|no
        List the contents of the directory recursively (default: yes)
        
"""

def main(argv):

    try:
        args, lastargs = getopt.getopt(argv, "", ['config-section=', 'echo', 'help', 'recursive='])
    except getopt.error:
        print sys.exc_value
        print usage
        sys.exit(0)

    configSection = "hsi"
    echo = False
    recurse = True
    for flag, arg in args:
        if flag=='--config-section':
            configSection = arg
        elif flag=='--echo':
            echo = True
        elif flag=='--help':
            print usage
            sys.exit(0)
        elif flag=='--recursive':
            recurse = (arg.lower()=="yes")

    if len(lastargs)==0:
        print "No directory specified."
        print usage
        sys.exit(0)

    if recurse:
        recurseOption = "R"
    else:
        recurseOption = ""

    config = loadConfig(None)
    command = config.get(configSection, 'hsi')
    path = lastargs[0]
    command_args = "ls -1s%s %s"%(recurseOption, path)

    if echo:
        print '%s %s'%(command, command_args)
        sys.exit(0)

    try:
        errout = subprocess.Popen([command, command_args], stderr=subprocess.PIPE).stderr
    except:
        raise ESGPublishError("Error running command '%s %s': check configuration option 'hsi'"%(command, command_args))
    lines = errout.readlines()
    errout.close()

    printit = False
    for line in lines:
        if printit:
            if line[0]=='*':
                raise Exception("Error accessing %s: %s"%(path, line))
            if line[0]!='-':
                fields = line.split()
                print fields[1], fields[0]
        else:
            printit = (line[0:8]=="Username")

if __name__=='__main__':
    main(sys.argv[1:])
