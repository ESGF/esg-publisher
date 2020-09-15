#!/usr/bin/env python
    
from setuptools import setup, find_packages
from pathlib import Path
import os
import sys
import esgcet.esgmigrate as esgmigrate



VERSION = '5.0.0a'
print("esgcet version =", VERSION)
HOME = str(Path.home())
FULLPATH = HOME + '/.esg'
DEFAULT_ESGINI = '/esg/config/esgcet'
if not os.path.exists(FULLPATH):
    os.makedirs(FULLPATH)
if os.path.exists(FULLPATH + "/esg.ini"):
    config_exists = True
else:
    config_exists = False
#if os.path.exists(DEFAULT_ESGINI) and not config_exists:
#    esgmigrate.run({})

#os.system("bash install.sh")
if config_exists:
    setup(
        name = 'esgcet',
        version = VERSION,
        description = 'ESGCET publication package',
        author = 'Elysia Witham, Sasha Ames',
        author_email = 'witham3@llnl.gov',
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
        entry_points={'console_scripts': ['esgpidcitepub=esgcet.pid_cite_pub:main',
                                          'esgmkpubrec=esgcet.mk_dataset:main',
                                          'esgindexpub=esgcet.index_pub:main',
                                          'esgpublish=esgcet.pub_internal:main',
                                          'esgupdate=esgcet.update:main',
                                          'esgmapconv=esgcet.mapfile:main',
                                          'esgmigrate=esgcet.esgmigrate:main']}
    )
else:
    setup(
        name = 'esgcet',
        version = VERSION,
        description = 'ESGCET publication package',
        author = 'Elysia Witham, Sasha Ames',
        author_email = 'witham3@llnl.gov',
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
        entry_points={'console_scripts': ['esgpidcitepub=esgcet.pid_cite_pub:main',
                                          'esgmkpubrec=esgcet.mk_dataset:main',
                                          'esgindexpub=esgcet.index_pub:main',
                                          'esgpublish=esgcet.pub_internal:main',
                                          'esgupdate=esgcet.update:main',
                                          'esgmapconv=esgcet.mapfile:main'
                                          'esgmigrate=esgcet.esgmigrate:main']}
        )

    



