#!/usr/bin/env python
    
from setuptools import setup, find_packages
from pathlib import Path
import os
import sys
import configparser as cfg
from shutil import copyfile

import esgcet
VERSION = esgcet.__version__

additional_requirements = [
            "xarray",
            "netcdf4",
            "dask",
            "pyyaml",
            "globus-cli"
]


setup(
    name = 'esgcet',
    version = VERSION,
    description = 'ESGCET publication package',
    author = 'Sasha Ames',
    author_email = 'ames4@llnl.gov',
    url = 'http://esgf.github.io',
    install_requires = [
        "requests",
            "esgfpid",
        "ESGConfigParser==1.0.0a1",
    ] + additional_requirements,
    include_package_data = True,
    zip_safe = False,                   # Migration repository must be a directory
    entry_points={'console_scripts': ['esgpidcitepub=esgcet.esgpidcitepub:main',
                                        'esgmkpubrec=esgcet.esgmkpubrec:main',
                                        'esgindexpub=esgcet.esgindexpub:main',
                                        'esgpublish=esgcet.pub_internal:main',
                                        'esgupdate=esgcet.esgupdate:main',
                                        'esgmapconv=esgcet.esgmapconv:main',
                                        'esgmigrate=esgcet.migratecmd:main',
                                        'esgunpublish=esgcet.esgunpublish:main']}
)
