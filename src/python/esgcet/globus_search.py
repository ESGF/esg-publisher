#!/usr/bin/env python

import os
import json
from datetime import datetime

from esgcet.settings import *

#  migrate to settings.py
NON_LIST = [
    "creation_date",
    "title",
    "data_node",
    "index_node",
    "master_id",
    "instance_id",
    "id",
    "replica",
    "latest",
    "type",
    "version",
    "north_degrees",
    "south_degrees",
    "east_degrees",
    "west_degrees",
    "datetime_start",
    "datetime_end",
    "number_of_files",
    "size",
    "timestamp",
]

class GlobusSearch:

    def __init__(self, doc_arr, cachedir=None) -> None:
        self._doc_arr = doc_arr
        self._cache_dir = cachedir

    def _get_gmeta_entry(self, doc, now):
        for key, value in doc.items():
            if isinstance(value, list):
                continue
            if key in NON_LIST:
                continue
            doc[key] = [value]

        doc["retracted"] = False
        doc["_timestamp"] = now

        gmeta_entry = {
            "id": "dataset" if doc.get("type") == "Dataset" else "file",
            "subject": doc.get("id"),
            "visible_to": ["public"],
            "content": doc
        }

        return gmeta_entry


    def convert2esgf2(self):
        pid_esgf1 = self._doc_arr
        gmeta = []
        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        # Transform an ESGF1 dataset entries to an ESGF2 Globus index entry
        for doc in pid_esgf1:
            gmeta_entry = self._get_gmeta_entry(doc, now)
            gmeta.append(gmeta_entry)

        # Create a GMetaList with a GMetaEntry for the dataset and GMetaEntries for files
        gingest = {
            "ingest_type": "GMetaList",
            "ingest_data": {
                "gmeta": gmeta
            }
        }

        return gingest

    def extern_globus_publish(self, filename, indexid, update=False):
        os.system(f"globus search ingest {indexid} {filename}")

    def load_and_update_record(self, fn):
        res = json.load(open(fn))

        for rec in res["ingest_data"]["gmeta"]:
            rec["latest"] = False
            rec["mod_timestamp"] = datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        return res

    def check_cache(self):

        tmp_filename, _ = self._get_cache_filename()
        if os.path.exists(tmp_filename):
            return json.load(open(tmp_filename))


    def _get_cache_filename(self):

        d2 = self._doc_arr 
        mid = d2[-1]['master_id']
        version= d2[-1]['version']
        parts = mid.split('.')    
        tmp_subpath =  '/'.join(parts[0:CACHE_DIR_DEPTH])

        if self._cache_dir:
            tmp_abspath = f'{self.cache_dir}/{tmp_subpath}'
        else:
            tmp_abspath = f'/tmp/.esg-publisher/{tmp_subpath}'
        tmp_filename = f'{tmp_abspath}/{mid}.v{version}.json'
        return tmp_filename, tmp_abspath
    
    def run(self):
        
        doc_res = self.convert2esgf2()
        tmp_filename, tmp_abspath = self._get_cache_filename()
        os.mkdirs(tmp_abspath)
        with open(tmp_filename, "w") as f2:
            print(json.dumps(doc_res), file=f2)
        return tmp_filename