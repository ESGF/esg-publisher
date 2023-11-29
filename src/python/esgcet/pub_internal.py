from esgcet.args import PublisherArgs
import os
import sys
import esgcet.logger as logger

log = logger.ESGPubLogger()
publog = log.return_logger('Publisher-Main')

from pathlib import Path

def check_files(files):
    for file in files:
        try:
            myfile = open(file, 'r')
            myfile.close()
        except Exception as ex:
            publog.exception("Error opening file " + file + ". Exiting.")
            exit(1)


def run(fullmap, pub_args):

        # SETUP
    split_map = fullmap.split("/")
    fname = split_map[-1]
    fname_split = fname.split(".")
    project_name = fname_split[0]

    files = []
    files.append(fullmap)

    check_files(files)

    argdict = pub_args.get_dict(project_name)
    argdict["fullmap"] = fullmap

    if argdict["verbose"]:
        publog.info(argdict)
    if "proj" in argdict:
        project_name = argdict["proj"]
    else:
        argdict["proj"] = project_name
    project = project_name.lower()
    user_defined = False
    if argdict["user_project_config"]:
        user_defined = True
    non_netcdf = False
    if argdict["non_nc"]:
        non_netcdf = True

    if project == "cmip6" or "cmip6-clone" in argdict:
        from esgcet.cmip6 import cmip6
        proj = cmip6(argdict)
    elif project == "create-ip":
        from esgcet.create_ip import CreateIP
        proj = CreateIP(argdict)
    elif project == "cmip5":
        from esgcet.cmip5 import cmip5
        proj = cmip5(argdict)
    elif project == "input4mips":
        from esgcet.input4mips import input4mips
        proj = input4mips(argdict)
    elif project == "e3sm" and not non_netcdf:
        from esgcet.e3sm import e3sm
        proj = e3sm(argdict)
    elif non_netcdf:
        from esgcet.generic_pub import BasePublisher
        proj = BasePublisher(argdict)
    elif project == "generic" or project == "cordex" or user_defined or project == "none":
        if project == "none" and not argdict['silent']:
            publog.info("Using default settings, project not specified.")
        from esgcet.generic_netcdf import GenericPublisher
        proj = GenericPublisher(argdict)
    else:
        publog.error("Project " + project + " not supported.\nOpen an issue on our github to request additional project support.")
        exit(1)

    # ___________________________________________
    # WORKFLOW - one line call

    return proj.workflow()


def main():
    pub_args = PublisherArgs()
    pub = pub_args.get_args()
    maps = pub.map  # full mapfile path
    if maps is None:
        publog.error("Missing argument --map, use " + sys.argv[0] + " --help for usage.")
        exit(1)

    rc = True
    for m in maps:
        if os.path.isdir(m):
            mappath = Path(m)
            files = os.listdir(m)
            for f in files:
                fullmappath = mappath / f
                if os.path.isdir(fullmappath):
                    continue # Do not recurse subdirectories
                rc = rc and run(str(fullmappath), pub_args)
        else:
            myfile = open(m)
            ismap = False
            first = True
            for line in myfile:
                # if parsed line is not mapfile line, run on each file
                if first:
                    if '#' in line:
                        ismap = True
                        break
                    first = False

                length = len(line)
                rc = rc and run(line[0:length - 1], pub_args)
            myfile.close()
            if ismap:
                rc = rc and run(m, pub_args)

    if not rc:
        exit(1)


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
