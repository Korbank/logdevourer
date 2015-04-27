#!/usr/bin/python

from setuptools import setup, find_packages

setup(
    name = "logdevourer",
    version = "0.0.0",
    description = "Log parser and normalizer",
    packages     = [ "logdevd" ],
    package_dir  = { "": "pylib" },
    install_requires = [
        "liblognorm",
    ],
)
