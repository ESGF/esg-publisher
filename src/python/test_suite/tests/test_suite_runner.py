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

from all_tests import PublisherTests
from utils import config
from utils import set_esg_environment


def run_suite():
    
    set_esg_environment.set_esg_env()

    suite = unittest.TestLoader().loadTestsFromTestCase(PublisherTests)
    rv = unittest.TextTestRunner(verbosity=2).run(suite)

    if not rv.wasSuccessful():
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
