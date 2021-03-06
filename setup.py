#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pysimplecasper - A simple library for basic usage of Casper API that also does some
                 processing of the data and produces some common 'reports'

Copyright 2017, <copyright@mzpqnxow.com>
See COPYRIGHT for details
"""

from setuptools import setup
from codecs import open
from os import path

NAME = 'pysimplecasper'

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

#
# If you want to namespace for an internal PyPi repository
# Example
# NAMESPACE = ['companyname', 'teamname']
# This will name this companyname.teamname.pysimplecasper in your PyPi
#
NAMESPACE = []
NAMESPACE.append(NAME)
FULL_NAME = '.'.join(NAMESPACE)

setup(
    name=FULL_NAME,
    version='0.3',
    description='Simple wrapper for Casper API that generates reports',
    long_description=long_description,
    url='https://github.com/mzpqnxow/pysimplecasper.git',
    # Author details
    zip_safe=True,
    author='Adam Greene',
    # Choose your license
    license='3-clause BSD License',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: 3-clause BSD License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7'
    ],
    keywords='casper',
    packages=['simplecasper'],
    install_requires=['requests']
)
