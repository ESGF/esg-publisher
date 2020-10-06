import sys, json, os
import configparser as cfg
from pathlib import Path

config = cfg.ConfigParser()
home = str(Path.home())
config_file = home + "/.esg/esg.ini"
config.read(config_file)
try:
    s = config['user']['silent']
    if 'true' in s or 'yes' in s:
        SILENT = True
    else:
        SILENT = False
except:
    SILENT = False
try:
    v = config['user']['verbose']
    if 'true' in v or 'yes' in v:
        VERBOSE = True
    else:
        VERBOSE = False
except:
    VERBOSE = False


IDX = -1  # index for the dataset record
ARGS = 1
class FieldCheck(object):

    def __init__(self, cv_path):

        jobj = json.load(open(cv_path))["CV"]
        self.sid_dict = jobj["source_id"]


    def check_fields(self, source_id, activity_id):


        if source_id not in self.sid_dict:
            return False
        rec = self.sid_dict[source_id]

        return activity_id in rec["activity_participation"]


def run(input_rec):

    try:
        cmor_path = config["user"]["cmor_path"]
    except Exception as e:
        print(e)
        print("Error CMOR path not configured. Must do so to enable the Activity check! {}".format(str(e)))
        return -1
    cv_path="{}/CMIP6_CV.json".format(cmor_path)
    fc = FieldCheck(cv_path)

    # try:
    """except Exception as e:
        print("Error opening input json format for {}: ".format(args[0],e), file=sys.stderr)
        exit(1)"""

    # Refactor for several cases: (1) standalone with main() (2) called by larger publisher module (3) query results from search

    src_id = input_rec[IDX]['source_id']
    act_id = input_rec[IDX]['activity_drs']
 
    if fc.check_fields(src_id, act_id):
        if not SILENT:
            print("INFO: passed source_id registration test for {}".format(src_id))
    else:
        print("ERROR: source_id {} is not registered for participation in CMIP6 activity {}. Publication halted".format(src_id, act_id), file=sys.stderr)
        print("If you think this message has been received in error, please update your CV source repository", file=sys.stderr)


def open_run(args):
    if len(args) < (ARGS):
        print("Missing required arguments", file=sys.stderr)
        exit(0)
    jobj = json.load(open(args[0]))
    run(jobj)


def main():
    open_run(sys.argv[1:])


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    main()
