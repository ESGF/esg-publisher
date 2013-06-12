#!/usr/bin/env python

import sys, subprocess
import getopt
import os
from esgcet.config import loadConfig
from esgcet.exceptions import *

usage = """Usage:
    ls.py [options] directory

    Run the ls command. This is useful for debugging offline code
      without actual offline access.

Arguments:
    directory: A directory to list.

Options:

    --config-section section
        Configuration file section containing lister options. Defaults to 'ls'.

    --echo
        Echo the ls command.

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

    configSection = "ls"
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
    command = config.get(configSection, 'ls')
    path = lastargs[0]
    command_args = "-l%s"%recurseOption

    if echo:
        print '%s %s %s'%(command, command_args, path)
        sys.exit(0)

    try:
        errout = subprocess.Popen([command, command_args, path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout
    except:
        raise ESGPublishError("Error running command '%s %s': check configuration option 'ls'"%(command, command_args))
    lines = errout.readlines()
    errout.close()

    directory = path
    for line in lines:

        line = line.strip()

        # Skip blank lines
        if len(line)==0:
            continue

        # File
        elif line[0]=='-':
            fields = line.split()
            fullpath = os.path.join(directory, fields[-1])
            print fullpath, fields[4]

        # Directory
        elif line[0]=='/' and line[-1]==':':
            directory = line[:-1]

        # Error
        elif line[0]=='/':
            raise ESGPublishError("Error: %s"%line)

        # Skip
        else:
            continue

if __name__=='__main__':
    main(sys.argv[1:])
