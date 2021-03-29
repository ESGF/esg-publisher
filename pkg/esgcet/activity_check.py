import sys, json, os


class FieldCheck(object):

    def __init__(self, cmor_path, silent=False):
        cv_path = "{}/CMIP6_CV.json".format(cmor_path)
        jobj = json.load(open(cv_path))["CV"]
        self.sid_dict = jobj["source_id"]
        self.silent = silent

    def check_fields(self, source_id, activity_id):


        if source_id not in self.sid_dict:
            return False
        rec = self.sid_dict[source_id]

        return activity_id in rec["activity_participation"]


    def run_check(self, input_rec):
        src_id = input_rec[IDX]['source_id']
        act_id = input_rec[IDX]['activity_drs']
 
        if self.check_fields(src_id, act_id):
            if not self.silent:
                print("INFO: passed source_id registration test for {}".format(src_id))
        else:
            print("ERROR: source_id {} is not registered for participation in CMIP6 activity {}. Publication halted".format(src_id, act_id), file=sys.stderr)
            print("If you think this message has been received in error, please update your CV source repository", file=sys.stderr)
