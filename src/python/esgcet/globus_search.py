#!/usr/bin/env python

import os
import json
from datetime import datetime

from settings import *

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
            gmeta_entry = self.get_gmeta_entry(doc, now)
            gmeta.append(gmeta_entry)

        # Create a GMetaList with a GMetaEntry for the dataset and GMetaEntries for files
        gingest = {
            "ingest_type": "GMetaList",
            "ingest_data": {
                "gmeta": gmeta
            }
        }

        return gingest

    def run(self):
        
        mid = d2[-1]['master_id']
        version= d2[-1]['version']
        d2 = self.convert2esgf2()
        tmp_subpath =  '/'.join(parts[0:CACHE_DIR_DEPTH])

        if self._cache_dir:
            parts = mid.split('.')
            tmp_abspath = f'{self.cache_dir}/{tmp_subpath}'
        else:
            tmp_abspath = f'/tmp/.esg-publisher/{tmp_subpath}'
        tmp_filename = f'{tmp_abspath}/{mid}.v{version}.json'
        os.mkdirs(tmp_abspath)
        with open(tmp_filename, "w") as f2:
            print(json.dumps(d2), file=f2)
        return tmp_filename