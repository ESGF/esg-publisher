#!/usr/bin/env python
    
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages




VERSION = '5.0.0a'
print("esgcet version =", VERSION)

setup(
    name = 'esgcet',
    version = VERSION,
    description = 'ESGCET publication package',
    author = 'Elysia Witham, Sasha Ames',
    author_email = 'witham3@llnl.gov',
    url = 'http://esgf.llnl.gov',
    install_requires = [
        "requests>=2.22.0",
         "esgfpid>=0.8",
    ],
    setup_requires = [
        "requests>=2.22.0",
    ],
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
                                      'esgpublish=esgcet.pub-internal:main',
                                      'esgupdate=esgcet.update:main',
                                      'esgmapconv=esgcet.mapfile:main']}
)



