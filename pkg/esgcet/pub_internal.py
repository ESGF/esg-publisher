import esgcet.mapfile as mp
import esgcet.mk_dataset as mkd
import esgcet.update as up
import esgcet.index_pub as ip
import esgcet.pid_cite_pub as pid
import esgcet.activity_check as act
import esgcet.args as args
import os
import json
import sys
import tempfile
from cmip6_cv import PrePARE
from esgcet.settings import *
import configparser as cfg

def prepare_internal(json_map, cmor_tables):
    print("iterating through filenames for PrePARE (internal version)...")
    validator = PrePARE.PrePARE
    for info in json_map:
        filename = info[1]
        process = validator.checkCMIP6(cmor_tables)
        process.ControlVocab(filename)


def check_files(files):
    for file in files:
        try:
            myfile = open(file, 'r')
        except Exception as ex:
            print("Error opening file " + file + ": " + str(ex))
            exit(1)
        myfile.close()


def exit_cleanup(scan_file):
    scan_file.close()


def run(fullmap):

    split_map = fullmap.split("/")
    fname = split_map[-1]
    fname_split = fname.split(".")
    proj = fname_split[0]
    cmip6 = False
    if proj == "CMIP6":
        cmip6 = True

    files = []
    files.append(fullmap)

    check_files(files)

    pub = args.get_args()
    third_arg_mkd = False
    if pub.json is not None:
        json_file = pub.json
        third_arg_mkd = True
    config = cfg.ConfigParser()
    config.read('esg.ini')

    if pub.cert == "./cert.pem":
        try:
            cert = config['user']['cert']
        except:
            cert = pub.cert
    else:
        cert = pub.cert

    if pub.autocurator_path is None:
        try:
            autocurator = config['user']['autoc_path']
        except:
            print("No autocurator path defined. Use --autocurator option or define in config file.")
            exit(1)
    else:
        autocurator = pub.autocurator_path

    if pub.index_node is None:
        try:
            index_node = config['user']['index_node']
        except:
            print("Index node not defined. Use the --index-node option or define in esg.ini.")
            exit(1)
    else:
        index_node = pub.index_node

    if pub.data_node is None:
        try:
            data_node = config['user']['data_node']
        except:
            print("Data node not defined. Use --data-node option or define in esg.ini.")
            exit(1)
    else:
        data_node = pub.data_node

    if pub.set_replica and pub.no_replica:
        print("Error: replica publication simultaneously set and disabled.")
        exit(1)
    elif pub.set_replica:
        replica = True
    elif pub.no_replica:
        replica = False
    else:
        try:
            replica = config['user'].getboolean(['set_replica'])
        except:
            print("Set_replica not defined. Use --set-replica or --no-replica or define in esg.ini.")
            exit(1)


    scan_file = tempfile.NamedTemporaryFile()  # create a temporary file which is deleted afterward for autocurator
    scanfn = scan_file.name  # name to refer to tmp file

    autoc_command = autocurator + "/bin/autocurator"  # concatenate autocurator command

    os.system("cert_path=" + cert)

    print("Converting mapfile...")
    try:
        map_json_data = mp.run([fullmap, proj])
    except Exception as ex:
        print("Error with converting mapfile: " + str(ex))
        exit_cleanup(scan_file)
        exit(1)
    print("Done.")

    if cmip6:
        if pub.cmor_path is None:
            try:
                cmor_tables = config['user']['cmor_path']
            except:
                print("No path for CMOR tables defined. Use --cmor-tables option or define in config file.")
                exit(1)
        else:
            cmor_tables = pub.cmor_path
        try:
            prepare_internal(map_json_data, cmor_tables)
        except Exception as ex:
            print("Error with PrePARE: " + str(ex))
            exit_cleanup(scan_file)
            exit(1)

    # Run autocurator and all python scripts
    print("Running autocurator...")
    os.system("bash " + autocurator + "/autocurator.sh " + autoc_command + " " + fullmap + " " + scanfn)

    print("Done.\nMaking dataset...")
    try:
        if third_arg_mkd:
            out_json_data = mkd.run([map_json_data, scanfn, data_node, index_node, replica, json_file])
        else:
            out_json_data = mkd.run([map_json_data, scanfn, data_node, index_node, replica])
    except Exception as ex:
        print("Error making dataset: " + str(ex))
        exit_cleanup(scan_file)
        exit(1)

    if cmip6:
        print("Done.\nRunning pid cite...")
        try:
            new_json_data = pid.run([out_json_data, data_node])
        except Exception as ex:
            print("Error running pid cite: " + str(ex))
            exit_cleanup(scan_file)
            exit(1)

    print("Done.\nRunning activity check...")
    try:
        act.run(new_json_data)
    except Exception as ex:
        print("Error running activity check: " + str(ex))
        exit_cleanup(scan_file)
        exit(1)
    print("Done.\nUpdating...")
    try:
        up.run([new_json_data, index_node, cert])
    except Exception as ex:
        print("Error updating: " + str(ex))
        exit_cleanup(scan_file)
        exit(1)

    print("Done.\nRunning index pub...")
    try:
        ip.run([new_json_data, index_node, cert])
    except Exception as ex:
        print("Error running pub test: " + str(ex))
        exit_cleanup(scan_file)
        exit(1)

    print("Done. Cleaning up.")
    exit_cleanup(scan_file)

def main():
    pub = args.get_args()
    fullmap = pub.map  # full mapfile path
    if fullmap is None:
        print("Missing argument --map, use " + sys.argv[0] + " --help for usage.")
        exit(1)
    if fullmap[-4:] != ".map":
        myfile = open(fullmap)
        for line in myfile:
            length = len(line)
            run(line[0:length - 2])
        myfile.close()
        # iterate through file in directory calling main
    else:
        run(fullmap)

if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
