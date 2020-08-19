#!/usr/bin/env python
import os
from migrate.versioning.shell import main

main(repository=os.path.abspath(os.path.dirname(__file__)))
