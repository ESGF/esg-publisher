import mapfile as mp
import mk_dataset as mkd
import update as up
import pub_test as pt
import pid_cite_pub as pid
import os
import json
import sys
import tempfile
import subprocess
from cmip6_cv import PrePARE


def prepare_internal(json_map, cmor_tables):
    print("iterating through filenames for PrePARE (internal version)...")
    validator = PrePARE.PrePARE
    for info in json_map:
        filename = info[1]
        # file_cmor_version = fm_file.getAttribute('cmor_version', None) skipping for now
        # data_specs_version = fm_file.getAttribute('data_specs_version', None) might not be necessary
        process = validator.checkCMIP6(cmor_tables)
        process.ControlVocab(filename)


def prepare(fm_file, cmor_tables):
    print("Iterating through filenames for PrePARE...")
    for line in fm_file:  # iterate through mapfile files for PrePARE -- import PrePARE and run natively
        # see cmip6_handler.py for help -- error with file dependencies
        split_line = line.split(" | ")
        filename = split_line[1]
        command = "PrePARE --table-path " + cmor_tables + " " + filename
        os.system(command)  # subprocess module?? change this perhaps
        # issue with subprocess: output not as easily shown
        # prep.validateFile(fm_file)
    print("Done.")


def exit_cleanup(scan_file, fullmap_file):
    scan_file.close()
    fullmap_file.close()


def main(args):

    fullmap = args[2]  # full mapfile path
    split_map = fullmap.split("/")
    fname = split_map[-1]
    fname_split = fname.split(".")
    proj = fname_split[0]
    cmip6 = False
    if proj == "CMIP6":
        cmip6 = True

    scan_file = tempfile.NamedTemporaryFile()  # create a temporary file which is deleted afterward for autocurator
    scanfn = scan_file.name  # name to refer to tmp file

    cmor_tables = input("Path to cmor tables: ")  # interactive script, should require no internal editing
    autocurator = input("Path to autocurator: ")  # so we just get variable paths from user

    autoc_command = autocurator + "/bin/autocurator"  # concatenate autocurator command

    os.system("cert_path=./cert.pem")

    print("Converting mapfile...")
    try:
        map_json_data = mp.main([fullmap, proj])
    except Exception as ex:
        print("Error with converting mapfile: " + str(ex))
        exit_cleanup(scan_file, fullmap_file)
        exit(1)
    fullmap_file = open(fullmap, 'r')  # open file object for PrePARE
    print("Done.")

    if cmip6:
        try:
            prepare_internal(map_json_data, cmor_tables)
        except Exception as ex:
            print("Error with PrePARE: " + str(ex))
            exit_cleanup(scan_file, fullmap_file)
            exit(1)

    # Run autocurator and all python scripts
    print("Running autocurator...")
    os.system("bash gen-five/src/python/autocurator.sh " + autoc_command + " " + fullmap + " " + scanfn)

    print("Done.\nMaking dataset...")
    try:
        out_json_data = mkd.main([map_json_data, scanfn])
    except Exception as ex:
        print("Error making dataset: " + str(ex))
        exit_cleanup(scan_file, fullmap_file)
        exit(1)

    if cmip6:
        print("Done.\nSkipping pid cite...")
        # try:
        # out_json_data = pid.main(out_json_data)
        """except Exception as ex:
            print("Error running pid cite: " + str(ex))
            exit_cleanup(scan_file, fullmap_file)
            exit(1)"""

    print("Done.\nUpdating...")
    try:
        up.main(out_json_data)
    except Exception as ex:
        print("Error updating: " + str(ex))
        exit_cleanup(scan_file, fullmap_file)
        exit(1)

    print("Done.\nRunning pub test...")
    try:
        pt.main(out_json_data)
    except Exception as ex:
        print("Error running pub test: " + str(ex))
        exit_cleanup(scan_file, fullmap_file)
        exit(1)

    print("Done. Cleaning up.")
    exit_cleanup(scan_file, fullmap_file)


if __name__ == '__main__':
    args = sys.argv
    if len(args) < 3 or args[1] != "--map":
        print("Usage: python3 publish_script.py --map </path/to/mapfile>")
        exit(1)

    # os.system("export LD_LIBRARY_PATH=$CONDA_PREFIX/lib")  # this isn't working for some reason ...

    fullmap = args[2]  # full mapfile path
    # allow handling of multiple mapfiles later
    if fullmap[-1] == "/":
        pass
        # iterate through file in directory calling mai
    else:
        main(args)
