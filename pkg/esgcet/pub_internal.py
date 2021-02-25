import esgcet.mapfile as mp
import esgcet.mk_dataset as mkd
import esgcet.update as up
import esgcet.index_pub as ip
import esgcet.pid_cite_pub as pid
import esgcet.activity_check as act
import esgcet.args as args
import esgcet.esgmigrate as migrate
import os
import json
import sys
import tempfile
from cmip6_cv import PrePARE
from esgcet.settings import *
import configparser as cfg
from pathlib import Path
import esgcet.esgmigrate as em

DEFAULT_ESGINI = '/esg/config/esgcet'


def check_files(files):
    for file in files:
        try:
            myfile = open(file, 'r')
            myfile.close()
        except Exception as ex:
            print("Error opening file " + file + ": " + str(ex))
            exit(1)


def exit_cleanup(files):
    for f in files:
        f.close()


def check_data(data, proj):
    if data is None:
        exit_cleanup(proj.files)
        exit(1)


def run(fullmap):

    # SETUP
    split_map = fullmap.split("/")
    fname = split_map[-1]
    fname_split = fname.split(".")
    project = fname_split[0]

    files = []
    files.append(fullmap)

    check_files(files)

    pub = args.get_args()
    third_arg_mkd = False
    if pub.json is not None:
        json_file = pub.json
        third_arg_mkd = True


    if pub.migrate:
        migrate.run({})

    ini_file = pub.cfg
    config = cfg.ConfigParser()
    config_file = ini_file
    try:
        config.read(config_file)
    except Exception as ex:
        if not os.path.exists(ini_file):
            print("No config file found. Attempting to migrate old settings.")
            em.run(DEFAULT_ESGINI, False, False)
        else:
            print("Error opening config file: " + str(ex))
            exit(1)

    if pub.proj != "":
        project = pub.proj
    else:
        try:
            project = config['user']['project']
        except:
            pass

    if not pub.silent:
        try:
            s = config['user']['silent']
            if 'true' in s or 'yes' in s:
                silent = True
            else:
                silent = False
        except:
            silent = False
    else:
        silent = True

    if not pub.verbose:
        try:
            v = config['user']['verbose']
            if 'true' in v or 'yes' in v:
                verbose = True
            else:
                verbose = False
        except:
            verbose = False
    else:
        verbose = True
    
    if pub.cert == "./cert.pem":
        try:
            cert = config['user']['cert']
        except:
            cert = pub.cert
    else:
        cert = pub.cert

    conda_auto = False
    if pub.autocurator_path is None:
        try:
            autocurator = config['user']['autoc_path']
            if autocurator == "autocurator":
                conda_auto = True
        except:
            autocurator = "autocurator"
            conda_auto = True
    else:
        autocurator = pub.autocurator_path

    if pub.index_node is None:
        try:
            index_node = config['user']['index_node']
        except:
            print("Index node not defined. Use the --index-node option or define in esg.ini.", file=sys.stderr)
            exit(1)
    else:
        index_node = pub.index_node

    if pub.data_node is None:
        try:
            data_node = config['user']['data_node']
        except:
            print("Data node not defined. Use --data-node option or define in esg.ini.", file=sys.stderr)
            exit(1)
    else:
        data_node = pub.data_node
    try:
        data_roots = json.loads(config['user']['data_roots'])
        if data_roots == 'none':
            print("Data roots undefined. Define in esg.ini to create file metadata.", file=sys.stderr)
            exit(1)
    except:
        print("Data roots undefined. Define in esg.ini to create file metadata.", file=sys.stderr)
        exit(1)

    try:
        globus = json.loads(config['user']['globus_uuid'])
    except:
        # globus undefined
        globus = "none"

    try:
        dtn = config['user']['data_transfer_node']
    except:
        # dtn undefined
        dtn = "none"
    
    if pub.set_replica and pub.no_replica:
        print("Error: replica publication simultaneously set and disabled.", file=sys.stderr)
        exit(1)
    elif pub.set_replica:
        replica = True
    elif pub.no_replica:
        replica = False
    else:
        try:
            r = config['user']['set_replica']
            if 'yes' in r or 'true' in r:
                replica = True
            elif 'no' in r  or 'false' in r:
                replica = False
            else:
                print("Config file error: set_replica must be true, false, yes, or no.", file=sys.stderr)
                exit(1)
        except:
            print("Set_replica not defined. Use --set-replica or --no-replica or define in esg.ini.", file=sys.stderr)
            exit(1)


    if not conda_auto:
        autoc_command = autocurator + "/bin/autocurator"  # concatenate autocurator command
    else:
        autoc_command = autocurator

    os.system("cert_path=" + cert)

    argdict = {"fullmap": fullmap, "third_arg_mkd": third_arg_mkd, "silent": silent, "verbose": verbose, "cert": cert,
               "autoc_command": autoc_command, "index_node": index_node, "data_node": data_node, "data_roots": data_roots,
               "globus": globus, "dtn": dtn, "replica": replica}

    if third_arg_mkd:
        argdict["json_file"] = json_file

    if project == "CMIP6":
        from esgcet.cmip6 import cmip6
        proj = cmip6()
    elif project == "non-nc":
        from esgcet.generic_pub import GenericPublisher
        proj = GenericPublisher()

    # ___________________________________________
    # WORKFLOW - one line call

    proj.workflow(argdict)


def main():
    pub = args.get_args()
    maps = pub.map  # full mapfile path
    if maps is None:
        print("Missing argument --map, use " + sys.argv[0] + " --help for usage.", file=sys.stderr)
        exit(1)
    if maps[0][-4:] != ".map":
        myfile = open(maps[0])
        for line in myfile:
            length = len(line)
            run(line[0:length - 2])
        myfile.close()
        # iterate through file in directory calling main func
    else:
        for m in maps:
            run(m)


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
