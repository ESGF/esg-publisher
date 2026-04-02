from esgcet.mk_dataset_autoc import ESGPubAutocHandler
from esgcet.mk_dataset_xarray import ESGPubXArrayHandler
from esgcet.mk_dataset_nc4 import ESGPubNC4Handler

from esgcet.mk_dataset import ESGPubMakeDataset

from esgcet.settings import *

import json, os, sys
import tempfile
from esgcet.generic_pub import BasePublisher
import traceback
import esgcet.logger as logger

from typing import Any

from compliance_checker.runner import CheckSuite, ComplianceChecker
from pathlib import Path

log = logger.ESGPubLogger()

class GenericPublisher(BasePublisher):

    scan_file = tempfile.NamedTemporaryFile()  # create a temporary file which is deleted afterward for autocurator
    scanfn = scan_file.name

    def __init__(self, argdict: dict[str, Any]) -> None:
        super().__init__(argdict)

        self.MKD_Construct = ESGPubMakeDataset
        if argdict["skipxr"]:
            self.autoc_command = None
            self.format_handler = ESGPubNC4Handler
            self.extract_method = self.nc4_load
        elif argdict["autoc_command"]:
            self.autoc_command = argdict["autoc_command"]
            self.format_handler = ESGPubAutocHandler
            self.extract_method = self.autocurator
        else:
            self.autoc_command = None
            self.extract_method = self.xarray_load
            self.format_handler = ESGPubXArrayHandler

        self.publog = log.return_logger('Generic NetCDF Publisher', self.silent, self.verbose)
        self._disable_further_info = argdict["disable_further_info"]

    def cleanup(self) -> None:
        self.scan_file.close()

    def compliance_check(self, map_json_data:dict[str, Any]) -> list[bool]:
        """ check the metadata using compliance checker."""

        check_suite = CheckSuite()
        check_suite.load_all_available_checkers()
        project_qc_config = QAQC.get(self.project, None)
        if not project_qc_config:
            self.publog.warn(f"QAQC not configured for {self.project}")
            return True

        ccreport_file = Path(self.fullmap).with_suffix(".ccreport").name
        return_value, errors = ComplianceChecker.run_checker(
            {mapfile_record['file'] for mapfile_record in self.mapdict},
            project_qc_config['test'],
            self.verbose,
            project_qc_config['criteria'],
            None, # skip_checks
            None, # include
            ccreport_file,  # outputfilename
            ["text"]
        )

        return_values = return_value
        if errors:
            self.publog.info(f"Checker Errors {errors}")
            raise RuntimeError(f"Errors from compliance checker {errors}")

        return return_values, ccreport_file
        
    
    ## TODO: refactor these down to a single scan command
    def nc4_load(self, map_json_data):
        """
        netCDF4 LOAD
        """
        self.nc4_set = self.format_handler.nc4_load(map_json_data)

    def xarray_load(self, map_json_data):
        """
        Xarray Load
        """
        self.xarray_set = self.format_handler.xarray_load(map_json_data)


    def autocurator(self, map_json_data):
        """
        Autocurator
        """
        datafile = map_json_data[0][1]

        destpath = os.path.dirname(datafile)
        outname = os.path.basename(datafile)
        idx = outname.rfind('.')

        autstr = self.autoc_command + ' --out_pretty --out_json {} --files "{}/*.nc"'
        self.publog.debug(f"RUNNING {autstr}")
        stat = os.system(autstr.format(self.scanfn, destpath))
        if os.WEXITSTATUS(stat) != 0:
            self.publog.error("Autocurator exited with exit code: " + str(os.WEXITSTATUS(stat)))
            self.cleanup()
            exit(os.WEXITSTATUS(stat))

    def mk_dataset(self, map_json_data):
        
        https_url = self.argdict.get("https_url",None)    
        mkd = self.MKD_Construct(self.data_node, self.index_node, self.replica, self.globus, self.data_roots, 
                                 https_url, self.format_handler, self.silent, self.verbose, skip_opendap=self.argdict.get("skip_opendap",False))
        mkd.set_project(self.project)

        if self.argdict["skipxr"]:
            scan_arg = self.nc4_set
        elif self.autoc_command:
            scan_arg = json.load(open(self.scanfn))
        else:
            scan_arg = self.xarray_set

        try:
            out_json_data = mkd.get_records(map_json_data, scan_arg, self.json_file, user_project=self.proj_config)
        except Exception as ex:
            self.publog.exception("Failed to make dataset")
            self.cleanup()
            exit(1)
        return out_json_data

    def workflow(self):

        # step one: convert mapfile
        self.publog.info("Converting mapfile...")
        map_json_data = self.mapfile()

        if self.project in QAQC:

            checker_name = QAQC[self.project]['test']
            try:
                ret, ccreport_file = self.compliance_check(map_json_data)
                checker_passed = ret        

                if not checker_passed:
                    # dump to a json file, maybe link the checker results
                    failed_qc = {self.fullmap: ccreport_file}

                    record["timestamp"] = datetime.utcnow().isoformat()
                    record["failed"] = failed_qc

                    with open('failed.json', "a", encoding="utf-8") as f:
                        f.write(json.dumps(record) + "\n")

                    # stop the publication
                    return None
            except RuntimeError as e:
                self.publog.info(f"Checker Errors {e}")       

        else:
            raise ValueError(f"{self.project} is not in QAQC settings")
        
        # step two: autocurator
        self.publog.info(f"Running Extraction... {str(self.extract_method)}")
        self.extract_method(map_json_data)

            
        # step three: make dataset
        self.publog.info("Making dataset...")
        out_json_data = self.mk_dataset(map_json_data)

        # step four: update record if exists
        self.publog.info("Updating...")
        self.update(out_json_data)

        # step five: publish to database
        self.publog.info("Running index pub...")
        rc = self.index_pub(out_json_data)

        self.publog.info("Done. Cleaning up.")
        self.cleanup()
        return rc
