#!/usr/bin/env python
    
# try:
#     from setuptools import setup, find_packages
# except ImportError:
#     from ez_setup import use_setuptools
#     use_setuptools()
#     from setuptools import setup, find_packages
from setuptools import setup, find_packages
from pathlib import Path
import os



VERSION = '5.0.0a'
print("esgcet version =", VERSION)
HOME = str(Path.home())
FULLPATH = HOME + '/.esg'
if not os.path.exists(FULLPATH):
    os.makedirs(FULLPATH)

#os.system("bash install.sh")

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
    ],
#    setup_requires = [
#        "requests",
#    ],
    packages = find_packages(exclude=['ez_setup']),
    include_package_data = True,
    # test_suite = 'nose.collector',
    # Install the CF standard name table, ESG init file, etc.
    scripts = [
    ],
    zip_safe = False,                   # Migration repository must be a directory
    entry_points={'console_scripts': ['esgpidcitepub=esgcet.pid_cite_pub:main',
                                      'esgmkpubrec=esgcet.mk_dataset:main',
                                      'esgindexpub=esgcet.index_pub:main',
                                      'esgpublish=esgcet.pub_internal:main',
                                      'esgupdate=esgcet.update:main',
                                      'esgmapconv=esgcet.mapfile:main'
                                      'esgmigrate=esgcet.esgmigrate:main']},
    data_files=[(FULLPATH, ['esg.ini'])] 
)



