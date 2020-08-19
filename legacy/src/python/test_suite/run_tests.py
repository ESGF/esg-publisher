#!/usr/bin/env python

import sys

import tests.test_suite_runner as tsr

args = sys.argv[1:]

if len(args) == 0:
    tsr.run_suite()

elif len(args) == 1:
    tsr.run_suite(regexp = args[0])

else:
    print """
usage: run_tests.py [regexp]

  optional regexp, applied to method names, controls which tests to run"
  otherwise, runs all tests"""
    sys.exit(1)

    
