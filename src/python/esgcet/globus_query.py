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
        print(f"DEBUG {subj}")
        proc = Popen(["globus", "search", "subject", "show", self._UUID, subj[0].rstrip()], stdout=PIPE)
#        cmdstr = f"globus search subject show {self._UUID} '{subj.strip()}'"
#        proc = Popen(cmdstr            , shell=True, stdout=PIPE)
 #       print(f"DEBUG {cmdstr}")

 #       os.system(cmdstr)
        proc.wait()
#        res = proc.stdout.read().decode()
#        print(f"DEBUG {res}")
        return json.load(proc.stdout)

    def query_file_records(self, dataset_id, post_proc=True, latest=True):
        q = copy.deepcopy(SEARCH_TEMPLATE)
        q["filters"].append(self._add_filter("type", "File"))
        q["filters"].append(self._add_filter("dataset_id", dataset_id))

        if latest:
            q["filters"].append(self._add_filter("latest", "true"))
        res = self._run_query(q, False)
        print(f"DEBUG {res}")
        if post_proc:
            y = []
            for x in res:
                y.append(self._post_proc_query([x]))
            return y
        else:
            return res

    def dataset_query_master(self, master_id):
        self._dataset_query(master_id, "master_id")
    
    def _dataset_query(self, _id, field, latest=True):

        q = copy.deepcopy(SEARCH_TEMPLATE)
        q["filters"].append(self._data_node_filter)
        q["filters"].append(self._add_filter("type", "Dataset"))
        q["filters"].append(self._add_filter(field, _id))
        if latest:
            q["filters"].append(self._add_filter("latest", "true"))

        res = self._run_query(q)
        print (f"DEBUG : {res}")
        return self._post_proc_query(res)

    def _run_query(self, q, single=False):
        temp = tempfile.NamedTemporaryFile(mode="w", delete=False)
        json.dump(q, temp, indent=1)
        print(f"DEBUG: to {temp.name}")
        temp.close()

        subproc = Popen(["globus", "search", "query", self._UUID, "--query-document",temp.name], stdout=PIPE)

        subproc.wait()
        
        if single:
            subj = ""
            for x in subproc.stdout:
                if not subj:
                    raise RuntimeError(f"non empty {subj}")
                # There should be only one latest, TODO convert to raise an Exception
                subj = x.decode().rstrip()
        else:
            subj = []
            for x in subproc.stdout:
                subj.append(x.decode().rstrip())
  
        return subj

    def _post_proc_query(self, subj): 
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
    

    res2 = x.file_query(res["id"])

    

#test()