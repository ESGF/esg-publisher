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
# from my-publisher.gen-five.src.esgcet.config import cmip6_handler as prep
# import cmip6_handler as prep
# TODO: running into file dependency errors with internal representation of PrePARE


def prepare(fm_file, cmor_tables):
    print("Iterating through filenames for PrePARE...")
    for line in fm_file:  # iterate through mapfile files for PrePARE -- import PrePARE and run natively
        # see cmip6_handler.py for help -- error with file dependencies
        split_line = line.split(" | ")
        filename = split_line[2]
        command = "PrePARE --table-path " + cmor_tables + " " + filename
        os.system(command)  # subprocess module?? change this perhaps
        # issue with subprocess: output not as easily shown
        # prep.validateFile(fm_file)
    print("Done.")

def exit_cleanup():
    scan_file.close()
    fullmap_file.close()


def main(args):
    if len(args) < 2:
        print("Usage: python3 publish_script.py </path/to/mapfile> <project>")

    os.system("export LD_LIBRARY_PATH=$CONDA_PREFIX/lib")  # this isn't working for some reason ...

    fullmap = args[0]  # full mapfile path
    # allow handling of multiple mapfiles later

    proj = args[1]
    cmip6 = False
    if proj == "CMIP6":
        cmip6 = True

    scan_file = tempfile.NamedTemporaryFile()  # create a temporary file which is deleted afterward for autocurator
    scanfn = scan_file.name  # name to refer to tmp file

    cmor_tables = input("Path to cmor tables: ")  # interactive script, should require no internal editing
    autocurator = input("Path to autocurator: ")  # so we just get variable paths from user

    autoc_command = autocurator + "/bin/autocurator"  # concatenate autocurator command

    os.system("cert_path=./cert.pem")  # TODO: fix this

    fullmap_file = open(fullmap, 'r')  # open file object for PrePARE
    if cmip6:
        try:
            prepare(fullmap_file, cmor_tables)
        except Exception as ex:
            print("Error with PrePARE: " + ex)
            exit_cleanup()
            exit(1)

    # Run autocurator and all python scripts
    print("Running autocurator...")
    os.system("bash gen-five/src/python/autocurator.sh " + autoc_command + " " + fullmap + " " + scanfn)

    print("Done.\nConverting mapfile...")
    try:
        map_json_data = mp.main([fullmap, proj])
    except Exception as ex:
        print("Error with converting mapfile: " + ex)
        exit_cleanup()
        exit(1)

    print("Done.\nMaking dataset...")
    try:
        out_json_data = mkd.main([map_json_data, scanfn])
    except Exception as ex:
        print("Error making dataset: " + ex)
        exit_cleanup()
        exit(1)

    if cmip6:
        print("Done.\nRunning pid cite...")
        try:
            out_json_data = pid.main(out_json_data)
        except Exception as ex:
            print("Error running pid cite: " + ex)

    print("Done.\nUpdating...")
    try:
        up.main(out_json_data)
    except Exception as ex:
        print("Error updating: " + ex)
        exit_cleanup()
        exit(1)

    print("Done.\nRunning pub test...")
    try:
        pt.main(out_json_data)
    except Exception as ex:
        print("Error running pub test: " + ex)
        exit_cleanup()
        exit(1)

    print("Done. Cleaning up.")
    exit_cleanup()


if __name__ == '__main__':
    main(sys.argv)
