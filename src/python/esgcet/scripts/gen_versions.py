#/usr/bin/env python

import sys


usage = """this is a utility script for creating a version map from a esgpublisher
'map' file, where the version number is indicated in the 12th level subdirectory, as used by cmip5 naming conventions.

Usage:
    python gen_version.py <map_file>

"""

if len(sys.argv) < 2:

    print usage


    exit(1)




ver_field = 12



for line in open(sys.argv[1]):
    parts = line.split(" | ")

    pp=parts[1].split("/")

    verno = pp[ver_field]

    print parts[0] + " | " + verno[1:]





