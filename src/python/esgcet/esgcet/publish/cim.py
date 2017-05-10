"""
esgcet wrapper to cdf2cim.

Provides create_cim_from_dmap.

Imports cdf2cim, but only if and when create_cim_from_dmap is actually called, so if import fails,
publisher can still be run without it.
"""

import os
import sys
from utility import tracebackString


class Cdf2cimWrapper:

    cdf2cim = None

    def _do_import(self):
        if self.cdf2cim == None:
            self.cdf2cim = __import__("cdf2cim")    

    def create_cim_from_dmap(self, dmap):
        """
        Call cdf2cim with a starting directory which is the deepest common parent directory 
        for the set of files listed in the map file.
        The map file ought only contain one dataset ID, but if it contains more than one, 
        call cdf2cim for each separately.
        """

        if not dmap:
            print "WARNING: Empty map file.  cdf2cim will not be run."
            return

        self._do_import()

        if len(dmap) > 1:
            print "WARNING: Dataset map contains more than one dataset."
            print "         Will run cdf2cim separately for each."

        failures = ""
        for top_dir in self._yield_starting_directories(dmap):
            try:
                self._call_cdf2cim(top_dir)
            except:
                failures += "While running cdf2cim on 'top_dir':\n%s" % tracebackString(indent=5)

        if failures:
            raise Exception(failures)
    
    def _yield_starting_directories(self, dmap):
        for (dsid, version), values in dmap.items():
            paths = [path for path, size in values]
            # allow for ignoring dataset with no files (though impossible with current map file syntax)
            if not paths:
                continue
            start_dir = self._deepest_common_parent(paths)
            print "INFO: for dataset ID %s," % dsid
            print "      top dir for create-cim is %s" % start_dir
            yield start_dir

    def _call_cdf2cim(self, starting_directory):
        # not sure what the interface will be...
        self.cdf2cim.blah(starting_directory)  # FIXME...

    def _deepest_common_parent(self, paths):
        common_substring = self._longest_common_substring([os.path.normpath(p) for p in paths])

        # substring will either end in either be /path/to/dir/ or /path/to/dir/common_file_stem
        # in either case dirname will return /path/to/dir
        return os.path.dirname(common_substring)

    def _longest_common_substring(self, strings):
        """
        longest substring at start of all the strings
        """
        s = ""
        for chars in zip(*strings):
            cset = set(chars)
            if len(cset) > 1:  # differences found
                break
            s += cset.pop()
        return s


create_cim_from_dmap = Cdf2cimWrapper().create_cim_from_dmap
