import sys, json, os
import esgcet.logger as logger

log = logger.Logger()


class FieldCheck(object):

    def __init__(self, cmor_path, silent=False):
        cv_path = "{}/CMIP6_CV.json".format(cmor_path)
        jobj = json.load(open(cv_path))["CV"]
        self.sid_dict = jobj["source_id"]
        self.silent = silent
        self.idx = -1
        self.publog = log.return_logger('Activity Check', silent=silent)

    def check_activity(self, source_id, activity_id):


        if source_id not in self.sid_dict:
            return False
        rec = self.sid_dict[source_id]

        return activity_id in rec["activity_participation"]

    def check_institution(self, source_id, inst_id):

        if source_id not in self.sid_dict:
            return False
        rec = self.sid_dict[source_id]

        return inst_id in rec["institution_id"]

    def run_check(self, input_rec):
        src_id = input_rec[self.idx]['source_id']
        act_id = input_rec[self.idx]['activity_drs']
        inst_id = input_rec[self.idx]['institution_id']
 

        if not self.check_activity(src_id, act_id):
            self.publog.error("Source_id {} is not registered for participation in CMIP6 activity {}. Publication halted".format(src_id, act_id))
            self.publog.info("If you think this message has been received in error, please update your CV source repository")
            raise UserWarning
        if not self.check_institution(src_id, inst_id):
            self.publog.error("Institution_id {} is not registered to contribute to source_id {}. Publication halted".format(inst_id, src_id))
            self.publog.info("If you think this message has been received in error, please update your CV source repository")
            raise UserWarning

        self.publog.info("Passed source_id registration test for {}".format(src_id))
        