#!/usr/bin/python

from setuptools import setup, find_packages

setup(
    name = "logdevourer",
    version = "0.1.0",
    description = "Log parser and normalizer",
    scripts      = [ "bin/logdevd" ],
    packages     = [ "logdevd" ],
    package_dir  = { "": "pylib" },
    install_requires = [
        "liblognorm",
        "yaml",
    ],
)
