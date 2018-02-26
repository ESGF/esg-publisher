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
    _verbose_errors = False

    def _do_import(self):
        if self.cdf2cim == None:
            self.cdf2cim = __import__("cdf2cim")    

    def set_verbose_errors(self):
        self._verbose_errors = True

    def create_cim_from_dmap(self, dmap, exception_on_fail=True):
        """
        Call cdf2cim with a starting directory which is the deepest common parent directory 
        for the set of files listed in the map file.
        The map file ought only contain one dataset ID, but if it contains more than one, 
        call cdf2cim for each separately.

        If exception_on_fail=False, then on failure it will not raise an exception, 
        but will print a warning and return False.  (Otherwise returns True.)
        """
        try:
            self._create_cim_from_dmap(dmap)
        except:
            if exception_on_fail:
                raise
            else:
                print "WARNING: --create-cim failed:\n"
                print tracebackString(indent=5)
                print "Continuing after --create-cim failure:\n"
                return False

        return True

    def _create_cim_from_dmap(self, dmap):
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
                failures += "While running cdf2cim on '%s':\n%s" % (top_dir, tracebackString(indent=5))

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

    def _list_files(self, files, title):
        if files:
            print "    " + title + ":"
            for f in files:
                print "        " + f

    def _call_cdf2cim(self, starting_directory):
        print "=========="
        print "CIM creation and publication"
        print "scanning %s" % starting_directory
        new, queued, published = self.cdf2cim.scan(starting_directory)
        self._list_files(new, "JSON files newly generated and queued for publication")
        self._list_files(queued, "relevant JSON files found already generated but still queued for publication")
        self._list_files(published, "relevant JSON files found already published")
        print "publishing queued JSON files (if any)"
        published, errors = self.cdf2cim.publish()
        if not published and not errors:
            print "    (none found)"
        self._list_files(published, "JSON files published")
        self._list_files([path for path, err in errors],
                         "JSON files that failed to publish")
        print "=========="
        if errors:
            if self._verbose_errors:
                print "========================"
                print "Web-service responses for failed JSON publication:"
                for path, err in errors:
                    print "\nPath: %s" % path
                    print "\nError: %s" % err.message
                print "========================"
            raise Exception("some JSON files could not be published")

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


_create_cim_wrapper = Cdf2cimWrapper()
create_cim_from_dmap = _create_cim_wrapper.create_cim_from_dmap
set_verbose_cim_errors = _create_cim_wrapper.set_verbose_errors


def setup_cdf2cim_environment(config, project_section):
    """
    Sets the environment values needed by cdf2cim from the ini file.
    The specified environment variables are set based on the same named var in the 
    ini file unless they are already set in the environment (so the environment can 
    override the ini file).
    
    Note that the ini file variable names are case-insensitive, for example
    "cdf2cim_client_ws_host" in the file is acceptable although the 
    corresponding environment variable is called CDF2CIM_CLIENT_WS_HOST.
    """

    # known environment variables; 2-tuples of (name, is_mandatory)
    variables = [('CDF2CIM_CLIENT_WS_HOST', True), 
                 ('CDF2CIM_CLIENT_GITHUB_USER', True), 
                 ('CDF2CIM_CLIENT_GITHUB_ACCESS_TOKEN', True)]

    for var_name, is_mandatory in variables:
        if os.getenv(var_name) == None:
            if config.has_option(project_section, var_name):
                os.environ[var_name] = config.get(project_section, var_name)
            elif is_mandatory:
                msg = "Mandatory variable '{0}' for cdf2cim needs to be supplied from environment or ini file section '{1}'".format(var_name, project_section)
                raise Exception(msg)
