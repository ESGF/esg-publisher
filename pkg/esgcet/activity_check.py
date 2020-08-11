import sys, json


CMIPCV="/export/ames4/git/CMIP6_CVs"
SRC_ID_JSON="CMIP6_source_id.json"

IDX = -1  # index for the dataset record
ARGS = 1
class FieldCheck(object):

    def __init__(self, cv_path):

        jobj = json.load(open(cv_path))
        self.sid_dict = jobj["source_id"]


    def check_fields(self, source_id, activity_id):


        if source_id not in self.sid_dict:
            return False
        rec = self.sid_dict[source_id]

        return activity_id in rec["activity_participation"]


def main(args):

    cv_path = "{}/{}".format(CMIPCV, SRC_ID_JSON)
    fc = FieldCheck(cv_path)

    if len(args) < (ARGS):
        print("Missing required arguments")
        exit(0)

    try:
        input_rec = json.load(open(args[0]))
    except Exception as e:
        print("Error opening input json format for {}: ".format(args[0],e))
        exit(1)

    # Refactor for several cases: (1) standalone with main() (2) called by larger publisher module (3) query results from search

    src_id = input_rec[IDX]['source_id']
    act_id = input_rec[IDX]['activity_drs']
 
    if fc.check_fields(src_id, act_id):
        print("INFO: passed source_id registration test for {}".format(src_id))
    else:
        print("ERROR: source_id {} is not registered for participation in CMIP6 activity {}. Publication halted".format(src_id, act_id))
        print("If you think this message has been received in error, please update your CV source repository")



if __name__ == '__main__':
    main(sys.argv[1:])
