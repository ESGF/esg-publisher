#!/usr/bin/env python

"""
test_suite_runner.py
====================

Runs all tests for ESGF publisher suite.
"""

# Standard library imports
import unittest
import re
import os
import sys
import string

from tests import *
from utils import config

def gather_tests():
    "Returns a list of tests to run."
    tests_dir = os.path.join(config.get("test_base_dir"), "tests")
    test_mods = [test_mod.split(".")[0] for test_mod in os.listdir(tests_dir) if re.match("test_\d", test_mod)]
    test_classes = set()

    for test_mod in test_mods:
        test_number = test_mod.split("_")[1]
        mod = __import__(test_mod)
        test_class = [getattr(mod, x) for x in dir(mod) if x.find("Test%s" % test_number) == 0][0]
        test_classes.add(test_class)

    test_classes = sorted(list(test_classes))
    return test_classes

def run_suite():

    test_classes = gather_tests()
    print test_classes

    failures = ""
    for test_class in test_classes:
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        rv = unittest.TextTestRunner(verbosity=2).run(suite)
        if not rv.wasSuccessful():
            failures += string.join(["In %s:\n\n   %s\n\n" % 
                                     (e[0], e[1].replace("\n", "\n   "))
                                     for e in (rv.errors + rv.failures)])
    if failures:
        print """

===============================================
  Collated errors/failures from above tests
===============================================

"""
        print failures
        print "Some test(s) failed - see above"
        sys.exit(1)
    else:
        print "All tests successful"
        if config.devel_options_used:
            print "\nHowever, failing overall test because the following 'devel_' options were used:"
            for opt in config.devel_options_used:
                print "   %s" % opt
            print "\nFor test to succeed, unset devel_ options in the config and try again.\n"
            sys.exit(1)
        sys.exit(0)

if __name__ == "__main__":

    run_suite()
