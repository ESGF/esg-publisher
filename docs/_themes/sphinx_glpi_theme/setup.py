# -*- coding: utf-8 -*-
"""`sphinx_glpi_theme` lives on `Github`_.

.. _github: https://www.github.com/glpi-project/sphinx_glpi_theme

"""
from setuptools import setup, find_packages
from sphinx_glpi_theme import __version__


setup(
    name='sphinx_glpi_theme',
    version=__version__,
    url='https://github.com/glpi-project/sphinx_glpi_theme/',
    license='MIT',
    author='Johan Cwiklinski',
    author_email='jcwiklinski@teclib.com',
    description='GLPI theme for Sphinx',
    long_description=open('README.rst').read(),
    zip_safe=False,
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Operating System :: OS Independent',
        'Topic :: Documentation',
        'Topic :: Software Development :: Documentation',
    ],
)
