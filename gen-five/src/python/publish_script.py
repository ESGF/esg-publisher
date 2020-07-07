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
import args
import timeit


def prepare_internal(json_map, cmor_tables):
    print("iterating through filenames for PrePARE (internal version)...")
    validator = PrePARE.PrePARE
    for info in json_map:
        filename = info[1]
        # file_cmor_version = fm_file.getAttribute('cmor_version', None) skipping for now
        # data_specs_version = fm_file.getAttribute('data_specs_version', None) might not be necessary
        process = validator.checkCMIP6(cmor_tables)
        process.ControlVocab(filename)


# this function no longer in use
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


def check_files(files):
    for file in files:
        try:
            myfile = open(file, 'r')
        except Exception as ex:
            print("Error opening file " + file + ": " + str(ex))
            exit(1)
        myfile.close()


def exit_cleanup(scan_file):
    scan_file.close()


def wrapper(func, *args, **kwargs):
    def wrapped():
        return func(*args, **kwargs)
    return wrapped


def autocuratorf():
    os.system("bash gen-five/src/python/autocurator.sh " + autoc_command + " " + fullmap + " " + scanfn)


def main(fullmap):

    split_map = fullmap.split("/")
    fname = split_map[-1]
    fname_split = fname.split(".")
    proj = fname_split[0]
    cmip6 = False
    if proj == "CMIP6":
        cmip6 = True


    files = []
    files.append(fullmap)
    print(timeit.timeit(args.get_args, number=1))
    pub = args.get_args()
    third_arg_mkd = False
    if pub.json is not None:
        json_file = pub.json
        third_arg_mkd = True
        files.append(json_file)

    if cmip6 and pub.proj == "":
        print("Error: No CMOR tables for PrePARE. Required for CMIP6.")
        exit(1)
    check_files(files)

    if pub.set_replica and pub.no_replica:
        print("ERROR: Replica simultaneously set and disabled.")
        exit(1)
    cert = pub.cert

    scan_file = tempfile.NamedTemporaryFile()  # create a temporary file which is deleted afterward for autocurator
    scanfn = scan_file.name  # name to refer to tmp file

    # add these as command line args
    cmor_tables = pub.cmor_path
    autocurator = pub.autocurator_path

    autoc_command = autocurator + "/bin/autocurator"  # concatenate autocurator command

    os.system("cert_path=" + cert)

    print("Converting mapfile...")
    try:
        mymap = wrapper(mp.main, [fullmap, proj])
        print(timeit.timeit(mymap, number=1))
        map_json_data = mp.main([fullmap, proj])
    except Exception as ex:
        print("Error with converting mapfile: " + str(ex))
        exit_cleanup(scan_file)
        exit(1)
    print("Done.")

    if cmip6:
        try:
            prep = wrapper(prepare_internal, map_json_data, cmor_tables)
            print(timeit.timeit(prep, number=1))
            prepare_internal(map_json_data, cmor_tables)
        except Exception as ex:
            print("Error with PrePARE: " + str(ex))
            exit_cleanup(scan_file)
            exit(1)

    # Run autocurator and all python scripts
    print("Running autocurator...")
    print(timeit.timeit(autocuratorf, number=1))
    os.system("bash gen-five/src/python/autocurator.sh " + autoc_command + " " + fullmap + " " + scanfn)

    print("Done.\nMaking dataset...")
    try:
        if third_arg_mkd:
            out_json_data = mkd.main([map_json_data, scanfn, json_file])
        else:
            makedata = wrapper(mkd.main, [map_json_data, scanfn])
            print(timeit.timeit(makedata, number=1))
            out_json_data = mkd.main([map_json_data, scanfn])

    except Exception as ex:
        print("Error making dataset: " + str(ex))
        exit_cleanup(scan_file)
        exit(1)

    if cmip6:
        print("Done.\nRunning pid cite...")
        try:
            pidc = wrapper(pid.main, out_json_data)
            print(timeit.timeit(pidc, number=1))
            new_json_data = pid.main(out_json_data)
        except Exception as ex:
            print("Error running pid cite: " + str(ex))
            exit_cleanup(scan_file)
            exit(1)

    print("Done.\nUpdating...")
    try:
        upd = wrapper(up.main, new_json_data)
        print(timeit.timeit(upd, number=1))
        up.main(new_json_data)
    except Exception as ex:
        print("Error updating: " + str(ex))
        exit_cleanup(scan_file)
        exit(1)

    print("Done.\nRunning pub test...")
    try:
        pubt = wrapper(pt.main, out_json_data)
        print(timeit.timeit(pubt, number=1))
        pt.main(out_json_data)
    except Exception as ex:
        print("Error running pub test: " + str(ex))
        exit_cleanup(scan_file)
        exit(1)

    print("Done. Cleaning up.")
    exit_cleanup(scan_file)


if __name__ == '__main__':

    # os.system("export LD_LIBRARY_PATH=$CONDA_PREFIX/lib")  # this isn't working for some reason ...
    pub = args.get_args()
    fullmap = pub.map  # full mapfile path
    # allow handling of multiple mapfiles later
    if fullmap[-4:] != ".map":
        myfile = open(fullmap)
        for line in myfile:
            length = len(line)
            main(line[0:length-2])
        myfile.close()
        # iterate through file in directory calling main
    else:
        main(fullmap)
