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

from tests import *
from utils import config

def gather_tests():
    "Returns a list of tests to run."
    tests_dir = os.path.join(config["test_base_dir"], "tests")
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

    for test_class in test_classes:
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == "__main__":

    run_suite()
