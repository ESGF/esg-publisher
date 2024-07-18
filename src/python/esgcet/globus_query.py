import json, copy
import tempfile
import sys, os

from subprocess import Popen, PIPE

FILTER_TEMPLATE = {
    "type" : "match_all",
    "field_name" : "data_node",
    "values" : []
    }

SEARCH_TEMPLATE = {
    "q" : "",
    "filters" : [
        {
        "type" : "match_all",
        "field_name" : "latest",
        "values" : ["true"]
        }
        ],
    }

class ESGGlobusQuery():

    def __init__(self, UUID_in, data_node_in):
        self._UUID = UUID_in
        self._data_node_filter = self._add_filter("data_node", data_node_in)

    def _add_filter(self, name, value):
        tmpfilter = copy.deepcopy(FILTER_TEMPLATE)
        tmpfilter["field_name"] = name
        tmpfilter["values"].append(value)
        return tmpfilter
    
    def globus_get_record(self, subj):
        proc = Popen(["globus", "search", "subject", "show", self._UUID, subj.rstrip()], stdout=PIPE)
#        cmdstr = f"globus search subject show {self._UUID} '{subj.strip()}'"
#        proc = Popen(cmdstr            , shell=True, stdout=PIPE)
 #       print(f"DEBUG {cmdstr}")

 #       os.system(cmdstr)
        proc.wait()
#        res = proc.stdout.read().decode()
#        print(f"DEBUG {res}")
        return json.load(proc.stdout)

    

    def dataset_query(self, master_id):

        q = copy.deepcopy(SEARCH_TEMPLATE)
        q["filters"].append(self._data_node_filter)
        q["filters"].append(self._add_filter("type", "Dataset"))
        q["filters"].append(self._add_filter("master_id", master_id))


        temp = tempfile.NamedTemporaryFile(mode="w", delete=False)
        json.dump(q, temp, indent=1)
        print(f"DEBUG: to {temp.name}")
        temp.close()

        subproc = Popen(["globus", "search", "query", self._UUID, "--query-document",temp.name], stdout=PIPE)

        subproc.wait()
        subj = ""
        record = None
        for x in subproc.stdout:
            assert not subj  # There should be only one latest, TODO convert to raise an Exception
            subj = x.decode()
        
        if subj:
            res = self.globus_get_record(subj)
            if res and "content" in res:
                return res["content"]
            else:
                raise RuntimeError(f"Unexpected error {res}")
        else:
            print("No record found")
            return {}

def test():        
    UUID = "5cc79324-1b74-4a77-abc3-838aba2fc734"
    DATA_NODE = "esgf-fake-test.llnl.gov"

    x = ESGGlobusQuery(UUID, DATA_NODE)

    res = x.dataset_query(sys.argv[1])
    with open("test.json", "w") as outf:
        json.dump(res, outf)

test()