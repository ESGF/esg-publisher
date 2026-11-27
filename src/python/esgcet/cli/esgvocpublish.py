from esgcet.util.args import PublisherArgs
import os
import sys
import esgcet.util.logger as logger
from esgcet.vocab import ESGNetcdfAssembler
import glob

log = logger.ESGPubLogger()
publog = log.return_logger("Esgvoc-Publisher")

from pathlib import Path

def check_files(files):
    for file in files:
        try:
            myfile = open(file, "r")
            myfile.close()
        except Exception as ex:
            publog.exception("Error opening file " + file + ". Exiting.")
            exit(1)

def main():
    pub_args = PublisherArgs()
    pub = pub_args.get_args()

    map = pub.map

    if isinstance(map, list) and len(map) > 1:
        maps = map
    elif os.path.isfile(map[0]):
        if '.txt' in map[0]:
            with open(map[0]) as f:
                maps = [r.strip() for r in f]
        else:
            maps = [map[0]]
    elif os.path.isdir(map[0]):
        maps = glob.glob(f'{map[0]}/*.map')
    else:
        raise ValueError(
            f'{map[0]} not a valid map input - '
            'acceptable values are mapfile, text file, directory')

    for mf in maps:
        print(f'Using map file: {map}')
        ea = ESGNetcdfAssembler(
            mf,
            pub.cfg,
            save_stac=pub.save_stac,
            dry_run=pub.dry_run,
            verbose=pub.verbose,
            silent=pub.silent,
            jsonfile=pub.json)

        ea.publish_stac_record()


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
