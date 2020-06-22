import mapfile as mp
import mk_dataset as mkd
import update as up
import pub_test as pt
import pid_cite_pub as pid
import os
import json
import sys
import tempfile
sys.path.insert(1, '../../../src/python/esgcet/esgcet/config')
import cmip6_handler as prep

def prepare(fm_file):
    save = True
    print("Iterating through filenames for PrePARE...")
    for line in fm_file:  # iterate through mapfile files for PrePARE -- import PrePARE and run natively
        # see cmip6_handler.py for help
        split_line = line.split(" | ")
        filename = split_line[2]
        if save:
            path = filename
            save = False
        # command = "PrePARE --table-path " + cmor_tables + " " + filename
        # os.system(command)  # subprocess module?? change this perhaps
        prep.validateFile(filename)

    return path

def exit_cleanup():
    scan_file.close()
    fullmap_file.close()


if len(sys.argv) < 1:
    print("Usage: python3 publish_script.py </path/to/mapfile>")

fullmap = sys.argv[1]  # full mapfile path
# allow handling of multiple mapfiles later
proj = "CMIP6"  # needed for mapfile.py
# if not cmip6 PrePARE and pid aren't necessary -- take proj as argument in final product
basename = str(os.path.basename(fullmap))  # base dir of full map directory

scan_file = tempfile.NamedTemporaryFile()  # create a temporary file which is deleted afterward for autocurator
scanfn = scan_file.name  # name to refer to tmp file

cmor_tables = input("Path to cmor tables: ")  # interactive script, should require no internal editing
autocurator = input("Path to autocurator: ")  # so we just get variable paths from user

autoc_command = autocurator + "/bin/autocurator --out_pretty --out_json " + scanfn  # concatenate autocurator command

os.system("cert_path=./cert.pem")  # TODO: fix this

os.system("export LD_LIBRARY_PATH=$CONDA_PREFIX/lib")  # this isn't working for some reason ...

fullmap_file = open(fullmap, 'r')  # open file object for PrePARE
try:
    path = prepare(fullmap_file)
except Exception as ex:
    print("Error with PrePARE: " + ex)
    exit_cleanup()
    exit(1)


datasetdir = os.path.dirname(path) + "/*.nc"  # TODO: fix -- autocurator having issues with *
# temporary fix:
dataset_test = "/p/css03/esgf_publish/CMIP6/CMIP/NCAR/CESM2/historical/r2i1p1f1/Emon/cTotFireLut/gn/v20190308/cTotFireLut_Emon_CESM2_historical_r2i1p1f1_gn_185001-201412.nc"

# Run autocurator and all python scripts
print("Done.\nRunning autocurator...")
os.system(autoc_command + " --files " + dataset_test)

# print("Printing contents of scanfn")
# os.system("cat " + scanfn)

print("Done.\nConverting mapfile...")
map_json_data = mp.main([fullmap, proj])

print("Done.\nMaking dataset...")
out_json_data = mkd.main([map_json_data, scanfn])

print("Done.\nRunning pid cite...")
out_json_data = pid.main(out_json_data)

print("Done.\nUpdating...")
up.main(out_json_data)

print("Done.\nRunning pub test...")
pt.main(out_json_data)

print("Done. Cleaning up.")
exit_cleanup()
