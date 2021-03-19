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


import traceback

DEFAULT_ESGINI = '/esg/config/esgcet'


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
            migrate.run(DEFAULT_ESGINI, False, False)
        else:
            print("Error opening config file: " + str(ex))
            exit(1)

    if pub.proj != "":
        proj = pub.proj
    else:
        try:
            tmp = config['user']['project']
            if tmp != "none":
                proj = tmp
        except:
            pass
    if proj == "CMIP6":
        cmip6 = True

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
        globus = config['user']['globus_uuid']
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

    scan_file = tempfile.NamedTemporaryFile()  # create a temporary file which is deleted afterward for autocurator
    scanfn = scan_file.name  # name to refer to tmp file

    if not conda_auto:
        autoc_command = autocurator + "/bin/autocurator"  # concatenate autocurator command
    else:
        autoc_command = autocurator

    os.system("cert_path=" + cert)

    if not silent:
        print("Converting mapfile...")
    try:
        map_json_data = mp.run([fullmap, proj])
    except Exception as ex:
        if verbose:
            traceback.print_exc()

        print("Error with converting mapfile: " + str(ex), file=sys.stderr)
        exit_cleanup(scan_file)
        exit(1)
    if not silent:
        print("Done.")

    if cmip6:
        if pub.cmor_path is None:
            try:
                cmor_tables = config['user']['cmor_path']
            except:
                print("No path for CMOR tables defined. Use --cmor-tables option or define in config file.", file=sys.stderr)
                exit(1)
        else:
            cmor_tables = pub.cmor_path
        try:
            prepare_internal(map_json_data, cmor_tables)
        except Exception as ex:
            if verbose:
                traceback.print_exc()
            print("Error with PrePARE: " + str(ex), file=sys.stderr)
            exit_cleanup(scan_file)
            exit(1)

    # Run autocurator and all python scripts
    if not silent:
        print("Running autocurator...")
    datafile = map_json_data[0][1]

    destpath = os.path.dirname(datafile)
    outname = os.path.basename(datafile)
    idx = outname.rfind('.')

    out_json_data = None
    new_json_data = None

    autstr = autoc_command + ' --out_pretty --out_json {} --files "{}/*.nc"'
    stat = os.system(autstr.format(scanfn, destpath))
    if os.WEXITSTATUS(stat) != 0:
        print("Error running autocurator, exited with exit code: " + str(os.WEXITSTATUS(stat)), file=sys.stderr)
        exit(os.WEXITSTATUS(stat))

    if not silent:
        print("Done.\nMaking dataset...")
    try:
        if third_arg_mkd:
            out_json_data = mkd.run([map_json_data, scanfn, data_node, index_node, replica, data_roots, globus, dtn, silent, verbose, json_file])
        else:
            out_json_data = mkd.run([map_json_data, scanfn, data_node, index_node, replica, data_roots, globus, dtn, silent, verbose])
    except Exception as ex:
        if verbose:
            traceback.print_exc()
        print("Error making dataset: " + str(ex), file=sys.stderr)
        exit_cleanup(scan_file)
        exit(1)

    if cmip6:
        if not silent:
            print("Done.\nRunning activity check...")
        try:
            act.run(out_json_data)
        except Exception as ex:
            print("Error running activity check: " + str(ex), file=sys.stderr)
            exit_cleanup(scan_file)
            exit(1)

        if not silent:
            print("Done.\nRunning pid cite...")
        try:
            pid_creds = json.loads(config['user']['pid_creds'])
        except:
            print("PID credentials not defined. Define in config file esg.ini.", file=sys.stderr)
            exit(1)
        try:
            new_json_data = pid.run([out_json_data, data_node, pid_creds, silent, verbose])
        except Exception as ex:
            if verbose:
                traceback.print_exc()
            print("Error running pid cite: " + str(ex), file=sys.stderr)
            exit_cleanup(scan_file)
            exit(1)

    else:
        new_json_data = out_json_data

    if not silent:
        print("Done.\nUpdating...")
    try:
        up.run([new_json_data, index_node, cert, silent, verbose])
    except Exception as ex:
        if verbose:
            traceback.print_exc()
        print("Error updating: " + str(ex), file=sys.stderr)
        exit_cleanup(scan_file)
        exit(1)

    if not silent:
        print("Done.\nRunning index pub...")
    try:
        ip.run([new_json_data, index_node, cert, silent, verbose])
    except Exception as ex:
        if verbose:
            traceback.print_exc()
        print("Error running index pub: " + str(ex), file=sys.stderr)
        exit_cleanup(scan_file)
        exit(1)

    if not silent:
        print("Done. Cleaning up.")
    exit_cleanup(scan_file)


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
