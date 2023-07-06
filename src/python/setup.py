#!/usr/bin/env python
    
from setuptools import setup, find_packages
from pathlib import Path
import os
import sys
import configparser as cfg
from shutil import copyfile


import esgcet
VERSION = esgcet.__version__

print("esgcet version =", VERSION)
HOME = str(Path.home())
FULLPATH = HOME + '/.esg'
DEFAULT_ESGINI = '/esg/config/esgcet'

if not os.path.exists(FULLPATH):
    os.makedirs(FULLPATH)

if os.path.exists(FULLPATH + "/esg.yaml"):
    make_config = False
else:
    make_config = True

if make_config:
    setup(
        name = 'esgcet',
        version = VERSION,
        description = 'ESGCET publication package',
        author = 'Sasha Ames',
        author_email = 'ames4@llnl.gov',
        url = 'http://esgf.llnl.gov',
        install_requires = [
            "requests",
             "esgfpid",
            "ESGConfigParser==1.0.0a1",
            "xarray",
            "netcdf4",
            "dask",
            "pyyaml"
        ],
        packages = find_packages(exclude=['ez_setup']),
        include_package_data = True,
        scripts = [
        ],
        zip_safe = False,                   # Migration repository must be a directory
        entry_points={'console_scripts': ['esgpidcitepub=esgcet.esgpidcitepub:main',
                                          'esgmkpubrec=esgcet.esgmkpubrec:main',
                                          'esgindexpub=esgcet.esgindexpub:main',
                                          'esgpublish=esgcet.pub_internal:main',
                                          'esgupdate=esgcet.esgupdate:main',
                                          'esgmapconv=esgcet.esgmapconv:main',
                                          'esgmigrate=esgcet.migratecmd:main',
                                          'esgunpublish=esgcet.esgunpublish:main']},
        data_files=[(FULLPATH, ['esg.yaml'])]

    )
else:
    setup(
        name = 'esgcet',
        version = VERSION,
        description = 'ESGCET publication package',
        author = 'Sasha Ames',
        author_email = 'ames4@llnl.gov',
        url = 'http://esgf.llnl.gov',
        install_requires = [
            "requests",
             "esgfpid",
            "ESGConfigParser==1.0.0a1"
        ],
        packages = find_packages(exclude=['ez_setup']),
        include_package_data = True,
        scripts = [
        ],
        zip_safe = False,                   # Migration repository must be a directory
        entry_points={'console_scripts': ['esgpidcitepub=esgcet.esgpidcitepub:main',
                                          'esgmkpubrec=esgcet.esgmkpubrec:main',
                                          'esgindexpub=esgcet.esgindexpub:main',
                                          'esgpublish=esgcet.pub_internal:main',
                                          'esgupdate=esgcet.esgupdate:main',
                                          'esgmapconv=esgcet.esgmapconv:main'
                                          'esgmigrate=esgcet.migratecmd:main',
                                          'esgunpublish=esgcet.esgunpublish:main']}
        )
