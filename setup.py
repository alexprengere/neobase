#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import with_statement

from setuptools import setup, find_packages

with open('VERSION') as f:
    VERSION = f.read().rstrip()

with open('README.md') as fl:
    LONG_DESCRIPTION = fl.read()

with open('requirements.txt') as f:
    REQUIREMENTS = [p.strip() for p in f.readlines()]

setup(
    name='NeoBase',
    version=VERSION,
    author='Alex Prengère',
    author_email='alex.prengere@gmail.com',
    url='http://rndwww.nce.amadeus.net/git/projects/SADAM/repos/neobase',
    description='Optd Python API.',
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    include_package_data=True,
    install_requires=REQUIREMENTS,
    entry_points={
        'console_scripts' : [
            'NeoBase=neobase.neobase:main'
        ]
    },
)
