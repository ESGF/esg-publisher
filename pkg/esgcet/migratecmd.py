from esgcet.esgmigrate import ESGPubMigrate
import argparse, sys, os
from pathlib import Path


DEFAULT_ESGINI = '/esg/config/esgcet/'
home = str(Path.home())


def get_args():
    parser = argparse.ArgumentParser(description="Migrate old config settings into new format.")

    parser.add_argument("--old-config", dest="cfg", default=DEFAULT_ESGINI, help="Path to directory containing old config file to migrate.")
    parser.add_argument("--silent", dest="silent", action="store_true", help="Enable silent mode.")
    parser.add_argument("--verbose", dest="verbose", action="store_true", help="Enable verbose mode.")
    parser.add_argument("--project", dest="project", default=None, help='Name of a particular legacy project to migrate.')
    parser.add_argument("--destination", dest='dest', default=home+'/.esg/esg.ini', help="Destination for new config file.")

    pub = parser.parse_args()

    return pub


def main():

    a = get_args()
    ini_path = a.cfg
    silent = a.silent
    verbose = a.verbose
    project = a.project
    filepath = a.dest

    em = ESGPubMigrate(ini_path, filepath, silent=silent, verbose=verbose)

    em.migrate(project)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
