#!/usr/bin/env python

from setuptools import setup

__author__ = "Michael Ganzberger"

setup(
    name="geomip",
    version='1.0',
    description="GeoMip data",
    author=__author__,
    packages=["geomip"],
    entry_points="""
    [esgcet.project_handlers]
    handler_name = geomip_handler
    handler = geomip.project_handler:CustomProjectHandler
    """,
)
