import mapfile as mp
import mk_dataset as mkd
import update as up
import pub_test as pt
import os
import json
import sys


if len(sys.argv) < 1:
    print("Usage: python3 publish_script.py </path/to/mapfile>")

fullmap = sys.argv[1]
proj = "CMIP6"
basename = str(os.path.basename(fullmap))
scanfn = basename + ".scan.json"
convmapfn = basename + ".map.json"
outfn = basename + ".out.json"

cmor_tables = input("Path to cmor tables: ")
autocurator = input("Path to autocurator: ")
autoc_command = autocurator + "/bin/autocurator --out_pretty --out_json " + scanfn

fullmap_file = open(fullmap, 'r')
os.system("export LD_LIBRARY_PATH=$CONDA_PREFIX/lib")
path = ""
save = True
for line in fullmap_file:
    split_line = line.split(" | ")
    filename = split_line[2]
    if save:
        path = filename
        save = False
    command = "PrePARE --table-path " + cmor_tables + " " + filename
    os.system(command)
fullmap_file.close()

datasetdir = os.path.dirname(path) + "/*.nc"
dataset_test = os.path.dirname(path) + "/CMIP6.CMIP.E3SM-Project.E3SM-1-0.historical.r2i1p1f1.Amon.ps.gr.v20190729.ps_Amon_E3SM-1-0_historical_r2i1p1f1_gr_200001-201412.nc"

print("Running autocurator...")
autoc_command += " --files " + datasetdir
os.system(autoc_command)

print("Done.\nConverting mapfile...")
map_file = open(convmapfn, 'w+')
json.dump(mp.main([fullmap, proj]), map_file, indent=1)

print("Done.\nMaking dataset...")
out_file = open(outfn, 'w+')
# PROBLEM: mk_dataset is seemingly reading nothing from scanfn--
# cont: AUTOCURATOR not working... not putting anything in scanfn, but not producing any errors
json.dump(mkd.main([convmapfn, scanfn]), out_file, indent=1)

print("Done.\nUpdating...")
up.main(outfn)

print("Done.\nRunning pub test...")
pt.main(outfn)

print("Done. Cleaning up.")
out_file.close()
map_file.close()
scan_file.close()

