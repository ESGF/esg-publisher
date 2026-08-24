import json, copy
import tempfile
import sys, os

from subprocess import Popen, PIPE
from time import sleep

FILTER_TEMPLATE = {
    "type" : "match_all",
    "field_name" : "data_node",
    "values" : []
    }

SEARCH_TEMPLATE = {
    "q" : "",
    "filters" : [
        ],
    }



class ESGGlobusQuery():

    def __init__(self, UUID_in, data_node_in):
        self._UUID = UUID_in
        self._data_node_filter = self._add_filter("data_node", data_node_in)

    def _add_filter(self, name, value, any=False):
        tmpfilter = copy.deepcopy(FILTER_TEMPLATE)
        tmpfilter["field_name"] = name
        if isinstance(value, list):
            tmpfilter["values"] += value
        else:
            tmpfilter["values"].append(value)
        if any:
            tmpfilter["type"] = "match_any"
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

    def query_file_records(self, dataset_id, post_proc=True, latest=True, wget=False):
        q = copy.deepcopy(SEARCH_TEMPLATE)
        q["filters"].append(self._add_filter("type", "File"))
        q["filters"].append(self._add_filter("dataset_id", dataset_id, any=wget))
        if wget:
            latest = False

        if latest:
            q["filters"].append(self._add_filter("latest", True))

        print(f"Query in {q}")
        res = self._run_query(q, single=False, isjson=wget)
        
        if wget:
            return [entry["content"] for x in res["gmeta"] for entry in x["entries"]]
        elif post_proc:
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
        q["filters"].append(self._add_filter("type", "Dataset", any=True))
        q["filters"].append(self._add_filter(field, _id))
        if latest:
            q["filters"].append(self._add_filter("latest", True))

        res = self._run_query(q)

        return self._post_proc_query(res)

    def _run_query(self, q, single=False, isjson=False):
        temp = tempfile.NamedTemporaryFile(mode="w", delete=False)
        json.dump(q, temp, indent=1)
        print(f"DEBUG: to {temp.name}")
        temp.close()
    
        cmdarr = ["globus", "search", "query", self._UUID, "--query-document",temp.name, "--limit", "10000"]
        if isjson:
            cmdarr += ["--format", "json"]
        subproc = Popen(cmdarr, stdout=PIPE)

        sleep(5)
        
        #print("Complete")
        
        if isjson:
            res = {}
            try:
                res = json.load(subproc.stdout)
            except Exception as e:
                print(f"Exception encountered")
                with open("log.log", "w") as f:
                    print(f"{e}", file=f)
            print("Loaded")
            return res
        
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
