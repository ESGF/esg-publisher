import argparse

def get_args():
    parser = argparse.ArgumentParser(description="Publish data sets to ESGF databases.")

    # ANY FILE NAME INPUT: check first to make sure it exists
    # add project flag: cmip6 or CMIP6 is fine, case insensitive
    # for test see settings
    parser.add_argument("--test", dest="test", action="store_true", help="PID registration will run in 'test' mode. Use this mode unless you are performing 'production' publications.")
    # replica stuff new... hard-coded, modify mk dataset so that it imports it instead
    parser.add_argument("--set-replica", dest="set_replica", action="store_true", help="Enable replica publication.")
    parser.add_argument("--no-replica", dest="no_replica", action="store_true", help="Disable replica publication.")
    parser.add_argument("--json", dest="json", default=None, help="Load attributes from a JSON file in .json form. The attributes will override any found in the DRS structure or global attributes.")
    parser.add_argument("--data-node", dest="data_node", default=None, help="Specify data node.")
    parser.add_argument("--index-node", dest="index_node", default=None, help="Specify index node.")
    parser.add_argument("--certificate", "-c", dest="cert", default="./cert.pem", help="Use the following certificate file in .pem form for publishing (use a myproxy login to generate).")
    parser.add_argument("--project", dest="proj", default="", help="Set/overide the project for the given mapfile, for use with selecting the DRS or specific features, e.g. PrePARE, PID.")
    parser.add_argument("--cmor-tables", dest="cmor_path", default=None, help="Path to CMIP6 CMOR tables for PrePARE. Required for CMIP6 only.")
    parser.add_argument("--autocurator", dest="autocurator_path", default=None, help="Path to autocurator repository folder.")
    parser.add_argument("--map", dest="map", required=True, nargs="+", help="mapfile or file containing a list of mapfiles.")

    pub = parser.parse_args()

    return pub
