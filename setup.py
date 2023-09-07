#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Setup file, will build the pip package for the project.
"""

from time import time
from setuptools import setup

PRE = "{Personal-Access-Token-Name}:{Personal-Access-Token}"

def new_version():
    """
    This Method will create a New version and update the Version file.
    """
    time_now = int(time())
    version = f'2.0.{time_now}'

    return version


setup(
    name = "trinityx-obol",
    version = new_version(),
    description = "Command line utility to manage LDAP users and groups.",
    long_description = "Command line utility to manage LDAP users and groups.",
    author = 'ClusterVision Development Team',
    author_email = "support@clustervision.com",
    maintainer = 'ClusterVision Development Team',
    maintainer_email = "support@clustervision.com",
    url = "https://gitlab.taurusgroup.one/clustervision/trinityx-obol.git",
    download_url = f"https://{PRE}@gitlab.taurusgroup.one/api/v4/projects/14/packages/pypi/simple",
    packages = [
        "obol"
    ],
    license = "MIT",
    install_requires = [
        "python-ldap>=3.3"
    ],
    data_files = [
        ("/etc/obol", ["obol.conf"])
    ],
    entry_points={
        'console_scripts': [
            'obol = obol.obol:run',
        ]
    },

)
# python setup.py sdist bdist_wheel
