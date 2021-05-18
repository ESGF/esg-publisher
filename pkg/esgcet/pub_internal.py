from esgcet.args import PublisherArgs
import esgcet.esgmigrate as migrate
import os
import json
import sys
from esgcet.settings import *
import configparser as cfg
from pathlib import Path


def check_files(files):
    for file in files:
        try:
            myfile = open(file, 'r')
            myfile.close()
        except Exception as ex:
            print("Error opening file " + file + ": " + str(ex))
            exit(1)


def run(fullmap, pub_args):

    # SETUP
    split_map = fullmap.split("/")
    fname = split_map[-1]
    fname_split = fname.split(".")
    project = fname_split[0]

    files = []
    files.append(fullmap)

    check_files(files)

    argdict = pub_args.get_dict(fullmap)

    if argdict["proj"]:
        project = argdict["proj"]

    if project == "CMIP6":
        from esgcet.cmip6 import cmip6
        proj = cmip6(argdict)
    elif project == "non-nc":
        from esgcet.generic_pub import BasePublisher
        proj = BasePublisher(argdict)
    elif project == "generic" or project == "cordex":
        from esgcet.generic_netcdf import GenericPublisher
        proj = GenericPublisher(argdict)
    elif project == "CREATE-IP":
        from esgcet.create_ip import CreateIP
        proj = CreateIP(argdict)
    elif project == "CMIP5":
        from esgcet.cmip5 import cmip5
        proj = cmip5(argdict)
    else:
        print("Project " + project + "not supported.\nOpen an issue on our github to request additional project support.")
        exit(1)

    # ___________________________________________
    # WORKFLOW - one line call

    proj.workflow()


def main():
    pub_args = PublisherArgs()
    pub = pub_args.get_args()
    maps = pub.map  # full mapfile path
    if maps is None:
        print("Missing argument --map, use " + sys.argv[0] + " --help for usage.", file=sys.stderr)
        exit(1)
    for m in maps:
        if os.path.isdir(m):
            files = os.listdir(m)
            for f in files:
                if os.path.isdir(m + f):
                    continue
                run(m + f, pub_args)
        else:
            myfile = open(m)
            ismap = True
            first = True
            for line in myfile:
                # if parsed line is not mapfile line, run on each file
                if first:
                    if os.path.isfile(line):
                        ismap = False
                    else:
                        break
                    first = False

                length = len(line)
                run(line[0:length - 2], pub_args)
            myfile.close()
            if ismap:
                run(m, pub_args)


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
