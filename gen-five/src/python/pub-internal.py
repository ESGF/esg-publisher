import mapfile as mp
import mk_dataset as mkd
import update as up
import pub_test as pt
import pid_cite_pub as pid
import os
import json
import sys
import tempfile
from cmip6_cv import PrePARE
from settings import *

CMOR_PATH = "/export/witham3/cmor"

def run_ac(input_rec):
    cv_path = "{}/CMIP6_CV.json".format(CMOR_PATH)
    jobj = json.load(open(cv_path))["CV"]
    sid_dict = jobj["source_id"]

    src_id = input_rec['source_id']
    act_id = input_rec['activity_drs']

    if src_id not in sid_dict:
        return False

    rec = sid_dict[src_id]
    return act_id in rec["activity_participation"]


def run_ec(rec):
    cv_path = "{}/CMIP6_CV.json".format(CMOR_PATH)

    act_id = rec['activity_drs']
    exp_id = rec['experiment_id']

    cv_table = json.load(open(cv_path, 'r'))["CV"]
    if exp_id not in cv_table['experiment_id']:
        return False
    elif act_id not in cv_table['experiment_id'][exp_id]['activity_id'][0]:
        return False
    else:
        return True


def prepare_internal(json_map, cmor_tables):
    print("iterating through filenames for PrePARE (internal version)...")
    validator = PrePARE.PrePARE
    for info in json_map:
        filename = info[1]
        process = validator.checkCMIP6(cmor_tables)
        process.ControlVocab(filename)


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

    check_files(files)

    cert = CERT_FN

    scan_file = tempfile.NamedTemporaryFile()  # create a temporary file which is deleted afterward for autocurator
    scanfn = scan_file.name  # name to refer to tmp file

    # add these as command line args
    autocurator = AUTOC_PATH

    autoc_command = autocurator + "/bin/autocurator"  # concatenate autocurator command

    os.system("cert_path=" + cert)

    print("Converting mapfile...")
    # try:
    map_json_data = mp.main([fullmap, proj])
    """ except Exception as ex:
        print("Error with converting mapfile: " + str(ex))
        exit_cleanup(scan_file)
        exit(1) """
    print("Done.")

    # Run autocurator and all python scripts
    print("Running autocurator...")
    os.system("bash gen-five/src/python/autocurator.sh " + autoc_command + " " + fullmap + " " + scanfn)

    print("Done.\nMaking dataset...")
  #  try:
    out_json_data = mkd.main([map_json_data, scanfn])

    """except Exception as ex:
        print("Error making dataset: " + str(ex))
        exit_cleanup(scan_file)
        exit(1)"""
    print("Done, running ac")
    ac_valid = run_ac(out_json_data[-1])
    ec_valid = True
    if ac_valid:
        ec_valid = run_ec(out_json_data[-1])
    else:
        print("WARNING: Failed ac check.")
    if not ec_valid:
        print("WARNING: Failed ec check.")
    
    if cmip6:
        print("Done.\nRunning pid cite...")
        try:
            new_json_data = pid.main(out_json_data)
        except Exception as ex:
            print("Error running pid cite: " + str(ex))
            exit_cleanup(scan_file)
            exit(1)
    else:
        new_json_data = out_json_data

    print("Done.\nUpdating...")
    try:
        up.main(new_json_data)
    except Exception as ex:
        print("Error updating: " + str(ex))
        exit_cleanup(scan_file)
        exit(1)

    print("Done.\nRunning pub test...")
    try:
        pt.main(new_json_data)
    except Exception as ex:
        print("Error running pub test: " + str(ex))
        exit_cleanup(scan_file)
        exit(1)

    print("Done. Cleaning up.")
    exit_cleanup(scan_file)


if __name__ == '__main__':

    # os.system("export LD_LIBRARY_PATH=$CONDA_PREFIX/lib")  # this isn't working for some reason ...
    fullmap = sys.argv[2]  # full mapfile path
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
