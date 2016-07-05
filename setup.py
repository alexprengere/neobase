#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import with_statement

from setuptools import setup, find_packages

with open('VERSION') as f:
    VERSION = f.read().rstrip()

with open('README.rst') as f:
    LONG_DESCRIPTION = f.read()

with open('LICENSE') as f:
    LICENSE = f.read()

setup(
    name='NeoBase',
    version=VERSION,
    author='Alex Prengère',
    author_email='alex.prengere@gmail.com',
    url='https://github.com/alexprengere/neobase',
    description='Lightweight GeoBases implementation: no dependency, single, Py3 compatible',
    long_description=LONG_DESCRIPTION,
    license=LICENSE,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'argparse',
    ],
    entry_points={
        'console_scripts' : [
            'NeoBase=neobase.neobase:main'
        ]
    },
)
