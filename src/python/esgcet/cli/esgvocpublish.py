from esgcet.util.args import PublisherArgs
import os
import sys
import esgcet.util.logger as logger
from esgcet.vocab import ESGNetcdfAssembler

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

    for mf in pub.map:
        ea = ESGNetcdfAssembler(
            mf,
            pub.cfg,
            save_stac=pub.save_stac,
            dry_run=pub.dry_run,
            verbose=pub.verbose,
            silent=pub.silent)
            
        #     {
        #         'license':'Creative Commons Attribution 4.0 International License',
        #         'nominal_resolution':'site-collection',
        #         'processing_code_location':'undefined'
        #     },
        #     exclusions = [
        #         'variant_info'
        #     ]
        # )

        ea.publish_stac_record()


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
