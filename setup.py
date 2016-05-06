# -*- coding: utf-8 -*-
"""Setup script for Dalite XBlock."""

# Imports ###########################################################


import os
from setuptools import setup


# Functions #########################################################

def package_data(pkg, root_list):
    """Generic function to find package_data for `pkg` under `root`."""
    data = []
    for root in root_list:
        for dirname, dirnames, files in os.walk(os.path.join(pkg, root)):  # pylint: disable=unused-variable
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}

# Main ##############################################################

setup(
    name='xblock-dalite',
    version='0.1',
    description='XBlock - Dalite',
    packages=['dalite_xblock'],
    install_requires=[
        'XBlock>=0.4.7',
        'lazy>=1.1',
        'lti_consumer-xblock>=1.0.5'
    ],
    dependency_links=[
        'https://github.com/edx/XBlock/tarball/xblock-0.4.10#egg=XBlock-0.4.10',
        'https://github.com/edx/xblock-lti-consumer/tarball/v1.0.6#egg=lti_consumer-xblock-1.0.6'
    ],
    entry_points={
        'xblock.v1': 'xblock-dalite = dalite_xblock.xblock:DaliteXBlock',
    },
    package_data=package_data("dalite_xblock", ["templates", "public"]),
)
