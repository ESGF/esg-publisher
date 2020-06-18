import mapfile as mp
import mk_dataset as mkd
import update as up
import pub_test as pt
import os
import json
import sys
import tempfile


if len(sys.argv) < 1:
    print("Usage: python3 publish_script.py </path/to/mapfile>")

fullmap = sys.argv[1]  # full mapfile path
proj = "CMIP6"  # needed for mapfile.py
basename = str(os.path.basename(fullmap))  # base dir of full map directory

scan_file = tempfile.NamedTemporaryFile()  # create a temporary file which is deleted afterward for autocurator
scanfn = scan_file.name  # name to refer to tmp file

cmor_tables = input("Path to cmor tables: ")  # interactive script, should require no internal editing
autocurator = input("Path to autocurator: ")  # so we just get variable paths from user

autoc_command = autocurator + "/bin/autocurator --out_pretty --out_json " + scanfn  # concatenate autocurator command

os.system("cert_path=./cert.pem")  # TODO: fix this

os.system("export LD_LIBRARY_PATH=$CONDA_PREFIX/lib")  # this isn't working for some reason ...

fullmap_file = open(fullmap, 'r')  # open file object for PrePARE
path = ""
save = True
for line in fullmap_file:  # iterate through mapfile files for PrePARE
    split_line = line.split(" | ")
    filename = split_line[2]
    if save:
        path = filename
        save = False
    command = "PrePARE --table-path " + cmor_tables + " " + filename
    os.system(command)
fullmap_file.close()

datasetdir = os.path.dirname(path) + "/*.nc"  # TODO: fix -- autocurator having issues with *
# temporary fix:
dataset_test = "/p/css03/esgf_publish/CMIP6/CMIP/NCAR/CESM2/historical/r2i1p1f1/Emon/cTotFireLut/gn/v20190308/cTotFireLut_Emon_CESM2_historical_r2i1p1f1_gn_185001-201412.nc"

# Run autocurator and all python scripts
print("Running autocurator...")
autoc_command += " --files " + dataset_test
os.system(autoc_command)

print("Done.\nConverting mapfile...")
map_json_data = mp.main([fullmap, proj])

print("Done.\nMaking dataset...")
out_json_data = mkd.main([map_json_data, scanfn])

print("Done.\nUpdating...")
up.main(out_json_data)

print("Done.\nRunning pub test...")
pt.main(out_json_data)

print("Done. Cleaning up.")
scan_file.close()
