import argparse
import os
from pathlib import Path
import esgcet.util.logger as logger

import esgcet.util.args as pub_args
import esgcet.util.logger as logger
from esgcet.stac.stac_client import getTransactionClient

log = logger.ESGPubLogger()
publog = log.return_logger("esglogin")


def get_config():
    parser = argparse.ArgumentParser(
        description="One-time login to fetch necessary OAuth2 token, required to publish ESGF STAC Transaction API. Ensure that you have configured your .yaml file with the correct API settings prior to use."
    )

    home = str(Path.home())
    def_config = home + "/.esg/esg.yaml"
    parser.add_argument(
        "--config",
        "-cfg",
        dest="cfg",
        default=def_config,
        help="Path to .yaml config file.",
    )

    pub = parser.parse_args()

    ini_file = pub.cfg
    if not os.path.exists(ini_file):
        publog.error("Config file not found. " + ini_file + " does not exist.")
        exit(1)
    if os.path.isdir(ini_file):
        publog.error(
            "Config file path is a directory. Please use a complete file path."
        )
        exit(1)
    args = pub_args.PublisherArgs()
    config = args.load_config(ini_file)
    return config


def main():

    args = get_config()

    TransCli = getTransactionClient(args.get("stac_config", {}))

    tc = TransCli(args)
