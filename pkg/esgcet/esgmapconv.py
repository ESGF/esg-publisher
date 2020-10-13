import esgcet.mapfile as mp
import sys
import json
import os
import configparser as cfg
import argparse
from pathlib import Path


def get_args():
    parser = argparse.ArgumentParser(description="Publish data sets to ESGF databases.")

    home = str(Path.home())
    def_config = home + "/.esg/esg.ini"
    parser.add_argument("--project", dest="proj", default="", help="Set/overide the project for the given mapfile, for use with selecting the DRS or specific features, e.g. PrePARE, PID.")
    parser.add_argument("--map", dest="map", required=True, help="Mapfile ending in .map extension, contains metadata about the record.")
    parser.add_argument("--out-file", dest="out_file", help="Output file for map data in JSON format. Default is printed to standard out.")

    pub = parser.parse_args()

    return pub


def run():
    a = get_args()

    p = True
    if a.out_file is not None:
        p = False
        outfile = a.out_file

    proj = None
    if a.proj != "":
        proj = a.proj

    try:
        fullmap = a.map
    except:
        print("Error with argparse. Exiting.", file=sys.stderr)
        exit(1)
    try:
        if proj:
            map_json_data = mp.run([fullmap, proj])
        else:
            map_json_data = mp.run([fullmap])
    except Exception as ex:
        print("Error with converting mapfile: " + str(ex), file=sys.stderr)
        exit(1)

    if p:
        print(json.dumps(map_json_data))
    else:
        with open(outfile, 'w') as of:
            json.dump(map_json_data, of)


def main():
    run()


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
